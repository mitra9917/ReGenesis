#!/usr/bin/env bash
# Build React UI for production and sync to S3 / CloudFront.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STACK_NAME="${STACK_NAME:-regenesis-dev}"
AWS_REGION="${AWS_REGION:-ap-south-1}"

PROFILE_ARG=()
if [[ -n "${AWS_PROFILE:-}" ]]; then
  PROFILE_ARG=("--profile" "$AWS_PROFILE")
fi

echo "=========================================================="
echo "  RE:GENESIS - Deploy Web UI to AWS Hosting (S3 / CloudFront)"
echo "=========================================================="
echo "Querying CloudFormation stack: $STACK_NAME (Region: $AWS_REGION)..."

API_URL="$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$AWS_REGION" \
  "${PROFILE_ARG[@]}" \
  --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" \
  --output text)"
UI_BUCKET="$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$AWS_REGION" \
  "${PROFILE_ARG[@]}" \
  --query "Stacks[0].Outputs[?OutputKey=='UiBucketName'].OutputValue" \
  --output text)"
WEB_URL="$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$AWS_REGION" \
  "${PROFILE_ARG[@]}" \
  --query "Stacks[0].Outputs[?OutputKey=='UiWebsiteUrl'].OutputValue" \
  --output text)"
CLOUDFRONT_URL="$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$AWS_REGION" \
  "${PROFILE_ARG[@]}" \
  --query "Stacks[0].Outputs[?OutputKey=='CloudFrontUrl'].OutputValue" \
  --output text 2>/dev/null || echo "")"
DIST_ID="$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$AWS_REGION" \
  "${PROFILE_ARG[@]}" \
  --query "Stacks[0].Outputs[?OutputKey=='CloudFrontDistributionId'].OutputValue" \
  --output text 2>/dev/null || echo "")"

API_URL="${API_URL%/}"

echo "Stack:           $STACK_NAME"
echo "API Gateway:     $API_URL"
echo "Target S3 Bucket: $UI_BUCKET"
echo "S3 Website URL:  $WEB_URL"
if [[ -n "$CLOUDFRONT_URL" && "$CLOUDFRONT_URL" != "None" ]]; then
  echo "CloudFront URL:  $CLOUDFRONT_URL"
fi

cd "$ROOT/frontend"
if [[ -f package-lock.json ]]; then
  npm ci
else
  npm install
fi

echo ""
echo "Building Vite frontend bundle with VITE_API_URL=$API_URL..."
export VITE_API_URL="$API_URL"
npm run build

echo ""
echo "Syncing assets to s3://${UI_BUCKET}/..."
aws s3 sync dist/ "s3://${UI_BUCKET}/" --delete --region "$AWS_REGION" "${PROFILE_ARG[@]}"

if [[ -n "$DIST_ID" && "$DIST_ID" != "None" ]]; then
  echo "Invalidating CloudFront distribution $DIST_ID..."
  aws cloudfront create-invalidation --distribution-id "$DIST_ID" --paths "/*" "${PROFILE_ARG[@]}" || true
fi

echo ""
echo "=========================================================="
echo "  SUCCESS: RE:GENESIS Web UI Deployed to AWS!"
echo "=========================================================="
echo "Primary Live URL: $WEB_URL"
if [[ -n "$CLOUDFRONT_URL" && "$CLOUDFRONT_URL" != "None" ]]; then
  echo "CloudFront CDN:  $CLOUDFRONT_URL"
fi
echo "Connected API:    $API_URL"
