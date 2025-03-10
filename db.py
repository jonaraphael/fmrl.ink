import hashlib
import logging
from datetime import datetime, timedelta

from cryptography.fernet import Fernet
from google.cloud import firestore

from gcp_secrets import get_secret

# Retrieve ENCRYPTION_KEY from Secret Manager
ENCRYPTION_KEY = get_secret("ENCRYPTION_KEY")
fernet = Fernet(ENCRYPTION_KEY)
db_client = firestore.Client()


def _hash_email(email):
    """Return a SHA256 hash of the email address for document IDs."""
    return hashlib.sha256(email.encode("utf-8")).hexdigest()


def encrypt_email(email):
    """Encrypt the email address."""
    return fernet.encrypt(email.encode("utf-8")).decode("utf-8")


def decrypt_email(encrypted_email):
    """Decrypt the email address."""
    return fernet.decrypt(encrypted_email.encode("utf-8")).decode("utf-8")


def subscribe_user(list_keyword, email, duration_days):
    """
    Subscribe a user to a mailing list.
    """
    list_ref = db_client.collection("lists").document(list_keyword)
    list_doc = list_ref.get()
    if not list_doc.exists:
        list_ref.set({"created_at": datetime.utcnow()})
        logging.info(f"Created new list: {list_keyword}")

    expiration = datetime.utcnow() + timedelta(days=duration_days)
    subscriber_id = _hash_email(email)
    subscriber_data = {
        "email": encrypt_email(email),
        "expires_at": expiration,
        "subscribed_at": datetime.utcnow(),
    }
    list_ref.collection("subscribers").document(subscriber_id).set(subscriber_data)
    logging.info(f"Subscribed {email} to list {list_keyword} until {expiration}.")


def unsubscribe_user(list_keyword, email):
    """
    Unsubscribe a user from a mailing list.
    """
    list_ref = db_client.collection("lists").document(list_keyword)
    subscriber_id = _hash_email(email)
    list_ref.collection("subscribers").document(subscriber_id).delete()
    logging.info(f"Unsubscribed {email} from list {list_keyword}.")


def extend_subscription(list_keyword, email, extension_days):
    """
    Extend a subscriber's expiration date by extension_days.
    """
    list_ref = db_client.collection("lists").document(list_keyword)
    subscriber_id = _hash_email(email)
    sub_ref = list_ref.collection("subscribers").document(subscriber_id)
    sub_doc = sub_ref.get()
    if sub_doc.exists:
        current_exp = sub_doc.get("expires_at")
        new_exp = current_exp + timedelta(days=extension_days)
        sub_ref.update({"expires_at": new_exp})
        logging.info(
            f"Extended subscription for {email} to {new_exp} in list {list_keyword}."
        )
    else:
        logging.warning(f"Subscription for {email} in list {list_keyword} not found.")


def get_subscribers(list_keyword):
    """
    Return a list of subscribers for the given mailing list.
    """
    list_ref = db_client.collection("lists").document(list_keyword)
    subs = list_ref.collection("subscribers").stream()
    subscribers = []
    for sub in subs:
        data = sub.to_dict()
        try:
            email = decrypt_email(data["email"])
        except Exception as e:
            logging.error(f"Error decrypting email for subscriber {sub.id}: {e}")
            continue
        subscribers.append({"email": email, "expires_at": data["expires_at"]})
    return subscribers


def cleanup_expired():
    """
    Remove expired subscriptions and delete empty lists.
    """
    lists = db_client.collection("lists").stream()
    now = datetime.utcnow()
    for list_doc in lists:
        list_keyword = list_doc.id
        list_ref = db_client.collection("lists").document(list_keyword)
        subs = list_ref.collection("subscribers").stream()
        for sub in subs:
            data = sub.to_dict()
            if data["expires_at"] < now:
                sub.reference.delete()
                logging.info(
                    f"Deleted expired subscription {sub.id} in list {list_keyword}."
                )
        if not any(list_ref.collection("subscribers").limit(1).stream()):
            list_ref.delete()
            logging.info(
                f"Deleted list {list_keyword} as it has no active subscribers."
            )
