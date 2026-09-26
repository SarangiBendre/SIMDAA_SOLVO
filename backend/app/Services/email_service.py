"""
Email notification service.

Two ways to send, in order of preference:

1. Brevo HTTP API (recommended - set BREVO_API_KEY). Sends over HTTPS
   (port 443), which cloud platforms never block. This matters because
   Render's free tier (and several others) blocks outbound SMTP ports
   (25/465/587) entirely to prevent spam abuse - raw SMTP that works
   fine on your own machine will silently time out once deployed there.
   Get this key from Brevo > Settings > SMTP & API > API Keys tab (this
   is a DIFFERENT credential from the SMTP password - the SMTP key
   won't work here).

2. Plain SMTP (SMTP_SERVER/SMTP_EMAIL/SMTP_PASSWORD) - works for local
   development or any host that doesn't block SMTP ports, and as a
   fallback for non-Brevo providers.

Sending is always best-effort: if nothing is configured, or the send
fails (no network, wrong credentials, blocked port, etc.), we log a
warning and move on rather than breaking the request that triggered
the notification.
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("simdaa.email")

EMAIL_ENABLED = os.getenv("EMAIL_NOTIFICATIONS_ENABLED", "true").lower() == "true"

BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")

SMTP_SERVER = os.getenv("SMTP_SERVER", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

EMAIL_FROM = os.getenv("EMAIL_FROM", SMTP_EMAIL)
EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "SIMDAA SOLVO")


def is_configured() -> bool:
    if not EMAIL_ENABLED:
        return False
    return bool(BREVO_API_KEY) or bool(SMTP_SERVER and SMTP_EMAIL and SMTP_PASSWORD)


def _send_via_brevo_api(to_email: str, subject: str, body: str) -> bool:
    import requests

    try:
        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "api-key": BREVO_API_KEY,
                "Content-Type": "application/json",
                "accept": "application/json",
            },
            json={
                "sender": {"name": EMAIL_FROM_NAME, "email": EMAIL_FROM},
                "to": [{"email": to_email}],
                "subject": subject,
                "textContent": body,
            },
            timeout=10,
        )
        response.raise_for_status()
        return True
    except Exception as exc:
        logger.warning("Brevo API send to %s failed: %s", to_email, exc)
        return False


def _send_via_smtp(to_email: str, subject: str, body: str) -> bool:
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_FROM
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(EMAIL_FROM, to_email, msg.as_string())

        return True
    except Exception as exc:
        logger.warning("SMTP send to %s failed: %s", to_email, exc)
        return False


def send_email(to_email: str, subject: str, body: str) -> bool:
    """Send a plaintext email. Returns True on success, False otherwise.
    Never raises - callers should not need to wrap this in try/except."""

    if not is_configured():
        logger.info("Email notifications disabled or not configured; skipping send to %s", to_email)
        return False

    if BREVO_API_KEY:
        return _send_via_brevo_api(to_email, subject, body)

    return _send_via_smtp(to_email, subject, body)
