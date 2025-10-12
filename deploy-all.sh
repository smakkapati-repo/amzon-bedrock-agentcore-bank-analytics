#!/bin/bash

# BankIQ+ Fully Automated Deployment Script
set -e

# Simple Banner
echo -e "${GREEN}"
echo "  ██████╗  █████╗ ███╗   ██╗██╗  ██╗██╗ ██████╗ "
echo "  ██╔══██╗██╔══██╗████╗  ██║██║ ██╔╝██║██╔═══██╗"
echo "  ██████╔╝███████║██╔██╗ ██║█████╔╝ ██║██║   ██║"
echo "  ██╔══██╗██╔══██║██║╚██╗██║██╔═██╗ ██║██║▄▄ ██║"
echo "  ██████╔╝██║  ██║██║ ╚████║██║  ██╗██║╚██████╔╝"
echo "  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝ ╚══▀▀═╝"
echo -e "${NC}"
echo -e "${YELLOW}        Advanced Banking Analytics Platform${NC}"
echo -e "${GREEN}        Powered by AWS Bedrock & AgentCore${NC}"
echo ""
echo -e "${GREEN}🚀 FULLY AUTOMATED DEPLOYMENT STARTING...${NC}"
echo "══════════════════════════════════════════════════════════════════════════════════"
echo -e "${YELLOW}📋 Deployment will complete in 5 stages (~15-20 minutes)${NC}"
echo "   🔍 Stage 1: Prerequisites Check (30s)"
echo "   🤖 Stage 2: AgentCore Agent Deploy (2-3 min)"
echo "   🐳 Stage 3: Docker Build & Push (3-5 min)"
echo "   🏗️  Stage 4: Infrastructure Deploy (10-15 min)"
echo "   🌐 Stage 5: Verification & Testing (2-3 min)"
echo "══════════════════════════════════════════════════════════════════════════════════"
echo ""

# Configuration
AWS_REGION="us-east-1"
STACK_NAME="banking-analytics"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Stage 1: Prerequisites
echo -e "${YELLOW}📋 STAGE 1/5: Prerequisites Check${NC}"
echo "══════════════════════════════════════════════════════════════════════════════════"
echo "🔍 Detecting operating system and checking prerequisites..."

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macOS"
    echo -e "${GREEN}✅ Operating System: macOS${NC}"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="Linux"
    echo -e "${GREEN}✅ Operating System: Linux${NC}"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    OS="Windows"
    echo -e "${YELLOW}⚠️  Operating System: Windows (WSL/Git Bash detected)${NC}"
else
    OS="Unknown"
    echo -e "${RED}❌ Operating System: Unknown ($OSTYPE)${NC}"
    echo "   Supported: macOS, Linux, Windows (WSL/Git Bash)"
    exit 1
fi

# Track missing prerequisites
MISSING_PREREQS=()

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found${NC}"
    MISSING_PREREQS+=("AWS CLI")
else
    echo -e "${GREEN}✅ AWS CLI installed${NC}"
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found${NC}"
    MISSING_PREREQS+=("Docker")
else
    echo -e "${GREEN}✅ Docker installed${NC}"
fi

# Check if Docker daemon is running
echo "🔍 Checking Docker daemon status..."
if ! timeout 5 docker info &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker is installed but not running.${NC}"
    echo ""
    echo -e "${YELLOW}📋 Please start Docker manually:${NC}"
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        echo "   1. Open Docker Desktop from Applications folder"
        echo "   2. Wait for Docker to fully start (green whale icon in menu bar)"
        echo "   3. Verify with: docker info"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        echo "   1. Start Docker: sudo systemctl start docker"
        echo "   2. Verify with: docker info"
    else
        # Windows or other
        echo "   1. Start Docker Desktop"
        echo "   2. Wait for Docker to fully start"
        echo "   3. Verify with: docker info"
    fi
    
    echo ""
    read -p "Press Enter after starting Docker to continue deployment..."
    
    # Verify Docker is now running
    if ! docker info &> /dev/null; then
        echo -e "${RED}❌ Docker is still not running. Please start Docker and try again.${NC}"
        exit 1
    fi
fi

# Check Docker platform architecture (now that Docker is confirmed running)
echo -e "${GREEN}✅ Docker is running${NC}"

