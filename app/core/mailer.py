"""
Sends email over SMTP. Settings come from .env:

    SMTP_HOST      e.g. smtp.gmail.com   (leave EMPTY in development: the email is printed to the console instead)
    SMTP_PORT      587 (STARTTLS, default) or 465 (SSL)
    SMTP_USER      login for the SMTP server
    SMTP_PASSWORD  password / app password
    SMTP_FROM      "Course Allocation <you@example.com>"  (defaults to SMTP_USER)
    SMTP_STARTTLS  true (default). Set to false ONLY for a local test server such as MailHog.

Failures are logged, never raised: callers run this in a background task and must not
reveal to the user whether an address exists or whether delivery worked.
"""

import logging
import os
import smtplib
import ssl
from email.message import EmailMessage

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("mailer")


def send_email(to: str, subject: str, text: str, html: str | None = None) -> None:
    host = os.getenv("SMTP_HOST", "").strip()
    if not host:
        # Development mode: no mail server configured, so show the message here.
        print(
            "\n" + "=" * 64
            + f"\n[DEV EMAIL - SMTP_HOST is not set, nothing was sent]\nTo: {to}\nSubject: {subject}\n\n{text}\n"
            + "=" * 64 + "\n",
            flush=True,
        )
        return

    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "").strip()
    password = os.getenv("SMTP_PASSWORD", "")
    sender = os.getenv("SMTP_FROM", "").strip() or user

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = to
    message.set_content(text)
    if html:
        message.add_alternative(html, subtype="html")

    try:
        context = ssl.create_default_context()
        if port == 465:
            with smtplib.SMTP_SSL(host, port, context=context, timeout=20) as server:
                if user:
                    server.login(user, password)
                server.send_message(message)
        else:
            with smtplib.SMTP(host, port, timeout=20) as server:
                server.ehlo()
                if os.getenv("SMTP_STARTTLS", "true").strip().lower() != "false":
                    server.starttls(context=context)
                    server.ehlo()
                if user:
                    server.login(user, password)
                server.send_message(message)
    except Exception:
        logger.exception("Could not send email to %s", to)
