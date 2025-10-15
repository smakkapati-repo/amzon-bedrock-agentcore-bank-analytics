#!/bin/bash

# BankIQ+ Complete Deployment Script - Agent + Fargate Platform
set -e

echo "🚀 BankIQ+ Complete Deployment Starting..."
echo "📋 This will deploy: AgentCore Agent + Fargate Platform"

# Get user IP
USER_IP=$(curl -s https://checkip.amazonaws.com)
echo "📍 Your IP: $USER_IP"

# Get AWS account and region
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region || echo "us-east-1")
echo "🏗️  AWS Account: $AWS_ACCOUNT"
echo "🌍 AWS Region: $AWS_REGION"

echo ""
echo "📦 Step 1: Deploying AgentCore Agent..."

# Check if strands CLI is installed
if ! command -v agentcore &> /dev/null; then
    echo "📥 Installing Strands CLI..."
    pip install strands-agents bedrock-agentcore
fi

# Deploy the agent
cd backend
echo "🚀 Launching AgentCore agent..."
AGENT_OUTPUT=$(agentcore launch --local-build 2>&1)
echo "$AGENT_OUTPUT"

# Extract agent ARN from output
AGENT_ARN=$(echo "$AGENT_OUTPUT" | grep -o 'arn:aws:bedrock-agentcore:[^"]*' | head -1)

if [ -z "$AGENT_ARN" ]; then
    echo "❌ Failed to extract Agent ARN. Please check the output above."
    exit 1
fi

echo "✅ Agent deployed successfully!"
echo "🤖 Agent ARN: $AGENT_ARN"

cd ..

echo ""
echo "📦 Step 2: Building and pushing Docker images..."

# Build and push frontend
echo "🔨 Building frontend image..."
cd frontend
docker build --platform linux/amd64 -t bankiq-frontend .
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com

# Create ECR repos if they don't exist
aws ecr describe-repositories --repository-names bankiq-frontend --region $AWS_REGION 2>/dev/null || \
aws ecr create-repository --repository-name bankiq-frontend --region $AWS_REGION

docker tag bankiq-frontend:latest $AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com/bankiq-frontend:latest
docker push $AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com/bankiq-frontend:latest

# Build and push backend
echo "🔨 Building backend image..."
cd ../backend
docker build --platform linux/amd64 -t bankiq-backend .

aws ecr describe-repositories --repository-names bankiq-backend --region $AWS_REGION 2>/dev/null || \
aws ecr create-repository --repository-name bankiq-backend --region $AWS_REGION

docker tag bankiq-backend:latest $AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com/bankiq-backend:latest
docker push $AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com/bankiq-backend:latest

cd ..

echo ""
echo "📋 Step 3: Deploying Fargate infrastructure..."

aws cloudformation deploy \
  --template-file bank-iq-plus-fargate.yaml \
  --stack-name bankiq-complete-platform \
  --parameter-overrides \
    YourIPAddress=$USER_IP \
    AgentARNParameter=$AGENT_ARN \
  --capabilities CAPABILITY_IAM \
  --region $AWS_REGION

echo "✅ Infrastructure deployment complete!"

# Get outputs
ALB_URL=$(aws cloudformation describe-stacks \
  --stack-name bankiq-complete-platform \
  --query 'Stacks[0].Outputs[?OutputKey==`ApplicationURL`].OutputValue' \
  --output text \
  --region $AWS_REGION)

echo ""
echo "🎉 BankIQ+ Platform deployed successfully!"
echo "🤖 Agent ARN: $AGENT_ARN"
echo "🌐 Application URL: $ALB_URL"
echo "📊 Access your banking analytics platform at the URL above"
echo ""
echo "⏱️  Note: Services may take 2-3 minutes to fully start up"
echo "🔍 Monitor deployment: AWS Console → ECS → bankiq-platform-cluster"
echo ""
echo "📋 Share with others:"
echo "   - Give them this repository"
echo "   - They run: ./deploy-complete.sh"
echo "   - Each person gets their own agent + platform"