DOCKER_ARCH=$(docker version --format '{{.Server.Arch}}' 2>/dev/null || echo "unknown")
HOST_ARCH=$(uname -m)

echo "🔍 Checking Docker platform compatibility..."
echo "   Host Architecture: $HOST_ARCH"
echo "   Docker Architecture: $DOCKER_ARCH"

# Check if we can build x86_64 images
if docker buildx version &>/dev/null; then
    echo -e "${GREEN}✅ Docker Buildx available (multi-platform support)${NC}"
    # Test x86_64 platform support
    if docker buildx inspect --bootstrap 2>/dev/null | grep -q "linux/amd64"; then
        echo -e "${GREEN}✅ x86_64/amd64 platform support confirmed${NC}"
    else
        echo -e "${RED}❌ x86_64/amd64 platform not available${NC}"
        MISSING_PREREQS+=("Docker Platform")
    fi
elif [[ "$HOST_ARCH" == "x86_64" || "$HOST_ARCH" == "amd64" ]]; then
    echo -e "${GREEN}✅ Native x86_64 architecture (ECS Fargate compatible)${NC}"
else
    echo -e "${RED}❌ Non-x86_64 architecture detected${NC}"
    echo "   ECS Fargate requires x86_64/amd64 images"
    MISSING_PREREQS+=("Docker Platform")
fi

# Check AWS credentials (only if AWS CLI exists)
if command -v aws &> /dev/null; then
    if ! aws sts get-caller-identity &> /dev/null; then
        echo -e "${RED}❌ AWS credentials not configured${NC}"
        MISSING_PREREQS+=("AWS Credentials")
    else
        echo -e "${GREEN}✅ AWS credentials configured${NC}"
        
        # Check AWS service limits
        echo "🔍 Checking AWS service limits..."
        
        # Check VPC limit
        VPC_COUNT=$(aws ec2 describe-vpcs --region ${AWS_REGION} --query 'length(Vpcs)' --output text 2>/dev/null || echo "0")
        VPC_LIMIT=5  # Default AWS limit
        if [ "$VPC_COUNT" -ge "$VPC_LIMIT" ]; then
            echo -e "${RED}❌ VPC limit reached ($VPC_COUNT/$VPC_LIMIT)${NC}"
            MISSING_PREREQS+=("VPC Limit")
        else
            echo -e "${GREEN}✅ VPC availability ($VPC_COUNT/$VPC_LIMIT)${NC}"
        fi
        
        # Check Internet Gateway limit
        IGW_COUNT=$(aws ec2 describe-internet-gateways --region ${AWS_REGION} --query 'length(InternetGateways)' --output text 2>/dev/null || echo "0")
        IGW_LIMIT=5  # Default AWS limit
        if [ "$IGW_COUNT" -ge "$IGW_LIMIT" ]; then
            echo -e "${RED}❌ Internet Gateway limit reached ($IGW_COUNT/$IGW_LIMIT)${NC}"
            MISSING_PREREQS+=("IGW Limit")
        else
            echo -e "${GREEN}✅ Internet Gateway availability ($IGW_COUNT/$IGW_LIMIT)${NC}"
        fi
        
        # Check ECS Cluster limit
        ECS_COUNT=$(aws ecs list-clusters --region ${AWS_REGION} --query 'length(clusterArns)' --output text 2>/dev/null || echo "0")
        ECS_LIMIT=10  # Default AWS limit
        if [ "$ECS_COUNT" -ge "$ECS_LIMIT" ]; then
            echo -e "${RED}❌ ECS Cluster limit reached ($ECS_COUNT/$ECS_LIMIT)${NC}"
            MISSING_PREREQS+=("ECS Limit")
        else
            echo -e "${GREEN}✅ ECS Cluster availability ($ECS_COUNT/$ECS_LIMIT)${NC}"
        fi
        
        # Check if stack already exists
        if aws cloudformation describe-stacks --stack-name ${STACK_NAME} --region ${AWS_REGION} &>/dev/null; then
            echo -e "${RED}❌ CloudFormation stack '${STACK_NAME}' already exists${NC}"
            MISSING_PREREQS+=("Stack Exists")
        else
            echo -e "${GREEN}✅ CloudFormation stack name available${NC}"
        fi
    fi
fi

