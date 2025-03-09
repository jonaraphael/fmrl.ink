# FMRL Ink

fmrl.ink provides ephemeral, anonymous, and secure mailing lists, ideal for short-term collaborations, activist organizing, and temporary group communication. Subscribers remain completely anonymous, and all subscription data is permanently erased upon expiry, ensuring maximum privacy.

## ⚙️ How It Works

- **Create a Mailing List:**\
  Send an email with the subject line `3 days` (or any number of days) to:

  ```
  anykeyword@fmrl.ink
  ```

  This subscribes your email anonymously for the specified number of days.

- **Notify Others:**\
  CC additional recipients to notify them of the group's existence. They can subscribe similarly.

- **Anonymity Guaranteed:**\
  Any email sent to the generated address will anonymously forward to all current subscribers.

- **Automatic Expiration:**\
  After the subscription duration ends, you're automatically unsubscribed. When no subscribers remain, the list permanently disappears, leaving no trace.

## 📬 Commands & Shortcuts

- **Subscribe:** Send an email with subject `X days`.
- **Unsubscribe:** Subject line: `unsubscribe` or click the unsubscribe link at the bottom of emails.
- **Extend Subscription:** Subject line: `extend X`.
- **Help:** Subject line: `help` to receive detailed instructions.

## 🔐 Privacy & Security Guarantees

- **Ephemeral Storage:** All subscriber data is deleted permanently once expired.
- **Anonymous Emails:** Sender identity and subscriber lists are never revealed.
- **Encryption:** Subscribers' emails are encrypted with Google Cloud KMS.
- **Court-proof Privacy:** Algorithmic privacy ensures no historical subscriber data can ever be recovered or accessed.

## 🛠 Tech Stack

- **Google Cloud Platform:** Firestore, Cloud Functions, KMS, Cloud Scheduler
- **Language:** Python 3.9+
- **Database:** Firestore with TTL indexes
- **Email Integration:** Mailgun, SendGrid, or similar providers

## 🚀 Quickstart & Deployment

### Prerequisites

- Google Cloud Account
- `gcloud` CLI installed
- Firestore set up (Native mode)
- KMS key configured (set as environment variable)

### Deploying to Google Cloud

1. Clone and enter the repository:

```bash
git clone https://github.com/yourusername/fmrl-ink.git
cd fmrl-ink
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Deploy Cloud Functions:

**Email Handler**

```bash
gcloud functions deploy email_handler \
  --runtime python39 \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars KMS_KEY_NAME="projects/your-project/locations/global/keyRings/your-keyring/cryptoKeys/your-key"
```

**Cleanup Job:**

```bash
gcloud functions deploy cleanup_handler \
  --runtime python39 \
  --trigger-http \
  --allow-unauthenticated

# Schedule cleanup hourly
gcloud scheduler jobs create http cleanup-job \
  --schedule="0 * * * *" \
  --uri="https://YOUR_REGION-YOUR_PROJECT.cloudfunctions.net/cleanup_handler" \
  --http-method GET
```

## 🔒 Security

- **Ephemeral Data:** Automatically deleted subscriptions ensure no persistent data.
- **Strong Encryption:** Google Cloud KMS encrypts all sensitive data.
- **No Logs:** Designed for maximal privacy; no historical logs are retained.

## 🙌 Contributing

We welcome contributions! Fork, make changes, and submit a PR.

## 📃 License

[MIT](LICENSE)

