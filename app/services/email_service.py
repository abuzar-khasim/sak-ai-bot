import asyncio
import smtplib
from email.message import EmailMessage

from app.config.settings import settings


def _send_email_sync(
    name: str,
    email: str,
    service: str,
    requirement: str,
):
    message = EmailMessage()

    message["Subject"] = f"🚀 New SAK AI Lead — {service}"
    message["From"] = settings.smtp_email
    message["To"] = settings.admin_email
    message["Reply-To"] = email

    message.set_content(
        f"""New Contact Us submission from SAK AI

Name: {name}
Email: {email}
Service: {service}

Requirement:
{requirement}

---
SAK AI
AI • Automations • Agents
"""
    )

    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.starttls()
        smtp.login(
            settings.smtp_email,
            settings.smtp_app_password,
        )
        smtp.send_message(message)


async def send_lead_email(
    name: str,
    email: str,
    service: str,
    requirement: str,
):
    await asyncio.to_thread(
        _send_email_sync,
        name,
        email,
        service,
        requirement,
    )