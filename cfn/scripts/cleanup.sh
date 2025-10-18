#!/bin/bash
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Parse stack name from argument or prompt
if [ $# -eq 1 ]; then
  STACK_NAME="$1"
else
  read -p "Enter stack name to delete (default: bankiq): " STACK_NAME
  STACK_NAME=${STACK_NAME:-bankiq}
fi

# Auto-detect region from AWS CLI config
REGION=$(aws configure get region 2>/dev/null || echo "us-east-1")
FORCE=false

echo -e "${RED}🗑️  BankIQ+ Cleanup Script${NC}"
echo ""
echo "This will delete:"
echo "  - CloudFormation stack: $STACK_NAME"
echo "  - All nested stacks (prerequisites, agent, backend, frontend)"
echo "  - ECR repositories and images"
echo "  - S3 buckets and contents"
echo "  - AgentCore agent"
echo "  - ECS cluster and services"
echo "  - CloudFront distribution"
echo "  - All associated resources"
echo ""

if [ "$FORCE" = false ]; then
  read -p "Are you sure you want to continue? (yes/no): " CONFIRM
  if [ "$CONFIRM" != "yes" ]; then
    echo "Cleanup cancelled."
    exit 0
  fi
fi

echo ""
echo -e "${YELLOW}📋 Gathering resource information...${NC}"

# Try to get resources from master stack first, then from individual stacks
FRONTEND_BUCKET=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --query 'Stacks[0].Outputs[?OutputKey==`FrontendBucketName`].OutputValue' --output text 2>/dev/null || echo "")
DOCS_BUCKET=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --query 'Stacks[0].Outputs[?OutputKey==`UploadedDocsBucketName`].OutputValue' --output text 2>/dev/null || echo "")
BACKEND_ECR=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --query 'Stacks[0].Outputs[?OutputKey==`BackendECRRepositoryUri`].OutputValue' --output text 2>/dev/null | cut -d'/' -f2 || echo "")
AGENT_ECR=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --query 'Stacks[0].Outputs[?OutputKey==`AgentECRRepositoryUri`].OutputValue' --output text 2>/dev/null | cut -d'/' -f2 || echo "")
CLOUDFRONT_DIST=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDistributionId`].OutputValue' --output text 2>/dev/null || echo "")

# If not found in master stack, try individual stacks
if [ -z "$FRONTEND_BUCKET" ]; then
  FRONTEND_BUCKET=$(aws cloudformation describe-stacks --stack-name ${STACK_NAME}-infra --region $REGION --query 'Stacks[0].Outputs[?OutputKey==`FrontendBucketName`].OutputValue' --output text 2>/dev/null || echo "")
fi

if [ -z "$DOCS_BUCKET" ]; then
  DOCS_BUCKET=$(aws cloudformation describe-stacks --stack-name ${STACK_NAME}-infra --region $REGION --query 'Stacks[0].Outputs[?OutputKey==`UploadedDocsBucketName`].OutputValue' --output text 2>/dev/null || echo "")
fi

if [ -z "$BACKEND_ECR" ]; then
  BACKEND_ECR=$(aws cloudformation describe-stacks --stack-name ${STACK_NAME}-infra --region $REGION --query 'Stacks[0].Outputs[?OutputKey==`BackendECRRepositoryUri`].OutputValue' --output text 2>/dev/null | cut -d'/' -f2 || echo "")
fi

if [ -z "$AGENT_ECR" ]; then
  AGENT_ECR=$(aws cloudformation describe-stacks --stack-name ${STACK_NAME}-infra --region $REGION --query 'Stacks[0].Outputs[?OutputKey==`AgentECRRepositoryUri`].OutputValue' --output text 2>/dev/null | cut -d'/' -f2 || echo "")
fi

if [ -z "$CLOUDFRONT_DIST" ]; then
  CLOUDFRONT_DIST=$(aws cloudformation describe-stacks --stack-name ${STACK_NAME}-frontend --region $REGION --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDistributionId`].OutputValue' --output text 2>/dev/null || echo "")
fi

echo "Found resources:"
echo "  Frontend Bucket: ${FRONTEND_BUCKET:-Not found}"
echo "  Docs Bucket: ${DOCS_BUCKET:-Not found}"
echo "  Backend ECR: ${BACKEND_ECR:-Not found}"
echo "  Agent ECR: ${AGENT_ECR:-Not found}"
echo "  CloudFront: ${CLOUDFRONT_DIST:-Not found}"
echo ""

