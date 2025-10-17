#!/bin/bash
set -e

STACK_NAME=${1:-bankiq}
REGION=${2:-us-east-1}

echo "=========================================="
echo "PHASE 0: Cleanup Existing Resources"
echo "=========================================="

# Delete CloudFormation stacks
echo "🗑️  Deleting CloudFormation stacks..."
aws cloudformation delete-stack --stack-name ${STACK_NAME}-frontend --region $REGION 2>/dev/null || true
aws cloudformation delete-stack --stack-name ${STACK_NAME}-backend --region $REGION 2>/dev/null || true
aws cloudformation delete-stack --stack-name ${STACK_NAME}-infra --region $REGION 2>/dev/null || true
aws cloudformation delete-stack --stack-name ${STACK_NAME} --region $REGION 2>/dev/null || true

echo "⏳ Waiting for stacks to delete (this may take 5-10 minutes)..."
aws cloudformation wait stack-delete-complete --stack-name ${STACK_NAME}-frontend --region $REGION 2>/dev/null || true
aws cloudformation wait stack-delete-complete --stack-name ${STACK_NAME}-backend --region $REGION 2>/dev/null || true
aws cloudformation wait stack-delete-complete --stack-name ${STACK_NAME}-infra --region $REGION 2>/dev/null || true
aws cloudformation wait stack-delete-complete --stack-name ${STACK_NAME} --region $REGION 2>/dev/null || true

# Delete agent
echo "🗑️  Deleting AgentCore agent..."
cd ../../backend
agentcore destroy -a bank_iq_agent_v1 --force 2>/dev/null || true
cd ../cfn/scripts

# Delete ECR repos
echo "🗑️  Deleting ECR repositories..."
aws ecr delete-repository --repository-name ${STACK_NAME}-backend-prod --region $REGION --force 2>/dev/null || true
aws ecr delete-repository --repository-name bedrock-agentcore-${STACK_NAME}-agent-prod --region $REGION --force 2>/dev/null || true

# Delete S3 buckets
echo "🗑️  Deleting S3 buckets..."
for bucket in $(aws s3 ls | grep "${STACK_NAME}" | awk '{print $3}'); do
    echo "Deleting bucket: $bucket"
    aws s3 rb s3://$bucket --force 2>/dev/null || true
done

# Delete staging buckets
for bucket in $(aws s3 ls | grep "${STACK_NAME}-cfn-staging" | awk '{print $3}'); do
    echo "Deleting staging bucket: $bucket"
    aws s3 rb s3://$bucket --force 2>/dev/null || true
done

echo ""
echo "✅ CLEANUP COMPLETE"
echo ""
echo "Next: Run phase1-agent.sh"
