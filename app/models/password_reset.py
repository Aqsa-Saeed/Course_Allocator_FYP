from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from .base import Base


def _utcnow() -> datetime:
    # The app stores naive UTC datetimes (see formatTime in ui.jsx), so do the same here.
    return datetime.now(timezone.utc).replace(tzinfo=None)


class PasswordResetCode(Base):
    """One emailed 6-digit code. Stored as a keyed hash, never in plain text."""
    __tablename__ = "password_reset_codes"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    code_hash = Column(String(64), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    attempts = Column(Integer, nullable=False, default=0)   # wrong guesses so far
    used_at = Column(DateTime, nullable=True)               # set when used or replaced by a newer code
    created_at = Column(DateTime, nullable=False, default=_utcnow)
