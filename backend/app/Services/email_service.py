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


def _send_via_brevo_api(to_email: str, subject: str, body: str, html_body: str | None = None) -> bool:
    import requests

    try:
        payload = {
            "sender": {"name": EMAIL_FROM_NAME, "email": EMAIL_FROM},
            "to": [{"email": to_email}],
            "subject": subject,
            "textContent": body,
        }
        if html_body:
            payload["htmlContent"] = html_body

        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "api-key": BREVO_API_KEY,
                "Content-Type": "application/json",
                "accept": "application/json",
            },
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        return True
    except Exception as exc:
        logger.warning("Brevo API send to %s failed: %s", to_email, exc)
        return False


def _send_via_smtp(to_email: str, subject: str, body: str, html_body: str | None = None) -> bool:
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = EMAIL_FROM
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        if html_body:
            msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(EMAIL_FROM, to_email, msg.as_string())

        return True
    except Exception as exc:
        logger.warning("SMTP send to %s failed: %s", to_email, exc)
        return False


def send_email(to_email: str, subject: str, body: str, html_body: str | None = None) -> bool:
    """Send an email with plaintext and optional HTML fallback. Returns True on success, False otherwise.
    Never raises - callers should not need to wrap this in try/except."""

    if not is_configured():
        logger.info("Email notifications disabled or not configured; skipping send to %s", to_email)
        return False

    if BREVO_API_KEY:
        return _send_via_brevo_api(to_email, subject, body, html_body)

    return _send_via_smtp(to_email, subject, body, html_body)


def send_account_creation_email(
    to_email: str,
    full_name: str,
    username: str,
    password: str,
    role_name: str,
    department: str = "",
) -> bool:
    """Send welcome email with account credentials when an admin creates a new user."""

    app_url = os.getenv("APP_URL", os.getenv("FRONTEND_URL", "https://simdaa-solvo-1.onrender.com")).rstrip("/")
    login_url = f"{app_url}/login"

    subject = "Welcome to SIMDAA SOLVO - Your Account Details"

    dept_line_text = f"- Department: {department}\n" if department else ""
    dept_line_html = (
        f'<tr><td style="padding: 6px 0; color: #64748b; font-weight: 500;">Department:</td><td style="padding: 6px 0; font-weight: 600; color: #1e293b;">{department}</td></tr>'
        if department
        else ""
    )

    body_text = (
        f"Hello {full_name},\n\n"
        "Welcome to SIMDAA SOLVO! Your account has been created by the administrator.\n\n"
        "Here are your login credentials:\n\n"
        f"- Login URL: {login_url}\n"
        f"- Username: {username}\n"
        f"- Temporary Password: {password}\n"
        f"- Role: {role_name}\n"
        f"{dept_line_text}\n"
        "Getting Started:\n"
        f"1. Go to {login_url}\n"
        "2. Sign in with your username and password provided above.\n"
        "3. For security, please change your password after logging in by going to your Profile settings.\n\n"
        "If you have any questions, please contact your administrator.\n\n"
        "Best regards,\n"
        "SIMDAA SOLVO Team"
    )

    body_html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Welcome to SIMDAA SOLVO</title>
</head>
<body style="margin: 0; padding: 24px 0; background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e293b; line-height: 1.5;">
  <table width="100%" cellpadding="0" cellspacing="0" border="0">
    <tr>
      <td align="center">
        <table width="560" cellpadding="0" cellspacing="0" border="0" style="max-width: 560px; width: 100%; background: #ffffff; border-radius: 8px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
          <!-- Header -->
          <tr>
            <td style="background-color: #1e40af; padding: 24px 32px; text-align: left;">
              <h1 style="margin: 0; color: #ffffff; font-size: 22px; font-weight: 700; letter-spacing: -0.5px;">SIMDAA SOLVO</h1>
              <p style="margin: 4px 0 0; color: #93c5fd; font-size: 13px;">Ask. Solve. Share.</p>
            </td>
          </tr>
          <!-- Content -->
          <tr>
            <td style="padding: 32px;">
              <h2 style="margin: 0 0 12px; font-size: 18px; color: #0f172a;">Welcome, {full_name}!</h2>
              <p style="margin: 0 0 20px; font-size: 14px; color: #475569; line-height: 1.6;">
                An account has been created for you on <strong>SIMDAA SOLVO</strong>, your team's knowledge sharing and Q&amp;A platform. You can now log in using the credentials below:
              </p>

              <!-- Credentials Box -->
              <div style="background-color: #f1f5f9; border-radius: 6px; padding: 18px 20px; margin-bottom: 24px; border: 1px solid #e2e8f0;">
                <table width="100%" cellpadding="0" cellspacing="0" border="0" style="font-size: 14px;">
                  <tr>
                    <td width="140" style="padding: 6px 0; color: #64748b; font-weight: 500;">Username:</td>
                    <td style="padding: 6px 0; font-family: Consolas, Monaco, monospace; font-size: 14px; font-weight: 600; color: #0f172a;">{username}</td>
                  </tr>
                  <tr>
                    <td style="padding: 6px 0; color: #64748b; font-weight: 500;">Temporary Password:</td>
                    <td style="padding: 6px 0; font-family: Consolas, Monaco, monospace; font-size: 14px; font-weight: 600; color: #2563eb;">{password}</td>
                  </tr>
                  <tr>
                    <td style="padding: 6px 0; color: #64748b; font-weight: 500;">Role:</td>
                    <td style="padding: 6px 0; font-weight: 600; color: #1e293b;">{role_name}</td>
                  </tr>
                  {dept_line_html}
                </table>
              </div>

              <!-- CTA Button -->
              <div style="text-align: center; margin-bottom: 24px;">
                <a href="{login_url}" style="display: inline-block; background-color: #2563eb; color: #ffffff; text-decoration: none; padding: 12px 28px; border-radius: 6px; font-weight: 600; font-size: 14px;">Log In to SIMDAA SOLVO</a>
              </div>

              <!-- Security Warning -->
              <div style="background-color: #fffbeb; border-left: 4px solid #f59e0b; border-radius: 4px; padding: 12px 16px; margin-bottom: 20px;">
                <p style="margin: 0; font-size: 13px; color: #92400e; line-height: 1.5;">
                  <strong>Security Tip:</strong> For your security, we strongly recommend changing your password right after logging in. You can do this at any time from your <strong>Profile &gt; Change password</strong> section.
                </p>
              </div>

              <p style="margin: 0; font-size: 13px; color: #64748b; line-height: 1.5;">
                If you did not expect this invitation or have trouble signing in, please reach out to your system administrator.
              </p>
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="background-color: #f8fafc; border-top: 1px solid #e2e8f0; padding: 16px 32px; text-align: center;">
              <p style="margin: 0; font-size: 12px; color: #94a3b8;">
                SIMDAA SOLVO &middot; Knowledge Sharing &amp; Collaboration Platform
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    return send_email(to_email, subject, body_text, body_html)
