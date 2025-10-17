#!/bin/bash
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

# Banner
clear
echo -e "${MAGENTA}"
cat << "EOF"
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   ██████╗  █████╗ ███╗   ██╗██╗  ██╗██╗ ██████╗       ██╗                  ║
║   ██╔══██╗██╔══██╗████╗  ██║██║ ██╔╝██║██╔═══██╗    ██╔╝                  ║
║   ██████╔╝███████║██╔██╗ ██║█████╔╝ ██║██║   ██║   ██╔╝                   ║
║   ██╔══██╗██╔══██║██║╚██╗██║██╔═██╗ ██║██║▄▄ ██║  ██╔╝                    ║
║   ██████╔╝██║  ██║██║ ╚████║██║  ██╗██║╚██████╔╝ ██╔╝                     ║
║   ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝ ╚══▀▀═╝  ╚═╝                      ║
║                                                                              ║
║              AI-Powered Banking Analytics Platform                           ║
║                    CloudFormation Deployment                                 ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"
echo ""

# Parse stack name from argument or prompt
if [ $# -eq 1 ]; then
  STACK_NAME="$1"
else
  echo -e "${CYAN}📝 Enter your deployment details:${NC}"
  echo ""
  read -p "Stack name (default: bankiq): " STACK_NAME
  STACK_NAME=${STACK_NAME:-bankiq}
fi

# Auto-detect region from AWS CLI config
REGION=$(aws configure get region 2>/dev/null || echo "us-east-1")

# Set defaults
PROJECT_NAME="$STACK_NAME"
ENVIRONMENT="prod"
MODEL_ID="us.anthropic.claude-sonnet-4-5-20250929-v1:0"
CREATE_VPC="true"

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}                     ${WHITE}DEPLOYMENT CONFIGURATION${NC}                        ${BLUE}║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${CYAN}📦 Stack Name:${NC}     ${WHITE}$STACK_NAME${NC}"
echo -e "  ${CYAN}🌍 Region:${NC}         ${WHITE}$REGION${NC}"
echo -e "  ${CYAN}🏗️  VPC:${NC}           ${WHITE}New VPC with 2 public subnets${NC}"
echo -e "  ${CYAN}🤖 AI Model:${NC}       ${WHITE}Claude Sonnet 4.5${NC}"
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}                      ${WHITE}WHAT WILL BE CREATED${NC}                          ${BLUE}║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${GREEN}✓${NC} VPC with Internet Gateway & 2 Public Subnets"
echo -e "  ${GREEN}✓${NC} AgentCore Agent powered by Claude Sonnet 4.5"
echo -e "  ${GREEN}✓${NC} ECS Fargate Cluster with Application Load Balancer"
echo -e "  ${GREEN}✓${NC} CloudFront Distribution with S3 Static Hosting"
echo -e "  ${GREEN}✓${NC} ECR Repositories for Docker Images"
echo -e "  ${GREEN}✓${NC} S3 Buckets for Frontend & Document Storage"
echo -e "  ${GREEN}✓${NC} IAM Roles & Security Groups"
echo -e "  ${GREEN}✓${NC} CloudWatch Log Groups"
echo ""
echo -e "${YELLOW}╔════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║${NC}  ⏱️  Estimated Time: ${WHITE}15-20 minutes${NC}                                   ${YELLOW}║${NC}"
echo -e "${YELLOW}║${NC}  💰 Estimated Cost:  ${WHITE}~\$50-90/month${NC} (24/7 operation)                  ${YELLOW}║${NC}"
echo -e "${YELLOW}╚════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Create staging bucket
STAGING_BUCKET="${STACK_NAME}-cfn-staging-$(date +%s)"
echo -e "${YELLOW}📦 Creating staging bucket: $STAGING_BUCKET${NC}"
aws s3 mb s3://$STAGING_BUCKET --region $REGION

# Upload templates
echo -e "${YELLOW}📤 Uploading CloudFormation templates...${NC}"
aws s3 sync templates/ s3://$STAGING_BUCKET/templates/ --region $REGION --quiet

# Upload agent source
echo -e "${YELLOW}📤 Uploading agent source...${NC}"
aws s3 cp artifacts/agent.zip s3://$STAGING_BUCKET/agent.zip --region $REGION --quiet

