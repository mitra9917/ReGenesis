#!/usr/bin/env bash
# Build React UI for production and sync to the stack's public S3 website bucket.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STACK_NAME="${STACK_NAME:-regenesis-dev}"
AWS_REGION="${AWS_REGION:-ap-south-1}"

: "${AWS_PROFILE:?Set AWS_PROFILE (e.g. regenesis)}"

API_URL="$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$AWS_REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" \
  --output text)"
UI_BUCKET="$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$AWS_REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='UiBucketName'].OutputValue" \
  --output text)"
WEB_URL="$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$AWS_REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='UiWebsiteUrl'].OutputValue" \
  --output text)"

API_URL="${API_URL%/}"

echo "Stack: $STACK_NAME | API: $API_URL"
echo "UI bucket: $UI_BUCKET"
echo "Website: $WEB_URL"

cd "$ROOT/frontend"
if [[ -f package-lock.json ]]; then
  npm ci
else
  npm install
fi

export VITE_API_URL="$API_URL"
npm run build

aws s3 sync dist/ "s3://${UI_BUCKET}/" --delete --region "$AWS_REGION"

echo ""
echo "Hosted UI deployed."
echo "Open: $WEB_URL"
echo "Production build uses VITE_API_URL=$API_URL"
