#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/infrastructure/sam"

echo "Building SAM application..."
sam build

echo "Deploying stack (use samconfig.toml or guided prompts)..."
if [[ -f samconfig.toml ]]; then
  sam deploy
else
  sam deploy --guided
fi

echo "Build frontend and sync to UI bucket (set UI_BUCKET from stack outputs):"
echo "  cd frontend && npm ci && npm run build"
echo "  aws s3 sync dist/ s3://\${UI_BUCKET}/ --delete"
