#!/bin/bash
set -e

# Define variables
PROJECT_ID="fmrl-453205"
REGION="us-central1"
SERVICE_ACCOUNT="fmrl-sa@fmrl-453205.iam.gserviceaccount.com"

# Deploy inbound email function with custom service account
gcloud functions deploy inbound-email \
  --entry-point inbound_email \
  --runtime python39 \
  --trigger-http \
  --allow-unauthenticated \
  --service-account ${SERVICE_ACCOUNT} \
  --project ${PROJECT_ID} \
  --region ${REGION}

# Deploy cleanup function (triggered by Cloud Scheduler) with custom service account
gcloud functions deploy cleanup \
  --entry-point cleanup \
  --runtime python39 \
  --trigger-http \
  --allow-unauthenticated \
  --service-account ${SERVICE_ACCOUNT} \
  --project ${PROJECT_ID} \
  --region ${REGION}

# Deploy unsubscribe link handler with custom service account
gcloud functions deploy unsubscribe-link \
  --entry-point unsubscribe_link \
  --runtime python39 \
  --trigger-http \
  --allow-unauthenticated \
  --service-account ${SERVICE_ACCOUNT} \
  --project ${PROJECT_ID} \
  --region ${REGION}

# Get the cleanup function URL using the Gen2 field
CLEANUP_URL=$(gcloud functions describe cleanup \
  --project ${PROJECT_ID} \
  --region ${REGION} \
  --format='value(serviceConfig.uri)')

if [[ -z "$CLEANUP_URL" ]]; then
  echo "Error: Cleanup function URL is empty."
  exit 1
fi

# Configure Cloud Scheduler to hit the cleanup endpoint daily.
gcloud scheduler jobs create http fmrlink-cleanup-job \
  --schedule="0 0 * * *" \
  --http-method=POST \
  --uri="${CLEANUP_URL}" \
  --time-zone="UTC" \
  --attempt-deadline=60s \
  --project ${PROJECT_ID} \
  --location ${REGION} \
  --quiet

echo "Deployment complete."
