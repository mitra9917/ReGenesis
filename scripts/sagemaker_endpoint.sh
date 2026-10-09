#!/usr/bin/env bash
# Cost-guard helper for regenesis-yolo-dev (ON = billing, OFF = stop billing)
set -euo pipefail

REGION="${AWS_REGION:-ap-south-1}"
ENDPOINT_NAME="${ENDPOINT_NAME:-regenesis-yolo-dev}"
MODEL_NAME="${MODEL_NAME:-regenesis-yolo-model-v2}"
CONFIG_NAME="${CONFIG_NAME:-regenesis-yolo-config-m5l-v2}"
ROLE_ARN="${SAGEMAKER_ROLE_ARN:-arn:aws:iam::620694778016:role/regenesis-sagemaker-exec}"
IMAGE="${SAGEMAKER_IMAGE:-763104351884.dkr.ecr.ap-south-1.amazonaws.com/pytorch-inference:2.3.0-cpu-py311-ubuntu20.04-sagemaker}"
MODEL_DATA="${MODEL_DATA:-s3://regenesis-dev-assetsbucket-xp9zjtzuwy50/models/regenesis-yolo/model.tar.gz}"

usage() {
  cat <<EOF
Usage: $0 {on|off|status|wait}

  on     Create endpoint if missing (STARTS BILLING)
  off    Delete endpoint (STOPS BILLING) — keeps model + config for fast recreate
  status Show endpoint status
  wait   Poll until InService or Failed
EOF
}

cmd_status() {
  if ! aws sagemaker describe-endpoint --endpoint-name "$ENDPOINT_NAME" --region "$REGION" \
    --query '{Status:EndpointStatus,Failure:FailureReason}' --output table 2>/dev/null; then
    echo "Endpoint '$ENDPOINT_NAME' does not exist (OFF — not billing)."
  fi
}

ensure_model() {
  if aws sagemaker describe-model --model-name "$MODEL_NAME" --region "$REGION" >/dev/null 2>&1; then
    return 0
  fi
  echo "Creating model $MODEL_NAME …"
  aws sagemaker create-model \
    --model-name "$MODEL_NAME" \
    --primary-container "Image=$IMAGE,ModelDataUrl=$MODEL_DATA,Mode=SingleModel,Environment={SAGEMAKER_PROGRAM=inference.py,SAGEMAKER_SUBMIT_DIRECTORY=/opt/ml/model/code,SAGEMAKER_CONTAINER_LOG_LEVEL=20,SAGEMAKER_REGION=$REGION}" \
    --execution-role-arn "$ROLE_ARN" \
    --region "$REGION" >/dev/null
}

ensure_config() {
  if aws sagemaker describe-endpoint-config --endpoint-config-name "$CONFIG_NAME" --region "$REGION" >/dev/null 2>&1; then
    return 0
  fi
  echo "Creating endpoint config $CONFIG_NAME (ml.m5.large) …"
  aws sagemaker create-endpoint-config \
    --endpoint-config-name "$CONFIG_NAME" \
    --production-variants "VariantName=AllTraffic,ModelName=$MODEL_NAME,InitialInstanceCount=1,InstanceType=ml.m5.large,InitialVariantWeight=1.0" \
    --region "$REGION" >/dev/null
}

cmd_on() {
  ensure_model
  ensure_config
  if aws sagemaker describe-endpoint --endpoint-name "$ENDPOINT_NAME" --region "$REGION" >/dev/null 2>&1; then
    echo "Endpoint already exists — status:"
    cmd_status
    return 0
  fi
  echo "⚠️  CREATING ENDPOINT — billing starts when Status becomes InService"
  aws sagemaker create-endpoint \
    --endpoint-name "$ENDPOINT_NAME" \
    --endpoint-config-name "$CONFIG_NAME" \
    --region "$REGION" \
    --tags Key=project,Value=regenesis Key=cost-guard,Value=delete-when-idle >/dev/null
  echo "Creating… run: $0 wait"
}

cmd_off() {
  if ! aws sagemaker describe-endpoint --endpoint-name "$ENDPOINT_NAME" --region "$REGION" >/dev/null 2>&1; then
    echo "Already OFF (no endpoint)."
    return 0
  fi
  echo "Deleting endpoint $ENDPOINT_NAME — stopping inference billing…"
  aws sagemaker delete-endpoint --endpoint-name "$ENDPOINT_NAME" --region "$REGION"
  echo "Delete requested. Confirm with: $0 status"
}

cmd_wait() {
  echo "Polling $ENDPOINT_NAME …"
  while true; do
    if ! STATUS=$(aws sagemaker describe-endpoint --endpoint-name "$ENDPOINT_NAME" --region "$REGION" \
      --query EndpointStatus --output text 2>/dev/null); then
      echo "Endpoint gone / not found."
      return 1
    fi
    echo "$(date -u +%H:%M:%S)Z  Status=$STATUS"
    case "$STATUS" in
      InService) echo "✅ InService — BILLING ON. Smoke-test then consider: $0 off"; return 0 ;;
      Failed)
        aws sagemaker describe-endpoint --endpoint-name "$ENDPOINT_NAME" --region "$REGION" \
          --query FailureReason --output text
        return 1
        ;;
      *) sleep 30 ;;
    esac
  done
}

case "${1:-}" in
  on) cmd_on ;;
  off) cmd_off ;;
  status) cmd_status ;;
  wait) cmd_wait ;;
  *) usage; exit 1 ;;
esac
