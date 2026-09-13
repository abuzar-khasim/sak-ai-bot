import resend

from app.config.settings import settings


async def send_lead_email(
    name: str,
    email: str,
    service: str,
    requirement: str,
):
    resend.api_key = settings.resend_api_key

    params = {
        "from": "SAK AI <onboarding@resend.dev>",
        "to": [settings.admin_email],
        "subject": f"🚀 New SAK AI Lead — {service}",
        "html": f"""
        <h2>New SAK AI Lead</h2>

        <p><strong>Name:</strong> {name}</p>
        <p><strong>Email:</strong> {email}</p>
        <p><strong>Service:</strong> {service}</p>

        <h3>Requirement</h3>
        <p>{requirement}</p>

        <hr>

        <p>
            <strong>SAK AI</strong><br>
            AI • Automations • Agents
        </p>
        """,
    }

    result = await resend.Emails.send_async(params)

    print(f"✅ Email sent successfully: {result}")

    return result