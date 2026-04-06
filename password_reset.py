"""
password_reset.py
-----------------
Handles password reset token generation, email sending, and verification.
Uses Gmail SMTP (same credentials as email_report.py).
"""

import os
from dotenv import load_dotenv
load_dotenv()
import uuid
import smtplib
import hashlib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from database import get_connection


# ------------------------------------------------------------------ #
# DATABASE SETUP
# ------------------------------------------------------------------ #

def create_reset_tables():
    """
    Create required DB columns/tables if they don't exist.
    MySQL/MariaDB compatible. Call this once at startup.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:

            # Add email column to users if it doesn't exist (MySQL compatible)
            cur.execute("""
                SELECT COUNT(*) FROM information_schema.columns
                WHERE table_schema = DATABASE()
                AND table_name = 'users'
                AND column_name = 'email'
            """)
            email_exists = cur.fetchone()[0]
            if not email_exists:
                cur.execute("ALTER TABLE users ADD COLUMN email VARCHAR(255)")

            # Create password_reset_tokens table (MySQL compatible)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS password_reset_tokens (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(255) NOT NULL,
                    token VARCHAR(255) NOT NULL UNIQUE,
                    expires_at DATETIME NOT NULL,
                    used TINYINT(1) DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()


# ------------------------------------------------------------------ #
# TOKEN HELPERS
# ------------------------------------------------------------------ #

def _generate_token() -> str:
    """Generate a secure unique token."""
    return hashlib.sha256(uuid.uuid4().bytes).hexdigest()


def create_reset_token(username: str) -> str | None:
    """
    Create a password reset token for username.
    Returns the token string, or None if username not found.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Check user exists
            cur.execute("SELECT username FROM users WHERE username = %s", (username,))
            if not cur.fetchone():
                return None

            # Invalidate any existing tokens for this user
            cur.execute(
                "UPDATE password_reset_tokens SET used = TRUE WHERE username = %s AND used = FALSE",
                (username,)
            )

            token = _generate_token()
            expires_at = datetime.now() + timedelta(hours=1)

            cur.execute(
                """
                INSERT INTO password_reset_tokens (username, token, expires_at)
                VALUES (%s, %s, %s)
                """,
                (username, token, expires_at)
            )
            conn.commit()
            return token


def verify_reset_token(token: str) -> tuple[bool, str]:
    """
    Verify a reset token.
    Returns (valid: bool, username: str or error message).
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT username, expires_at, used
                FROM password_reset_tokens
                WHERE token = %s
                """,
                (token,)
            )
            row = cur.fetchone()

            if not row:
                return False, "Invalid or expired reset link."

            username, expires_at, used = row

            if used:
                return False, "This reset link has already been used."

            if datetime.now() > expires_at:
                return False, "This reset link has expired. Please request a new one."

            return True, username


def mark_token_used(token: str):
    """Mark a token as used after successful password reset."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE password_reset_tokens SET used = TRUE WHERE token = %s",
                (token,)
            )
            conn.commit()


# ------------------------------------------------------------------ #
# EMAIL HELPERS
# ------------------------------------------------------------------ #

def get_user_email(username: str) -> str | None:
    """Fetch the stored email for a username."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT email FROM users WHERE username = %s", (username,))
            row = cur.fetchone()
            return row[0] if row and row[0] else None


def save_user_email(username: str, email: str):
    """Save or update email for a user."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET email = %s WHERE username = %s",
                (email, username)
            )
            conn.commit()


def send_reset_email(recipient_email: str, username: str, token: str) -> tuple[bool, str]:
    """
    Send password reset email with token link.
    Returns (success: bool, message: str).
    """
    sender_email = (os.environ.get("SENDER_EMAIL") or os.environ.get("EMAIL_USER", ""))
    app_password = (os.environ.get("SENDER_APP_PASSWORD") or os.environ.get("EMAIL_PASSWORD", ""))
    email_host   = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
    email_port   = int(os.environ.get("EMAIL_PORT", 587))

    if not sender_email or not app_password:
        return False, "Email credentials not configured. Set EMAIL_USER and EMAIL_PASSWORD in your .env file."

    # Build a reset link — since this is a local Streamlit app we pass the token
    # as a URL param. Users copy it into the "Reset Password" tab.
    reset_code = token[:8].upper()   # Short code for manual entry

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"Salary Prediction App <{sender_email}>"
        msg["To"] = recipient_email
        msg["Subject"] = "Password Reset Request — Salary Prediction App"

        body_text = f"""