# Upload backend Docker image to S3 (will be pushed to ECR by Lambda)
echo -e "${YELLOW}📤 Uploading backend Docker image to S3...${NC}"
aws s3 cp artifacts/backend-image.tar.gz s3://$STAGING_BUCKET/backend-image.tar.gz --region $REGION --quiet
echo "✅ Backend image uploaded to S3"

# Upload frontend build to S3
echo -e "${YELLOW}📤 Uploading frontend build to S3...${NC}"
aws s3 cp artifacts/frontend-build.zip s3://$STAGING_BUCKET/frontend-build.zip --region $REGION --quiet
echo "✅ Frontend build uploaded"

# Deploy master stack
echo ""
echo -e "${GREEN}🚀 Deploying CloudFormation stack...${NC}"
echo "This will take 15-20 minutes..."
echo ""

aws cloudformation create-stack \
  --stack-name $STACK_NAME \
  --template-url https://$STAGING_BUCKET.s3.$REGION.amazonaws.com/templates/master.yaml \
  --parameters \
    ParameterKey=ProjectName,ParameterValue=$PROJECT_NAME \
    ParameterKey=Environment,ParameterValue=$ENVIRONMENT \
    ParameterKey=ModelId,ParameterValue=$MODEL_ID \
    ParameterKey=AgentSourceBucket,ParameterValue=$STAGING_BUCKET \
    ParameterKey=AgentSourceKey,ParameterValue=agent.zip \
    ParameterKey=BackendImageTag,ParameterValue=latest \
    ParameterKey=BackendImageS3Bucket,ParameterValue=$STAGING_BUCKET \
    ParameterKey=BackendImageS3Key,ParameterValue=backend-image.tar.gz \
    ParameterKey=FrontendBuildS3Key,ParameterValue=frontend-build.zip \
    ParameterKey=TemplatesBucket,ParameterValue=$STAGING_BUCKET \
  --capabilities CAPABILITY_NAMED_IAM \
  --region $REGION

echo ""
echo -e "${YELLOW}⏳ Waiting for stack creation...${NC}"
aws cloudformation wait stack-create-complete --stack-name $STACK_NAME --region $REGION

# Get outputs
echo ""
echo -e "${GREEN}✅ Stack created successfully!${NC}"
echo ""

FRONTEND_BUCKET=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --query 'Stacks[0].Outputs[?OutputKey==`FrontendBucketName`].OutputValue' --output text)
CLOUDFRONT_DIST=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDistributionId`].OutputValue' --output text)
APP_URL=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --query 'Stacks[0].Outputs[?OutputKey==`ApplicationUrl`].OutputValue' --output text)

# Deploy frontend
echo -e "${YELLOW}📤 Deploying frontend to S3...${NC}"
cd artifacts
unzip -q frontend-build.zip -d frontend-build
aws s3 sync frontend-build/ s3://$FRONTEND_BUCKET/ --region $REGION --delete --quiet
rm -rf frontend-build

# Invalidate CloudFront
echo -e "${YELLOW}🔄 Invalidating CloudFront cache...${NC}"
aws cloudfront create-invalidation --distribution-id $CLOUDFRONT_DIST --paths "/*" --region $REGION > /dev/null

echo ""
echo -e "${GREEN}"
cat << "EOF"
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                    ✨ DEPLOYMENT SUCCESSFUL! ✨                              ║
║                                                                              ║
║              🎉 BankIQ+ is now live and ready to use! 🎉                    ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"
echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║${NC}                        ${WHITE}ACCESS YOUR APPLICATION${NC}                       ${CYAN}║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${GREEN}🌐 Application URL:${NC}"
echo -e "     ${WHITE}$APP_URL${NC}"
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}                         ${WHITE}STACK OUTPUTS${NC}                                ${BLUE}║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' --output table
echo ""
echo -e "${YELLOW}╔════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║${NC}  ℹ️  CloudFront may take 5-10 minutes to fully propagate              ${YELLOW}║${NC}"
echo -e "${YELLOW}║${NC}  🗑️  Staging bucket: ${WHITE}$STAGING_BUCKET${NC}${YELLOW}                              ║${NC}"
echo -e "${YELLOW}║${NC}     (can be deleted after deployment)                                 ${YELLOW}║${NC}"
echo -e "${YELLOW}╚════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
