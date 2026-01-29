import os
import smtplib
import ssl
from email.message import EmailMessage


def send_verification_email(to_email: str, code: str) -> None:
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASS")
    from_email = os.environ.get("SMTP_FROM", smtp_user)

    if not smtp_host or not smtp_user or not smtp_pass or not from_email:
        raise RuntimeError(
            "SMTP is not configured. Set SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM."
        )

    msg = EmailMessage()
    msg["Subject"] = "University Housing Verification Code"
    msg["From"] = from_email
    msg["To"] = to_email
    msg.set_content(
        f"Your verification code is: {code}\n\n"
        "If you did not request this, ignore this email."
    )

    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls(context=context)
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
