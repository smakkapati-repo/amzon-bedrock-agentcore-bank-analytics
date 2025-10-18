#!/bin/bash
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

STACK_NAME=${1:-bankiq}
REGION=${2:-us-east-1}

echo -e "${PURPLE}"
echo "═══════════════════════════════════════════════════════════════"
echo "  🚀 BankIQ+ FULL DEPLOYMENT WITH COGNITO"
echo "═══════════════════════════════════════════════════════════════"
echo -e "${CYAN}  Stack: ${YELLOW}$STACK_NAME${NC}"
echo -e "${CYAN}  Region: ${YELLOW}$REGION${NC}"
echo -e "${CYAN}  Estimated Time: ${YELLOW}20-25 minutes${NC}"
echo -e "${PURPLE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Phase 0: Check if Auth stack exists
echo -e "${BLUE}┌─────────────────────────────────────────────────────────────┐${NC}"
echo -e "${BLUE}│${NC} ${GREEN}[0/5]${NC} ${CYAN}Checking Cognito Auth Stack...${NC}                     ${BLUE}│${NC}"
echo -e "${BLUE}└─────────────────────────────────────────────────────────────┘${NC}"

AUTH_STACK_EXISTS=$(aws cloudformation describe-stacks --stack-name ${STACK_NAME}-auth --region $REGION >/dev/null 2>&1 && echo "yes" || echo "no")

if [ "$AUTH_STACK_EXISTS" = "yes" ]; then
  echo "✅ Auth stack already exists"
else
  echo "⚠️  Auth stack not found - deploying..."
  
  # Get the script directory to reference templates correctly
  SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
  
  aws cloudformation create-stack \
    --stack-name ${STACK_NAME}-auth \
    --template-body file://${SCRIPT_DIR}/../templates/auth.yaml \
    --parameters \
      ParameterKey=ProjectName,ParameterValue=$STACK_NAME \
      ParameterKey=CallbackURL,ParameterValue=http://localhost:3000 \
      ParameterKey=Environment,ParameterValue=prod \
    --region $REGION
  
  echo "⏳ Waiting for auth stack creation..."
  aws cloudformation wait stack-create-complete --stack-name ${STACK_NAME}-auth --region $REGION
  echo "✅ Auth stack created"
fi
echo ""

# Phase 1: Agent
echo -e "${BLUE}┌─────────────────────────────────────────────────────────────┐${NC}"
echo -e "${BLUE}│${NC} ${GREEN}[1/5]${NC} ${CYAN}Deploying AgentCore Agent...${NC}                        ${BLUE}│${NC}"
echo -e "${BLUE}└─────────────────────────────────────────────────────────────┘${NC}"
./phase1-agent.sh
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Phase 1 failed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Phase 1 Complete!${NC}\n"

# Phase 2: Infrastructure
echo -e "${BLUE}┌─────────────────────────────────────────────────────────────┐${NC}"
echo -e "${BLUE}│${NC} ${GREEN}[2/5]${NC} ${CYAN}Deploying Infrastructure (VPC, ALB, ECS)...${NC}         ${BLUE}│${NC}"
echo -e "${BLUE}└─────────────────────────────────────────────────────────────┘${NC}"

INFRA_EXISTS=$(aws cloudformation describe-stacks --stack-name ${STACK_NAME}-infra --region $REGION >/dev/null 2>&1 && echo "yes" || echo "no")
if [ "$INFRA_EXISTS" = "yes" ]; then
  echo "✅ Infrastructure stack already exists - skipping"
else
  ./phase2-infrastructure.sh $STACK_NAME $REGION
  if [ $? -ne 0 ]; then
      echo -e "${RED}❌ Phase 2 failed${NC}"
      exit 1
  fi
fi
echo -e "${GREEN}✅ Phase 2 Complete!${NC}\n"

# Phase 3: Backend
echo -e "${BLUE}┌─────────────────────────────────────────────────────────────┐${NC}"
echo -e "${BLUE}│${NC} ${GREEN}[3/5]${NC} ${CYAN}Building & Deploying Backend Container...${NC}           ${BLUE}│${NC}"
echo -e "${BLUE}└─────────────────────────────────────────────────────────────┘${NC}"
./phase3-backend.sh $STACK_NAME $REGION
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Phase 3 failed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Phase 3 Complete!${NC}\n"

# Phase 4: Frontend
echo -e "${BLUE}┌─────────────────────────────────────────────────────────────┐${NC}"
echo -e "${BLUE}│${NC} ${GREEN}[4/5]${NC} ${CYAN}Building & Deploying Frontend (React + S3)...${NC}       ${BLUE}│${NC}"
echo -e "${BLUE}└─────────────────────────────────────────────────────────────┘${NC}"
./phase4-frontend.sh $STACK_NAME $REGION
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Phase 4 failed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Phase 4 Complete!${NC}\n"

# Phase 5: Update Cognito Callback URLs
echo -e "${BLUE}┌─────────────────────────────────────────────────────────────┐${NC}"
echo -e "${BLUE}│${NC} ${GREEN}[5/5]${NC} ${CYAN}Updating Cognito Callback URLs...${NC}                   ${BLUE}│${NC}"
echo -e "${BLUE}└─────────────────────────────────────────────────────────────┘${NC}"

CLOUDFRONT_URL=$(aws cloudformation describe-stacks --stack-name ${STACK_NAME}-frontend --region $REGION --query 'Stacks[0].Outputs[?OutputKey==`ApplicationUrl`].OutputValue' --output text)

if [ -n "$CLOUDFRONT_URL" ]; then
  echo "Updating Cognito callback URLs with: $CLOUDFRONT_URL"
  
  aws cloudformation update-stack \
    --stack-name ${STACK_NAME}-auth \
    --template-body file://../templates/auth.yaml \
    --parameters \
      ParameterKey=ProjectName,ParameterValue=$STACK_NAME \
      ParameterKey=CallbackURL,ParameterValue=$CLOUDFRONT_URL \
      ParameterKey=Environment,ParameterValue=prod \
    --region $REGION
  
  echo "⏳ Waiting for auth stack update..."
  aws cloudformation wait stack-update-complete --stack-name ${STACK_NAME}-auth --region $REGION 2>/dev/null || echo "⚠️  Update may have had no changes"
  echo "✅ Cognito callback URLs updated"
else
  echo "⚠️  Could not get CloudFront URL - skipping callback URL update"
fi
echo ""

echo -e "${GREEN}"
echo "═══════════════════════════════════════════════════════════════"
echo "  ✅ DEPLOYMENT COMPLETE WITH COGNITO!"
echo "═══════════════════════════════════════════════════════════════"
echo -e "${NC}"
echo -e "${CYAN}🌐 Application URL: ${YELLOW}$CLOUDFRONT_URL${NC}"
echo -e "${CYAN}🔐 Login URL: ${YELLOW}https://bankiq-auth-164543933824.auth.us-east-1.amazoncognito.com${NC}"
echo -e "${CYAN}📊 View logs: ${YELLOW}aws logs tail /ecs/bankiq-backend --follow${NC}"
echo -e "${CYAN}🔍 Monitor: ${YELLOW}agentcore status${NC}"
echo ""
echo -e "${YELLOW}📝 Next Steps:${NC}"
echo "  1. Visit: $CLOUDFRONT_URL"
echo "  2. Click 'Sign In with AWS Cognito'"
echo "  3. Click 'Sign up' to create your account"
echo "  4. Verify your email and log in"
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
