#!/bin/bash
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

STACK_NAME=${1:-bankiq}
REGION=${2:-us-east-1}

echo -e "${PURPLE}"
echo "═══════════════════════════════════════════════════════════════"
echo "  🚀 BankIQ+ FULL DEPLOYMENT"
echo "═══════════════════════════════════════════════════════════════"
echo -e "${CYAN}  Stack: ${YELLOW}$STACK_NAME${NC}"
echo -e "${CYAN}  Region: ${YELLOW}$REGION${NC}"
echo -e "${CYAN}  Estimated Time: ${YELLOW}15-20 minutes${NC}"
echo -e "${PURPLE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Phase 1: Agent
echo -e "${BLUE}┌─────────────────────────────────────────────────────────────┐${NC}"
echo -e "${BLUE}│${NC} ${GREEN}[1/4]${NC} ${CYAN}Deploying AgentCore Agent...${NC}                        ${BLUE}│${NC}"
echo -e "${BLUE}└─────────────────────────────────────────────────────────────┘${NC}"
bash phase1-agent.sh
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Phase 1 failed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Phase 1 Complete!${NC}\n"

# Phase 2: Infrastructure
echo -e "${BLUE}┌─────────────────────────────────────────────────────────────┐${NC}"
echo -e "${BLUE}│${NC} ${GREEN}[2/4]${NC} ${CYAN}Deploying Infrastructure (VPC, ALB, ECS)...${NC}         ${BLUE}│${NC}"
echo -e "${BLUE}└─────────────────────────────────────────────────────────────┘${NC}"
bash phase2-infrastructure.sh $STACK_NAME $REGION
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Phase 2 failed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Phase 2 Complete!${NC}\n"

# Phase 3: Backend
echo -e "${BLUE}┌─────────────────────────────────────────────────────────────┐${NC}"
echo -e "${BLUE}│${NC} ${GREEN}[3/4]${NC} ${CYAN}Building & Deploying Backend Container...${NC}           ${BLUE}│${NC}"
echo -e "${BLUE}└─────────────────────────────────────────────────────────────┘${NC}"
bash phase3-backend.sh $STACK_NAME $REGION
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Phase 3 failed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Phase 3 Complete!${NC}\n"

# Phase 4: Frontend
echo -e "${BLUE}┌─────────────────────────────────────────────────────────────┐${NC}"
echo -e "${BLUE}│${NC} ${GREEN}[4/4]${NC} ${CYAN}Building & Deploying Frontend (React + S3)...${NC}       ${BLUE}│${NC}"
echo -e "${BLUE}└─────────────────────────────────────────────────────────────┘${NC}"
bash phase4-frontend.sh $STACK_NAME $REGION
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Phase 4 failed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Phase 4 Complete!${NC}\n"

echo -e "${GREEN}"
echo "═══════════════════════════════════════════════════════════════"
echo "  ✅ DEPLOYMENT COMPLETE!"
echo "═══════════════════════════════════════════════════════════════"
echo -e "${NC}"
echo -e "${CYAN}🌐 Access your application at the CloudFront URL above${NC}"
echo -e "${CYAN}📊 View logs: ${YELLOW}aws logs tail /ecs/bankiq-backend --follow${NC}"
echo -e "${CYAN}🔍 Monitor: ${YELLOW}agentcore status${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