Hi {username},

We received a request to reset your password for the Salary Prediction App.

Your reset code is:

    {reset_code}

Enter this code in the "Reset Password" tab on the login page.

This code expires in 1 hour.

If you did not request a password reset, you can safely ignore this email.

Best regards,
The Salary Prediction App Team
"""

        body_html = f"""
<html>
<body style="font-family:Arial,sans-serif; background:#f3f4f6; padding:40px;">
  <div style="max-width:480px; margin:auto; background:#ffffff;
      border-radius:16px; overflow:hidden;
      box-shadow:0 8px 24px rgba(0,0,0,0.1);">
    <div style="background:linear-gradient(135deg,#667eea,#764ba2);
        padding:28px 32px; text-align:center;">
      <h2 style="color:#ffffff; margin:0; font-size:1.5rem;">Password Reset</h2>
      <p style="color:rgba(255,255,255,0.8); margin:6px 0 0;">Salary Prediction App</p>
    </div>
    <div style="padding:32px;">
      <p style="color:#374151; font-size:0.95rem;">Hi <b>{username}</b>,</p>
      <p style="color:#374151; font-size:0.95rem;">
        We received a request to reset your password. Use the code below:
      </p>
      <div style="background:#f0f4ff; border:2px dashed #667eea;
          border-radius:12px; padding:20px; text-align:center; margin:20px 0;">
        <div style="font-size:0.75rem; color:#6b7280; margin-bottom:6px;
            text-transform:uppercase; letter-spacing:0.1em;">Your Reset Code</div>
        <div style="font-size:2.2rem; font-weight:800; color:#4c51bf;
            letter-spacing:0.2em;">{reset_code}</div>
      </div>
      <p style="color:#6b7280; font-size:0.85rem;">
        Enter this code in the <b>Reset Password</b> tab on the login page.
        This code expires in <b>1 hour</b>.
      </p>
      <p style="color:#9ca3af; font-size:0.8rem; margin-top:24px;">
        If you didn't request this, you can safely ignore this email.
      </p>
    </div>
    <div style="background:#f9fafb; padding:16px 32px; text-align:center;">
      <p style="color:#9ca3af; font-size:0.75rem; margin:0;">
        © Salary Prediction App — This is an automated message.
      </p>
    </div>
  </div>
</body>
</html>
"""
        msg.attach(MIMEText(body_text, "plain"))
        msg.attach(MIMEText(body_html, "html"))

        # Support Port 465 (SSL) or 587 (STARTTLS)
        if email_port == 465:
            server = smtplib.SMTP_SSL(email_host, email_port, timeout=15)
        else:
            server = smtplib.SMTP(email_host, email_port, timeout=15)
            server.starttls()

        with server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())

        return True, f"Reset code sent to {recipient_email}. Check your inbox."

    except (smtplib.SMTPConnectError, TimeoutError, ConnectionError) as e:
        return False, (
            f"Network Error: Connection timed out or refused. "
            f"Your current Wi-Fi or Firewall may be blocking {email_host} on port {email_port}. "
            "Try changing your Wi-Fi or updating your .env to use EMAIL_PORT=465."
        )
    except smtplib.SMTPAuthenticationError:
        return False, "Gmail authentication failed. Check your EMAIL_USER and EMAIL_PASSWORD (use an App Password)."
    except smtplib.SMTPException as e:
        return False, f"Email Error: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"
