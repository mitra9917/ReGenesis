#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../infrastructure/sam"
STACK="${1:-regenesis-dev}"
echo "Deleting CloudFormation stack: $STACK"
aws cloudformation delete-stack --stack-name "$STACK"
echo "Remember to delete SageMaker endpoint manually if created."
