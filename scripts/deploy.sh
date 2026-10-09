#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=sam-env.sh
source "$ROOT/scripts/sam-env.sh"
cd "$ROOT/infrastructure/sam"

echo "Building SAM application..."
sam build

echo "Deploying stack (use samconfig.toml or guided prompts)..."
if [[ -f samconfig.toml ]]; then
  sam deploy
else
  sam deploy --guided
fi

echo "Deploy hosted UI (reads ApiUrl + UiBucketName from stack outputs):"
echo "  AWS_PROFILE=regenesis ./scripts/deploy_ui.sh"
