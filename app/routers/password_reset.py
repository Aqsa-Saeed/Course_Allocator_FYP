"""
Forgot-password flow with an emailed 6-digit code.

  POST /auth/forgot-password   {username}                       -> always the same reply
  POST /auth/reset-password    {username, code, new_password}   -> sets the new password

The user only types their username; the code is emailed to the address registered on the account.

Safeguards
  * The reply to /forgot-password is identical whether or not the username belongs to an account
    (and it never shows the registered email address).
  * Codes expire after 10 minutes, work once, and a new request cancels older codes.
  * 5 wrong guesses kill the code. Failures always return the same message.
  * At most 1 code per minute and 5 per hour per account; 20 requests per 10 minutes per IP.
  * Codes are stored as an HMAC (keyed with SECRET_KEY), not in plain text.
  * Email is sent in a background task so response time doesn't reveal whether the account exists.
"""

import hashlib
import hmac
import secrets
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import SECRET_KEY
from app.core.mailer import send_email
from app.core.security import hash_password
from app.database import get_db
from app.models import User
from app.models.password_reset import PasswordResetCode
from app.schemas.password_reset import ForgotPasswordRequest, MessageOut, ResetPasswordRequest

router = APIRouter(prefix="/auth", tags=["auth"])

CODE_TTL_MINUTES = 10
MAX_ATTEMPTS = 5
RESEND_SECONDS = 60
MAX_CODES_PER_HOUR = 5
IP_LIMIT, IP_WINDOW_SECONDS = 20, 600

GENERIC_REPLY = (
    "If an account exists for that username, a 6-digit code has been sent to its registered email address. "
    "It expires in 10 minutes."
)

_ip_hits: dict[str, deque] = defaultdict(deque)  # per-process; fine for a single server


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _check_ip(request: Request) -> None:
    ip = request.client.host if request.client else "unknown"
    now, hits = time.monotonic(), _ip_hits[ip]
    while hits and now - hits[0] > IP_WINDOW_SECONDS:
        hits.popleft()
    if len(hits) >= IP_LIMIT:
        raise HTTPException(status_code=429, detail="Too many requests. Please wait a few minutes and try again.")
    hits.append(now)


def _hash_code(user_id: int, code: str) -> str:
    return hmac.new(SECRET_KEY.encode(), f"pwreset:{user_id}:{code}".encode(), hashlib.sha256).hexdigest()


def _find_user(db: Session, identifier: str) -> User | None:
    """Username (exact, as login does). An email address is also accepted as a convenience."""
    identifier = identifier.strip()
    user = db.query(User).filter(User.username == identifier).first()
    if user is None:
        user = db.query(User).filter(func.lower(User.email) == identifier.lower()).first()
    return user


def _email_body(code: str) -> tuple[str, str, str]:
    subject = "Your Course Allocation password reset code"
    text = (
        f"Your password reset code is: {code}\n\n"
        f"It expires in {CODE_TTL_MINUTES} minutes and can be used once.\n"
        "If you didn't ask to reset your password, you can ignore this email; your password has not changed."
    )
    html = (
        '<div style="font-family:Segoe UI,Arial,sans-serif;font-size:15px;color:#1a1a1a">'
        "<p>Your Course Allocation password reset code is:</p>"
        f'<p style="font-size:30px;letter-spacing:6px;font-weight:700;margin:12px 0">{code}</p>'
        f"<p>It expires in {CODE_TTL_MINUTES} minutes and can be used once.</p>"
        '<p style="color:#6b6862">If you didn\'t ask to reset your password, you can ignore this email. '
        "Your password has not changed.</p></div>"
    )
    return subject, text, html


@router.post("/forgot-password", response_model=MessageOut)
def forgot_password(
    body: ForgotPasswordRequest,
    request: Request,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
):
    _check_ip(request)
    user = _find_user(db, body.username)

    if user and user.is_active:
        now = _now()
        # Housekeeping: drop codes older than a day.
        db.query(PasswordResetCode).filter(PasswordResetCode.created_at < now - timedelta(days=1)).delete(
            synchronize_session=False
        )
        recent = (
            db.query(PasswordResetCode)
            .filter(PasswordResetCode.user_id == user.id, PasswordResetCode.created_at > now - timedelta(hours=1))
            .order_by(PasswordResetCode.created_at.desc())
            .all()
        )
        throttled = len(recent) >= MAX_CODES_PER_HOUR or (
            recent and (now - recent[0].created_at).total_seconds() < RESEND_SECONDS
        )
        if not throttled:
            code = f"{secrets.randbelow(10**6):06d}"
            # A new code cancels any earlier unused ones.
            db.query(PasswordResetCode).filter(
                PasswordResetCode.user_id == user.id, PasswordResetCode.used_at.is_(None)
            ).update({"used_at": now}, synchronize_session=False)
            db.add(
                PasswordResetCode(
                    user_id=user.id,
                    code_hash=_hash_code(user.id, code),
                    expires_at=now + timedelta(minutes=CODE_TTL_MINUTES),
                )
            )
            db.commit()
            subject, text, html = _email_body(code)
            background.add_task(send_email, user.email, subject, text, html)
        else:
            db.commit()

    return MessageOut(message=GENERIC_REPLY)


@router.post("/reset-password", response_model=MessageOut)
def reset_password(body: ResetPasswordRequest, request: Request, db: Session = Depends(get_db)):
    _check_ip(request)
    invalid = HTTPException(
        status_code=400,
        detail="That code is incorrect or has expired. Request a new code and try again.",
    )

    user = _find_user(db, body.username)
    if user is None or not user.is_active:
        raise invalid

    now = _now()
    record = (
        db.query(PasswordResetCode)
        .filter(
            PasswordResetCode.user_id == user.id,
            PasswordResetCode.used_at.is_(None),
            PasswordResetCode.expires_at > now,
        )
        .order_by(PasswordResetCode.created_at.desc())
        .first()
    )
    if record is None or record.attempts >= MAX_ATTEMPTS:
        raise invalid

    if not hmac.compare_digest(record.code_hash, _hash_code(user.id, body.code.strip())):
        record.attempts += 1
        db.commit()
        raise invalid

    user.hashed_password = hash_password(body.new_password)
    db.query(PasswordResetCode).filter(
        PasswordResetCode.user_id == user.id, PasswordResetCode.used_at.is_(None)
    ).update({"used_at": now}, synchronize_session=False)
    db.commit()
    return MessageOut(message="Your password has been changed. You can now sign in.")
