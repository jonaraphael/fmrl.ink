import base64
import logging
import os
from datetime import datetime

import requests  # New dependency for Mailgun API
from cryptography.fernet import Fernet
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

# Configure secrets (make sure these are set as environment variables)
TOKEN_SECRET = os.environ.get("TOKEN_SECRET", "default-token-secret")
ENCRYPTION_KEY = os.environ.get(
    "ENCRYPTION_KEY"
)  # Must be a 32-byte URL-safe base64-encoded key

# Mailgun configuration from environment
MAILGUN_API_KEY = os.environ.get("MAILGUN_API_KEY")
MAILGUN_DOMAIN = os.environ.get("MAILGUN_DOMAIN")

if not ENCRYPTION_KEY:
    raise Exception("ENCRYPTION_KEY environment variable not set")

# Initialize the token serializer
serializer = URLSafeTimedSerializer(TOKEN_SECRET)

# Initialize Fernet encryption
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
    base_url = os.environ.get("BASE_URL", "https://fmrl.ink")
    unsubscribe_url = f"{base_url}/unsubscribe?token={token}"
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
    This might include stripping headers or sender information.
    """
    # For simplicity, only include the body. A production version might
    # do more sophisticated processing.
    return email_data.get("body", "")