# Check if any prerequisites are missing
if [ ${#MISSING_PREREQS[@]} -gt 0 ]; then
    echo ""
    echo -e "${RED}❌ DEPLOYMENT ABORTED - Missing Prerequisites:${NC}"
    echo "══════════════════════════════════════════════════════════════════════════════════"
    
    for prereq in "${MISSING_PREREQS[@]}"; do
        case $prereq in
            "AWS CLI")
                echo -e "${RED}📋 AWS CLI:${NC}"
                if [[ "$OS" == "macOS" ]]; then
                    echo "   Install: brew install awscli"
                    echo "   Or: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
                elif [[ "$OS" == "Linux" ]]; then
                    echo "   Install: curl 'https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip' -o 'awscliv2.zip' && unzip awscliv2.zip && sudo ./aws/install"
                elif [[ "$OS" == "Windows" ]]; then
                    echo "   Install: Download from https://aws.amazon.com/cli/"
                fi
                ;;
            "Docker")
                echo -e "${RED}🐳 Docker:${NC}"
                if [[ "$OS" == "macOS" ]]; then
                    echo "   Install: Download Docker Desktop from https://docker.com/products/docker-desktop"
                elif [[ "$OS" == "Linux" ]]; then
                    echo "   Install: curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh"
                elif [[ "$OS" == "Windows" ]]; then
                    echo "   Install: Download Docker Desktop from https://docker.com/products/docker-desktop"
                fi
                ;;
            "AWS Credentials")
                echo -e "${RED}🔑 AWS Credentials:${NC}"
                echo "   Configure: aws configure"
                echo "   You'll need: Access Key ID, Secret Access Key, Region (us-east-1)"
                ;;
            "VPC Limit")
                echo -e "${RED}🌐 VPC Limit Exceeded:${NC}"
                echo "   Delete unused VPCs: aws ec2 describe-vpcs --query 'Vpcs[?State==\`available\`]'"
                echo "   Or request limit increase in AWS Support Center"
                ;;
            "IGW Limit")
                echo -e "${RED}🌐 Internet Gateway Limit Exceeded:${NC}"
                echo "   Delete unused IGWs: aws ec2 describe-internet-gateways --query 'InternetGateways[?length(Attachments)==\`0\`]'"
                echo "   Or request limit increase in AWS Support Center"
                ;;
            "ECS Limit")
                echo -e "${RED}📦 ECS Cluster Limit Exceeded:${NC}"
                echo "   Delete unused clusters: aws ecs list-clusters"
                echo "   Or request limit increase in AWS Support Center"
                ;;
            "Stack Exists")
                echo -e "${RED}🏗️  CloudFormation Stack Already Exists:${NC}"
                echo "   Delete existing: aws cloudformation delete-stack --stack-name ${STACK_NAME}"
                echo "   Or use different stack name by editing STACK_NAME in script"
                ;;
            "Docker Platform")
                echo -e "${RED}🐳 Docker Platform Incompatibility:${NC}"
                echo "   ECS Fargate requires x86_64/amd64 architecture"
                if [[ "$OS" == "macOS" ]]; then
                    echo "   Apple Silicon (M1/M2): Docker Desktop should handle this automatically"
                    echo "   Try: docker buildx create --use --platform linux/amd64"
                elif [[ "$OS" == "Linux" ]]; then
                    echo "   Install buildx: docker buildx install"
                    echo "   Enable multi-platform: docker run --privileged --rm tonistiigi/binfmt --install all"
                fi
                echo "   Verify: docker buildx ls"
                ;;
        esac
        echo ""
    done
    
    echo -e "${YELLOW}📋 After installing missing prerequisites, run: ./deploy-all.sh${NC}"
    echo "══════════════════════════════════════════════════════════════════════════════════"
    exit 1
fi

# Get AWS Account ID and IP (only if all prerequisites are met)
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✅ AWS Account: ${AWS_ACCOUNT_ID}${NC}"

