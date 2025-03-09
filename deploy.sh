#!/bin/bash
set -e

# List active accounts; if none, exit with error.
ACTIVE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)")
if [ -z "$ACTIVE_ACCOUNT" ]; then
  echo "No active account found. Exiting."
  exit 1
else
  echo "Active account: $ACTIVE_ACCOUNT"
fi

# Deploy inbound email function
gcloud functions deploy inbound-email \
  --entry-point inbound_email \
  --runtime python39 \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars "ENCRYPTION_KEY=${ENCRYPTION_KEY},TOKEN_SECRET=${TOKEN_SECRET},BASE_URL=${BASE_URL},MAILGUN_API_KEY=${MAILGUN_API_KEY},MAILGUN_DOMAIN=${MAILGUN_DOMAIN}"

# Deploy cleanup function (to be triggered by Cloud Scheduler)
gcloud functions deploy cleanup \
  --entry-point cleanup \
  --runtime python39 \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars "ENCRYPTION_KEY=${ENCRYPTION_KEY},MAILGUN_API_KEY=${MAILGUN_API_KEY},MAILGUN_DOMAIN=${MAILGUN_DOMAIN}"

# Deploy unsubscribe link handler
gcloud functions deploy unsubscribe-link \
  --entry-point unsubscribe_link \
  --runtime python39 \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars "ENCRYPTION_KEY=${ENCRYPTION_KEY},TOKEN_SECRET=${TOKEN_SECRET},BASE_URL=${BASE_URL},MAILGUN_API_KEY=${MAILGUN_API_KEY},MAILGUN_DOMAIN=${MAILGUN_DOMAIN}"

# (Optional) Configure Cloud Scheduler to hit the cleanup endpoint daily.
# Example: run cleanup every day at midnight.
gcloud scheduler jobs create http fmrlink-cleanup-job \
  --schedule="0 0 * * *" \
  --http-method=POST \
  --uri="$(gcloud functions describe cleanup --format='value(httpsTrigger.url)')" \
  --time-zone="UTC" \
  --attempt-deadline=60s --quiet

echo "Deployment complete."
