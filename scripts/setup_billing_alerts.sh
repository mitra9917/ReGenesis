#!/usr/bin/env bash
# Create RE:GENESIS hackathon cost guards: AWS Budget ($25/$50) + CloudWatch billing alarms.
# Requires: AWS CLI, profile with budgets + cloudwatch + sns permissions.
set -euo pipefail

: "${AWS_PROFILE:?Set AWS_PROFILE (e.g. regenesis)}"
: "${BILLING_ALERT_EMAIL:?Set BILLING_ALERT_EMAIL for budget + SNS notifications}"

ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
BUDGET_NAME="regenesis-hackathon-monthly"
SNS_TOPIC="regenesis-billing-alerts"
REGION_PRIMARY="${AWS_REGION:-ap-south-1}"

echo "Account: $ACCOUNT | primary region: $REGION_PRIMARY | alerts: $BILLING_ALERT_EMAIL"

aws budgets create-budget --account-id "$ACCOUNT" \
  --budget "{
    \"BudgetName\": \"$BUDGET_NAME\",
    \"BudgetLimit\": {\"Amount\": \"75\", \"Unit\": \"USD\"},
    \"BudgetType\": \"COST\",
    \"TimeUnit\": \"MONTHLY\"
  }" \
  --notifications-with-subscribers "[
    {\"Notification\":{\"NotificationType\":\"ACTUAL\",\"ComparisonOperator\":\"GREATER_THAN\",\"Threshold\":25,\"ThresholdType\":\"ABSOLUTE_VALUE\"},\"Subscribers\":[{\"SubscriptionType\":\"EMAIL\",\"Address\":\"$BILLING_ALERT_EMAIL\"}]},
    {\"Notification\":{\"NotificationType\":\"ACTUAL\",\"ComparisonOperator\":\"GREATER_THAN\",\"Threshold\":50,\"ThresholdType\":\"ABSOLUTE_VALUE\"},\"Subscribers\":[{\"SubscriptionType\":\"EMAIL\",\"Address\":\"$BILLING_ALERT_EMAIL\"}]},
    {\"Notification\":{\"NotificationType\":\"FORECASTED\",\"ComparisonOperator\":\"GREATER_THAN\",\"Threshold\":50,\"ThresholdType\":\"ABSOLUTE_VALUE\"},\"Subscribers\":[{\"SubscriptionType\":\"EMAIL\",\"Address\":\"$BILLING_ALERT_EMAIL\"}]}
  ]" 2>/dev/null || echo "Budget may already exist (ok)."

TOPIC_ARN="$(aws sns create-topic --region us-east-1 --name "$SNS_TOPIC" --query TopicArn --output text)"
aws sns subscribe --region us-east-1 --topic-arn "$TOPIC_ARN" --protocol email \
  --notification-endpoint "$BILLING_ALERT_EMAIL" >/dev/null || true

for THRESH in 25 50; do
  aws cloudwatch put-metric-alarm --region us-east-1 \
    --alarm-name "regenesis-estimated-charges-${THRESH}usd" \
    --alarm-description "RE:GENESIS: estimated charges exceed \$${THRESH} USD" \
    --metric-name EstimatedCharges --namespace AWS/Billing --statistic Maximum \
    --period 21600 --evaluation-periods 1 --threshold "$THRESH" \
    --comparison-operator GreaterThanThreshold \
    --dimensions Name=Currency,Value=USD \
    --alarm-actions "$TOPIC_ARN"
done

echo "Done. Confirm Budget + SNS emails. In Billing console (root), enable 'Receive CloudWatch Billing Alerts' if alarms stay INSUFFICIENT_DATA."
