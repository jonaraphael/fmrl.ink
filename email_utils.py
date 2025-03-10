import logging
from secrets import get_secret

import requests
from cryptography.fernet import Fernet
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

# Retrieve sensitive configuration from Secret Manager
TOKEN_SECRET = get_secret("TOKEN_SECRET")
ENCRYPTION_KEY = get_secret("ENCRYPTION_KEY")
MAILGUN_API_KEY = get_secret("MAILGUN_API_KEY")
MAILGUN_DOMAIN = get_secret("MAILGUN_DOMAIN")
BASE_URL = get_secret(
    "BASE_URL"
)  # Your service’s public URL (e.g., "https://fmrl.ink")

# Initialize the token serializer and Fernet encryption
serializer = URLSafeTimedSerializer(TOKEN_SECRET)
fernet = Fernet(ENCRYPTION_KEY)


def send_email(to_address, subject, body):
    """
    Send an email using the Mailgun API.
    """
    if not MAILGUN_API_KEY or not MAILGUN_DOMAIN:
        logging.error("Mailgun API key or domain not set.")
        return

    from_address = f"fmrl.ink <mailgun@{MAILGUN_DOMAIN}>"
    url = f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages"

    response = requests.post(
        url,
        auth=("api", MAILGUN_API_KEY),
        data={
            "from": from_address,
            "to": [to_address],
            "subject": subject,
            "text": body,
        },
    )

    if response.status_code != 200:
        logging.error(f"Mailgun API error: {response.text}")
    else:
        logging.info(f"Email sent to {to_address} via Mailgun.")


def generate_unsubscribe_link(email, list_keyword):
    """
    Generate a secure unsubscribe link with a signed token.
    """
    token = serializer.dumps({"email": email, "list": list_keyword})
    unsubscribe_url = f"{BASE_URL}/unsubscribe?token={token}"
    return unsubscribe_url


def verify_unsubscribe_token(token, max_age=86400):
    """
    Verify the token from the unsubscribe link.
    """
    try:
        data = serializer.loads(token, max_age=max_age)
        return data["email"], data["list"]
    except SignatureExpired:
        raise Exception("The unsubscribe link has expired.")
    except BadSignature:
        raise Exception("Invalid unsubscribe token.")


def send_help_email(email):
    """
    Sends a help message outlining available commands.
    """
    help_text = (
        "Welcome to fmrl.ink ephemeral mailing lists!\n\n"
        "Commands:\n"
        "- To subscribe: Send an email with subject '<n> days' (e.g., '3 days') to anykeyword@fmrl.ink. CC additional addresses if desired.\n"
        "- To unsubscribe: Send an email with subject 'unsubscribe' or click the unsubscribe link at the bottom of every email.\n"
        "- To extend your subscription: Send 'extend <n> days'.\n"
        "- To check your status: Send 'info'.\n"
        "- To pause/resume notifications: Send 'pause' or 'resume'.\n"
    )
    send_email(email, "fmrl.ink Help", help_text)


def anonymize_email_content(email_data):
    """
    Remove any personally identifiable information from the email before relaying.
    For simplicity, only include the body.
    """
    return email_data.get("body", "")
