#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=sam-env.sh
source "$ROOT/scripts/sam-env.sh"
cd "$ROOT/infrastructure/sam"

sam build
sam local invoke InvokeDetectionFunction --event "$ROOT/events/recovery_flow_input.json" \
  --env-vars "$ROOT/events/env.json" 2>/dev/null || \
sam local invoke InvokeDetectionFunction --event "$ROOT/events/recovery_flow_input.json"
