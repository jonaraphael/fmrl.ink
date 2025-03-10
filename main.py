import logging
import os
import re

from flask import Flask, jsonify, request

from db import (
    extend_subscription,
    get_subscribers,
    subscribe_user,
    unsubscribe_user,
)
from email_utils import (
    anonymize_email_content,
    generate_unsubscribe_link,
    send_email,
    send_help_email,
)

app = Flask(__name__)

# Regular expression for subscription command (e.g., "3 days")
SUBSCRIBE_REGEX = re.compile(r"^(\d+)\s*days$", re.IGNORECASE)
EXTEND_REGEX = re.compile(r"^extend\s+(\d+)\s*days$", re.IGNORECASE)


@app.route("/inbound", methods=["POST"])
def inbound_email():
    try:
        email_data = request.get_json(force=True)
        sender = email_data.get("sender")
        to_addr = email_data.get("to")  # e.g., "anykeyword@fmrl.ink"
        cc_list = email_data.get("cc", [])
        subject = email_data.get("subject", "").strip().lower()
        # body = email_data.get("body", "")
        list_keyword = to_addr.split("@")[0]

        logging.info(
            f"Processing email from {sender} to list {list_keyword} with subject '{subject}'."
        )

        subscribe_match = SUBSCRIBE_REGEX.match(subject)
        if subscribe_match:
            duration = int(subscribe_match.group(1))
            subscribe_user(list_keyword, sender, duration)
            if cc_list:
                for cc in cc_list:
                    subscribe_user(list_keyword, cc, duration)
            confirmation_msg = (
                f"You are now subscribed to {list_keyword} for {duration} day(s)."
            )
            send_email(
                sender, f"Subscription confirmed for {list_keyword}", confirmation_msg
            )
            return jsonify({"status": "subscribed"}), 200

        if subject == "unsubscribe":
            unsubscribe_user(list_keyword, sender)
            send_email(
                sender,
                f"Unsubscribed from {list_keyword}",
                "You have been unsubscribed.",
            )
            return jsonify({"status": "unsubscribed"}), 200

        extend_match = EXTEND_REGEX.match(subject)
        if extend_match:
            extension = int(extend_match.group(1))
            extend_subscription(list_keyword, sender, extension)
            send_email(
                sender,
                f"Subscription extended for {list_keyword}",
                f"Your subscription has been extended by {extension} day(s).",
            )
            return jsonify({"status": "extended"}), 200

        if subject in ["help", "info"]:
            send_help_email(sender)
            return jsonify({"status": "help_sent"}), 200

        subscribers = get_subscribers(list_keyword)
        if not subscribers:
            logging.warning("No active subscribers found; ignoring email relay.")
            return jsonify({"status": "no_subscribers"}), 404

        relay_body = anonymize_email_content(email_data)
        for sub in subscribers:
            if sub.get("email") != sender:
                unsubscribe_link = generate_unsubscribe_link(
                    sub.get("email"), list_keyword
                )
                relay_body_with_unsub = (
                    relay_body + f"\n\nUnsubscribe: {unsubscribe_link}"
                )
                send_email(
                    sub.get("email"),
                    f"[{list_keyword}] New message",
                    relay_body_with_unsub,
                )
        return jsonify({"status": "relayed"}), 200

    except Exception as e:
        logging.exception("Error processing inbound email.")
        return jsonify({"error": str(e)}), 500


@app.route("/cleanup", methods=["POST"])
def cleanup():
    from db import cleanup_expired

    try:
        cleanup_expired()
        return jsonify({"status": "cleanup complete"}), 200
    except Exception as e:
        logging.exception("Error during cleanup.")
        return jsonify({"error": str(e)}), 500


@app.route("/unsubscribe", methods=["GET"])
def unsubscribe_link():
    from email_utils import verify_unsubscribe_token

    try:
        token = request.args.get("token")
        if not token:
            return "Invalid unsubscribe link.", 400
        email, list_keyword = verify_unsubscribe_token(token)
        unsubscribe_user(list_keyword, email)
        return f"Successfully unsubscribed {email} from {list_keyword}.", 200
    except Exception:
        logging.exception("Error processing unsubscribe link.")
        return "Unsubscribe failed.", 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
