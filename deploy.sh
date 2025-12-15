#!/bin/bash

echo "=========================================="
echo "MediaForge Cloud Run Deploy Script"
echo "=========================================="

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "[ERROR] gcloud CLI is not installed."
    exit 1
fi

echo ""
echo "Checking gcloud configuration..."
PROJECT_ID=$(gcloud config get-value project)

if [ -z "$PROJECT_ID" ]; then
    echo "[ERROR] Google Cloud Project is not selected."
    echo "Please run 'gcloud config set project [PROJECT_ID]' or 'gcloud init'."
    exit 1
fi

echo ""
echo "Target Project: $PROJECT_ID"
echo "Target Region: asia-northeast1 (Tokyo)"
echo "Service Name: mediaforge"
echo ""
read -p "Are you sure you want to deploy? (y/n): " CONFIRM

if [[ "$CONFIRM" != "y" ]]; then
    echo "Deployment cancelled."
    exit 0
fi

echo ""
echo "Starting deployment... this may take a few minutes."
echo ""

gcloud run deploy mediaforge \
  --source . \
  --region asia-northeast1 \
  --allow-unauthenticated

if [ $? -eq 0 ]; then
    echo ""
    echo "[SUCCESS] Deployment completed successfully!"
else
    echo ""
    echo "[ERROR] Deployment failed."
fi
