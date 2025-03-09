#!/bin/bash
set -e

# Optionally, set the region if not the default (update as needed)
REGION="us-central1"

echo "Deleting Cloud Functions..."
gcloud functions delete inbound-email --quiet --region=$REGION --gen2
gcloud functions delete cleanup --quiet --region=$REGION --gen2
gcloud functions delete unsubscribe-link --quiet --region=$REGION --gen2

echo "Deleting Cloud Scheduler job..."
gcloud scheduler jobs delete fmrlink-cleanup-job --quiet --location=$REGION

echo "Deleting Firestore data (collection 'lists')..."
python delete_firestore_data.py

echo "Teardown complete."
