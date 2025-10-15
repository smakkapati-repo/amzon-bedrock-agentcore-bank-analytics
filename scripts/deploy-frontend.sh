#!/bin/bash

set -e

echo "🚀 BankIQ+ Frontend Deployment to S3 + CloudFront"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Get your IP address
echo "📍 Getting your IP address..."
YOUR_IP=$(curl -s https://checkip.amazonaws.com)
if [ -z "$YOUR_IP" ]; then
    echo -e "${RED}❌ Failed to get your IP address${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Your IP: ${YOUR_IP}${NC}"
echo ""

# Stack name
STACK_NAME="bankiq-frontend"

# Check if stack exists
echo "🔍 Checking if stack exists..."
if aws cloudformation describe-stacks --stack-name $STACK_NAME --region us-east-1 >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Stack already exists. Updating...${NC}"
    ACTION="update-stack"
else
    echo -e "${GREEN}✅ Creating new stack...${NC}"
    ACTION="create-stack"
fi
echo ""

# Deploy CloudFormation
echo "☁️  Deploying CloudFormation stack..."
aws cloudformation $ACTION \
    --stack-name $STACK_NAME \
    --template-body file://deployment/frontend-s3-cloudfront.yaml \
    --parameters ParameterKey=YourIPAddress,ParameterValue="${YOUR_IP}/32" \
    --region us-east-1 \
    --capabilities CAPABILITY_IAM

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ CloudFormation deployment failed${NC}"
    exit 1
fi

echo ""
echo "⏳ Waiting for stack to complete..."
if [ "$ACTION" = "create-stack" ]; then
    aws cloudformation wait stack-create-complete \
        --stack-name $STACK_NAME \
        --region us-east-1
else
    aws cloudformation wait stack-update-complete \
        --stack-name $STACK_NAME \
        --region us-east-1
fi

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Stack deployment failed${NC}"
    echo "Check AWS Console for details"
    exit 1
fi

echo -e "${GREEN}✅ CloudFormation stack deployed${NC}"
echo ""

# Get outputs
echo "📋 Getting stack outputs..."
BUCKET_NAME=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region us-east-1 \
    --query 'Stacks[0].Outputs[?OutputKey==`BucketName`].OutputValue' \
    --output text)

CLOUDFRONT_URL=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region us-east-1 \
    --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontURL`].OutputValue' \
    --output text)

DISTRIBUTION_ID=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region us-east-1 \
    --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDistributionId`].OutputValue' \
    --output text)

echo -e "${GREEN}✅ Bucket: ${BUCKET_NAME}${NC}"
echo -e "${GREEN}✅ CloudFront: ${CLOUDFRONT_URL}${NC}"
echo -e "${GREEN}✅ Distribution ID: ${DISTRIBUTION_ID}${NC}"
echo ""

# Build React app
echo "🔨 Building React app..."
cd frontend

# Update API URL in build
echo "REACT_APP_API_GATEWAY_URL=http://localhost:3001" > .env.production

npm run build

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Build failed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Build complete${NC}"
echo ""

# Upload to S3
echo "📤 Uploading to S3..."
aws s3 sync build/ s3://${BUCKET_NAME}/ --delete --region us-east-1

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Upload failed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Upload complete${NC}"
echo ""

# Invalidate CloudFront cache
echo "🔄 Invalidating CloudFront cache..."
aws cloudfront create-invalidation \
    --distribution-id ${DISTRIBUTION_ID} \
    --paths "/*" \
    --region us-east-1 >/dev/null

echo -e "${GREEN}✅ Cache invalidated${NC}"
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ Frontend Deployment Complete!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌐 Website URL: https://${CLOUDFRONT_URL}"
echo "🔒 Access restricted to: ${YOUR_IP}"
echo ""
echo "📝 Next steps:"
echo "   1. Open https://${CLOUDFRONT_URL} in your browser"
echo "   2. Make sure backend is running: cd backend && npm start"
echo "   3. Update frontend API URL if needed"
echo ""
echo "🔄 To update frontend:"
echo "   cd frontend && npm run build"
echo "   aws s3 sync build/ s3://${BUCKET_NAME}/ --delete"
echo "   aws cloudfront create-invalidation --distribution-id ${DISTRIBUTION_ID} --paths '/*'"
echo ""