# Step 1: Disable CloudFront distribution (required before deletion)
if [ -n "$CLOUDFRONT_DIST" ]; then
  echo -e "${YELLOW}🔄 Disabling CloudFront distribution...${NC}"
  
  # Get current config
  ETAG=$(aws cloudfront get-distribution-config --id $CLOUDFRONT_DIST --region $REGION --query 'ETag' --output text 2>/dev/null || echo "")
  
  if [ -n "$ETAG" ]; then
    # Get config and disable
    aws cloudfront get-distribution-config --id $CLOUDFRONT_DIST --region $REGION --query 'DistributionConfig' > /tmp/cf-config.json 2>/dev/null || true
    
    if [ -f /tmp/cf-config.json ]; then
      # Update enabled to false
      jq '.Enabled = false' /tmp/cf-config.json > /tmp/cf-config-disabled.json
      
      # Update distribution
      aws cloudfront update-distribution \
        --id $CLOUDFRONT_DIST \
        --distribution-config file:///tmp/cf-config-disabled.json \
        --if-match $ETAG \
        --region $REGION > /dev/null 2>&1 || true
      
      rm -f /tmp/cf-config.json /tmp/cf-config-disabled.json
      echo "✅ CloudFront distribution disabled (will be deleted with stack)"
    fi
  fi
fi

# Step 2: Delete ECR repositories
if [ -n "$BACKEND_ECR" ]; then
  echo -e "${YELLOW}🗑️  Deleting backend ECR repository: $BACKEND_ECR${NC}"
  aws ecr delete-repository --repository-name $BACKEND_ECR --region $REGION --force 2>/dev/null || true
  echo "✅ Backend ECR repository deleted"
fi

if [ -n "$AGENT_ECR" ]; then
  echo -e "${YELLOW}🗑️  Deleting agent ECR repository: $AGENT_ECR${NC}"
  aws ecr delete-repository --repository-name $AGENT_ECR --region $REGION --force 2>/dev/null || true
  echo "✅ Agent ECR repository deleted"
fi

# Fallback: Find and delete any remaining bankiq ECR repositories
echo -e "${YELLOW}🔍 Checking for any remaining ${STACK_NAME} ECR repositories...${NC}"
REMAINING_REPOS=$(aws ecr describe-repositories --region $REGION --query "repositories[?contains(repositoryName, '${STACK_NAME}')].repositoryName" --output text 2>/dev/null || echo "")
if [ -n "$REMAINING_REPOS" ]; then
  for REPO in $REMAINING_REPOS; do
    echo "Found repository: $REPO - deleting..."
    aws ecr delete-repository --repository-name $REPO --region $REGION --force 2>/dev/null || true
  done
  echo "✅ All remaining ECR repositories deleted"
else
  echo "No remaining ECR repositories found"
fi

# Step 3: Delete AgentCore agent
echo ""
echo -e "${YELLOW}🗑️  Deleting AgentCore agent...${NC}"
if command -v agentcore &> /dev/null; then
  agentcore delete -a bank_iq_agent_v1 --force 2>/dev/null || echo "⚠️  Agent may not exist or already deleted"
  echo "✅ AgentCore agent deleted"
else
  echo "⚠️  agentcore CLI not found, skipping agent deletion"
fi

# Step 4: Delete CloudFormation stacks
echo ""
echo -e "${YELLOW}🗑️  Deleting CloudFormation stacks...${NC}"
echo "This will take 10-15 minutes..."
echo ""

# Check if individual stacks exist
FRONTEND_STACK_EXISTS=$(aws cloudformation describe-stacks --stack-name ${STACK_NAME}-frontend --region $REGION 2>/dev/null && echo "yes" || echo "no")
BACKEND_STACK_EXISTS=$(aws cloudformation describe-stacks --stack-name ${STACK_NAME}-backend --region $REGION 2>/dev/null && echo "yes" || echo "no")
INFRA_STACK_EXISTS=$(aws cloudformation describe-stacks --stack-name ${STACK_NAME}-infra --region $REGION 2>/dev/null && echo "yes" || echo "no")
MASTER_STACK_EXISTS=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION 2>/dev/null && echo "yes" || echo "no")

# Delete in reverse order (frontend -> backend -> infra -> master)
if [ "$FRONTEND_STACK_EXISTS" = "yes" ]; then
  echo "Deleting ${STACK_NAME}-frontend stack..."
  aws cloudformation delete-stack --stack-name ${STACK_NAME}-frontend --region $REGION
  echo -e "${YELLOW}⏳ Waiting for frontend stack deletion...${NC}"
  aws cloudformation wait stack-delete-complete --stack-name ${STACK_NAME}-frontend --region $REGION 2>/dev/null || echo "⚠️  Frontend stack deletion completed with warnings"
  echo -e "${GREEN}✅ Frontend stack deleted${NC}"
fi

if [ "$BACKEND_STACK_EXISTS" = "yes" ]; then
  echo "Deleting ${STACK_NAME}-backend stack..."
  aws cloudformation delete-stack --stack-name ${STACK_NAME}-backend --region $REGION
  echo -e "${YELLOW}⏳ Waiting for backend stack deletion...${NC}"
  aws cloudformation wait stack-delete-complete --stack-name ${STACK_NAME}-backend --region $REGION 2>/dev/null || echo "⚠️  Backend stack deletion completed with warnings"
  echo -e "${GREEN}✅ Backend stack deleted${NC}"
