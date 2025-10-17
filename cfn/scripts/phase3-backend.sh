#!/bin/bash
set -e

STACK_NAME=${1:-bankiq}
REGION=${2:-us-east-1}

echo "=========================================="
echo "PHASE 3: Deploy Backend"
echo "=========================================="

# Load dependencies from previous phases
AGENT_ARN=$(cat /tmp/agent_arn.txt)
BACKEND_ECR=$(cat /tmp/backend_ecr.txt)
VPC_ID=$(cat /tmp/vpc_id.txt)
SUBNET_IDS=$(cat /tmp/subnet_ids.txt)

echo "Agent ARN: $AGENT_ARN"
echo "Backend ECR: $BACKEND_ECR"

# Build and push Docker image
echo "🚀 Building backend Docker image..."
cd ../../backend
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $(echo $BACKEND_ECR | cut -d'/' -f1)
docker build --platform linux/amd64 -t $BACKEND_ECR:latest -f Dockerfile.backend .
docker push $BACKEND_ECR:latest
echo "✅ Backend image pushed"

# Deploy backend stack
echo "🚀 Deploying backend stack..."
cd ../cfn/templates
aws cloudformation create-stack \
  --stack-name ${STACK_NAME}-backend \
  --template-body file://backend.yaml \
  --parameters \
    ParameterKey=ProjectName,ParameterValue=$STACK_NAME \
    ParameterKey=PrerequisitesStackName,ParameterValue=${STACK_NAME}-infra \
    ParameterKey=AgentArn,ParameterValue=$AGENT_ARN \
    ParameterKey=VpcId,ParameterValue=$VPC_ID \
    ParameterKey=SubnetIds,ParameterValue=\"$SUBNET_IDS\" \
    ParameterKey=BackendImageTag,ParameterValue=latest \
  --capabilities CAPABILITY_NAMED_IAM \
  --region $REGION

echo "⏳ Waiting for backend deployment (7-10 minutes)..."
aws cloudformation wait stack-create-complete --stack-name ${STACK_NAME}-backend --region $REGION

# Get ALB URL
ALB_URL=$(aws cloudformation describe-stacks --stack-name ${STACK_NAME}-backend --region $REGION --query 'Stacks[0].Outputs[?OutputKey==`ALBUrl`].OutputValue' --output text)
echo "$ALB_URL" > /tmp/alb_url.txt

echo ""
echo "✅ PHASE 3 COMPLETE"
echo "Backend URL: $ALB_URL"
echo ""
echo "Next: Run phase4-frontend.sh"