# Get current IP
YOUR_IP=$(curl -s https://checkip.amazonaws.com)
echo -e "${GREEN}✅ Your IP: ${YOUR_IP}${NC}"
echo -e "${GREEN}✅ Stage 1 Complete - All prerequisites satisfied!${NC}"
echo ""

# Check Bedrock model access
echo "🔍 Checking Bedrock model access..."
if aws bedrock list-foundation-models --region ${AWS_REGION} --query 'modelSummaries[?contains(modelId, `claude-3-5-sonnet`) || contains(modelId, `claude-3-haiku`) || contains(modelId, `titan-embed`)].modelId' --output text | grep -q claude; then
    echo -e "${GREEN}✅ Bedrock models accessible${NC}"
else
    echo -e "${YELLOW}⚠️  Bedrock model access may not be enabled. Please enable Claude and Titan models in Bedrock console.${NC}"
    echo "   Go to: https://console.aws.amazon.com/bedrock/ → Model Access"
    read -p "Press Enter after enabling Bedrock models to continue..."
fi

# Stage 2: AgentCore Agent
echo -e "${YELLOW}🤖 STAGE 2/5: AgentCore Agent Deployment${NC}"
echo "══════════════════════════════════════════════════════════════════════════════════"
echo "📦 Uploading banking_strands_agent.py with 5 custom tools..."
echo "🧠 Creating runtime with Claude Sonnet 4.0..."
echo "⏳ This may take 2-3 minutes..."
cd backend
# Try AgentCore deployment with background process and timeout
echo "Attempting AgentCore deployment (max 5 minutes)..."
python3 deploy_agent.py > agent_deploy.log 2>&1 &
DEPLOY_PID=$!

# Wait for deployment with timeout
for i in {1..300}; do
    if ! kill -0 $DEPLOY_PID 2>/dev/null; then
        # Process finished
        wait $DEPLOY_PID
        if [ $? -eq 0 ]; then
            AGENT_OUTPUT=$(cat agent_deploy.log)
            echo "$AGENT_OUTPUT"
            break
        else
            echo -e "${RED}❌ AgentCore deployment failed${NC}"
            cat agent_deploy.log
            exit 1
        fi
    fi
    
    if [ $i -eq 300 ]; then
        # Timeout reached
        kill $DEPLOY_PID 2>/dev/null
        echo -e "${RED}❌ AgentCore deployment timed out after 5 minutes${NC}"
        echo "Last output:"
        tail -10 agent_deploy.log
        exit 1
    fi
    
    sleep 1
done
echo "$AGENT_OUTPUT"

# Extract Agent ARN from output
AGENT_ARN=$(echo "$AGENT_OUTPUT" | grep -o 'arn:aws:bedrock-agentcore:[^"]*' | head -1)
if [ -z "$AGENT_ARN" ]; then
    echo -e "${RED}❌ Failed to extract Agent ARN from deployment output${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Agent ARN: ${AGENT_ARN}${NC}"
echo -e "${GREEN}✅ Stage 2 Complete - AgentCore agent deployed successfully!${NC}"
echo ""
cd ..

# Stage 3: Docker Build & Push
echo -e "${YELLOW}🐳 STAGE 3/5: Docker Build & Push${NC}"
echo "══════════════════════════════════════════════════════════════════════════════════"
echo "🏗️  Building Docker image with agentcore_web_server.py..."
echo "📤 Pushing to ECR repository..."
echo "⏳ This may take 3-5 minutes..."
./deploy.sh

echo -e "${GREEN}✅ Stage 3 Complete - Docker image built and pushed!${NC}"
echo ""

# Stage 4: Infrastructure Deploy
echo -e "${YELLOW}🏗️  STAGE 4/5: Infrastructure Deployment${NC}"
echo "══════════════════════════════════════════════════════════════════════════════════"
echo "☁️  Creating CloudFormation stack: ${STACK_NAME}..."
echo "🏢 Deploying VPC, ECS Fargate, ALB, S3 bucket..."
echo "🔐 Configuring security groups for IP: ${YOUR_IP}..."
echo "⏳ This is the longest stage (10-15 minutes)..."
aws cloudformation create-stack \
  --stack-name ${STACK_NAME} \
  --template-body file://cloudformation-template.yaml \
  --parameters \
    ParameterKey=YourIPAddress,ParameterValue=${YOUR_IP} \
    ParameterKey=AgentCoreAgentARN,ParameterValue="${AGENT_ARN}" \
  --capabilities CAPABILITY_IAM

echo -e "${YELLOW}⏳ Monitoring CloudFormation deployment progress...${NC}"
echo "   💡 Tip: You can monitor in AWS Console → CloudFormation → ${STACK_NAME}"

# Wait for stack creation
aws cloudformation wait stack-create-complete --stack-name ${STACK_NAME}

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ CloudFormation stack deployed successfully!${NC}"
    echo -e "${GREEN}✅ Stage 4 Complete - Infrastructure ready!${NC}"
    echo ""
else
    echo -e "${RED}❌ Stack creation failed. Check CloudFormation console for details.${NC}"
    echo "   🔍 Debug: aws cloudformation describe-stack-events --stack-name ${STACK_NAME}"
    exit 1
fi

# Stage 5: Verification
echo -e "${YELLOW}🌐 STAGE 5/5: Verification & Testing${NC}"
echo "══════════════════════════════════════════════════════════════════════════════════"
echo "📍 Extracting application URLs from CloudFormation..."
APP_URL=$(aws cloudformation describe-stacks \
  --stack-name ${STACK_NAME} \
  --query 'Stacks[0].Outputs[?OutputKey==`ApplicationURL`].OutputValue' \
  --output text)

ALB_DNS=$(aws cloudformation describe-stacks \
  --stack-name ${STACK_NAME} \
  --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerDNS`].OutputValue' \
  --output text)

S3_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name ${STACK_NAME} \
  --query 'Stacks[0].Outputs[?OutputKey==`DocumentBucket`].OutputValue' \
  --output text)

# Wait for service to be healthy
echo -e "${YELLOW}⏳ Waiting for ECS service to start (2-3 minutes)...${NC}"
echo "   🚀 Starting Fargate containers..."
echo "   📥 Pulling Docker image from ECR..."
echo "   🔄 Initializing AgentCore runtime..."

# Progress indicator
for i in {1..24}; do
    echo -n "."
    sleep 5
done
echo ""

# Test health endpoint
echo "🔍 Testing application health endpoint..."
for i in {1..10}; do
    if curl -s -f "http://${ALB_DNS}/health" > /dev/null; then
        echo -e "${GREEN}✅ Health check passed - Application is ready!${NC}"
        break
    else
        echo "   🔄 Health check $i/10 - waiting for application startup..."
        sleep 30
    fi
done

echo -e "${GREEN}✅ Stage 5 Complete - Deployment verification successful!${NC}"

# Final output
echo ""
echo "══════════════════════════════════════════════════════════════════════════════════"
echo -e "${GREEN}"
echo "██████╗ ███████╗██████╗ ██╗      ██████╗ ██╗   ██╗███████╗██████╗ "
echo "██╔══██╗██╔════╝██╔══██╗██║     ██╔═══██╗╚██╗ ██╔╝██╔════╝██╔══██╗"
echo "██║  ██║█████╗  ██████╔╝██║     ██║   ██║ ╚████╔╝ █████╗  ██║  ██║"
echo "██║  ██║██╔══╝  ██╔═══╝ ██║     ██║   ██║  ╚██╔╝  ██╔══╝  ██║  ██║"
echo "██████╔╝███████╗██║     ███████╗╚██████╔╝   ██║   ███████╗██████╔╝"
echo "╚═════╝ ╚══════╝╚═╝     ╚══════╝ ╚═════╝    ╚═╝   ╚══════╝╚═════╝ "
echo -e "${NC}"
echo -e "${YELLOW}           🎉 DEPLOYMENT COMPLETE! 🎉${NC}"
echo "══════════════════════════════════════════════════════════════════════════════════"
echo -e "${GREEN}Application URL: ${APP_URL}${NC}"
echo -e "${GREEN}Load Balancer: ${ALB_DNS}${NC}"
echo -e "${GREEN}S3 Bucket: ${S3_BUCKET}${NC}"
echo -e "${GREEN}Agent ARN: ${AGENT_ARN}${NC}"
echo ""
echo "🔐 Security: Access restricted to your IP (${YOUR_IP})"
echo "📊 Features: Peer analytics, financial reports, AI chat"
echo "🤖 AI Model: Claude Sonnet 4.0 with 5 custom banking tools"
echo ""
echo "🚀 Ready to use! Open the application URL in your browser."
echo ""
echo "📋 Useful commands:"
echo "   View logs: aws logs tail /ecs/bankiq-secure --follow"
echo "   Update app: ./deploy.sh && aws ecs update-service --cluster bankiq-secure-cluster --service bankiq-secure-service --force-new-deployment"
echo "   Delete stack: aws cloudformation delete-stack --stack-name ${STACK_NAME}"