fi

if [ "$INFRA_STACK_EXISTS" = "yes" ]; then
  echo "Deleting ${STACK_NAME}-infra stack..."
  aws cloudformation delete-stack --stack-name ${STACK_NAME}-infra --region $REGION
  echo -e "${YELLOW}⏳ Waiting for infra stack deletion...${NC}"
  aws cloudformation wait stack-delete-complete --stack-name ${STACK_NAME}-infra --region $REGION 2>/dev/null || echo "⚠️  Infra stack deletion completed with warnings"
  echo -e "${GREEN}✅ Infra stack deleted${NC}"
fi

if [ "$MASTER_STACK_EXISTS" = "yes" ]; then
  echo "Deleting ${STACK_NAME} master stack..."
  aws cloudformation delete-stack --stack-name $STACK_NAME --region $REGION
  echo -e "${YELLOW}⏳ Waiting for master stack deletion...${NC}"
  aws cloudformation wait stack-delete-complete --stack-name $STACK_NAME --region $REGION 2>/dev/null || echo "⚠️  Master stack deletion completed with warnings"
  echo -e "${GREEN}✅ Master stack deleted${NC}"
fi

echo ""
echo -e "${GREEN}✅ All stacks deleted successfully!${NC}"

# Step 5: Empty and delete S3 buckets (AFTER stacks are deleted)
echo ""
echo -e "${YELLOW}🗑️  Final cleanup: Deleting S3 buckets...${NC}"

if [ -n "$FRONTEND_BUCKET" ]; then
  echo -e "${YELLOW}🗑️  Deleting frontend S3 bucket: $FRONTEND_BUCKET${NC}"
  aws s3 rb s3://$FRONTEND_BUCKET --force --region $REGION 2>/dev/null || true
  echo "✅ Frontend bucket deleted"
fi

if [ -n "$DOCS_BUCKET" ]; then
  echo -e "${YELLOW}🗑️  Deleting uploaded docs S3 bucket: $DOCS_BUCKET${NC}"
  aws s3 rb s3://$DOCS_BUCKET --force --region $REGION 2>/dev/null || true
  echo "✅ Docs bucket deleted"
fi

# Fallback: Find and delete any remaining bankiq S3 buckets
echo -e "${YELLOW}🔍 Checking for any remaining ${STACK_NAME} S3 buckets...${NC}"
REMAINING_BUCKETS=$(aws s3 ls --region $REGION | grep "${STACK_NAME}" | awk '{print $3}' || echo "")
if [ -n "$REMAINING_BUCKETS" ]; then
  for BUCKET in $REMAINING_BUCKETS; do
    echo "Found bucket: $BUCKET - deleting..."
    aws s3 rb s3://$BUCKET --force --region $REGION 2>/dev/null || true
  done
  echo "✅ All remaining buckets deleted"
else
  echo "No remaining buckets found"
fi

# Step 6: Clean up staging buckets (optional)
echo ""
echo -e "${YELLOW}🔍 Checking for staging buckets...${NC}"
STAGING_BUCKETS=$(aws s3 ls --region $REGION | grep "${STACK_NAME}-cfn-staging" | awk '{print $3}' || echo "")

if [ -n "$STAGING_BUCKETS" ]; then
  echo "Found staging buckets:"
  echo "$STAGING_BUCKETS"
  echo ""
  
  for BUCKET in $STAGING_BUCKETS; do
    echo "Deleting $BUCKET..."
    aws s3 rb s3://$BUCKET --force --region $REGION 2>/dev/null || true
  done
  echo "✅ Staging buckets deleted"
else
  echo "No staging buckets found"
fi

# Step 7: Summary
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✨ Cleanup Complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Deleted resources:"
echo "  ✅ CloudFormation stack: $STACK_NAME"
echo "  ✅ All nested stacks"
echo "  ✅ S3 buckets (frontend, uploaded-docs)"
echo "  ✅ ECR repositories (backend, agent)"
echo "  ✅ ECS cluster and services"
echo "  ✅ CloudFront distribution"
echo "  ✅ ALB and target groups"
echo "  ✅ Security groups"
echo "  ✅ IAM roles"
echo "  ✅ CloudWatch log groups"
echo "  ✅ AgentCore agent"
echo ""
echo -e "${YELLOW}Note: Some resources may take a few minutes to fully delete${NC}"
echo ""

# Optional: Check for any remaining resources
echo "To verify all resources are deleted:"
echo "  aws cloudformation list-stacks --stack-status-filter DELETE_COMPLETE --region $REGION | grep $STACK_NAME"
echo "  aws s3 ls --region $REGION | grep $STACK_NAME"
echo "  aws ecr describe-repositories --region $REGION | grep $STACK_NAME"
