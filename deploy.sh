#!/bin/bash
set -e

# Deploy inbound email function
gcloud functions deploy inbound-email \
  --entry-point inbound_email \
  --runtime python39 \
  --trigger-http \
  --allow-unauthenticated

# Deploy cleanup function (triggered by Cloud Scheduler)
gcloud functions deploy cleanup \
  --entry-point cleanup \
  --runtime python39 \
  --trigger-http \
  --allow-unauthenticated

# Deploy unsubscribe link handler
gcloud functions deploy unsubscribe-link \
  --entry-point unsubscribe_link \
  --runtime python39 \
  --trigger-http \
  --allow-unauthenticated

# Configure Cloud Scheduler to hit the cleanup endpoint daily.
gcloud scheduler jobs create http fmrlink-cleanup-job \
  --schedule="0 0 * * *" \
  --http-method=POST \
  --uri="$(gcloud functions describe cleanup --format='value(httpsTrigger.url)')" \
  --time-zone="UTC" \
  --attempt-deadline=60s --quiet

echo "Deployment complete."
