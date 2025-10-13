#!/bin/bash

# BankIQ+ Complete Platform Deployment Script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored banners
print_banner() {
    echo -e "${CYAN}"
    echo "═══════════════════════════════════════════════════════════════════════════════"
    echo "  $1"
    echo "═══════════════════════════════════════════════════════════════════════════════"
    echo -e "${NC}"
}

print_step() {
    echo -e "${YELLOW}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check prerequisites
check_prerequisites() {
    print_step "Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI not found. Please install AWS CLI first."
        exit 1
    fi
    print_success "AWS CLI found"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker not found. Please install Docker first."
        exit 1
    fi
    print_success "Docker found"
    
    # Check Python/pip
    if ! command -v pip &> /dev/null; then
        print_error "pip not found. Please install Python and pip first."
        exit 1
    fi
    print_success "Python/pip found"
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured. Please run 'aws configure' first."
        exit 1
    fi
    print_success "AWS credentials configured"
    
    # Check VPC quota
    print_step "Checking VPC quota availability..."
    VPC_COUNT=$(aws ec2 describe-vpcs --query 'length(Vpcs)' --output text)
    VPC_LIMIT=$(aws service-quotas get-service-quota --service-code ec2 --quota-code L-F678F1CE --query 'Quota.Value' --output text 2>/dev/null || echo "5")
    
    if [ "$VPC_COUNT" -ge "$VPC_LIMIT" ]; then
        print_error "VPC quota exceeded: $VPC_COUNT/$VPC_LIMIT VPCs in use"
        print_error "Please delete unused VPCs or request quota increase"
        print_info "Delete VPCs: aws ec2 delete-vpc --vpc-id <vpc-id>"
        exit 1
    fi
    print_success "VPC quota available: $VPC_COUNT/$VPC_LIMIT VPCs used"
    
    # Check Internet Gateway quota
    IGW_COUNT=$(aws ec2 describe-internet-gateways --query 'length(InternetGateways)' --output text)
    IGW_LIMIT=$(aws service-quotas get-service-quota --service-code ec2 --quota-code L-A4707A72 --query 'Quota.Value' --output text 2>/dev/null || echo "5")
    
    if [ "$IGW_COUNT" -ge "$IGW_LIMIT" ]; then
        print_error "Internet Gateway quota exceeded: $IGW_COUNT/$IGW_LIMIT IGWs in use"
        print_error "Please delete unused Internet Gateways"
        exit 1
    fi
    print_success "Internet Gateway quota available: $IGW_COUNT/$IGW_LIMIT IGWs used"
    
    # Check S3 bucket availability
    print_step "Checking S3 bucket availability..."
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    S3_BUCKET_NAME="bankiq-uploaded-docs-${ACCOUNT_ID}"
    
    if aws s3api head-bucket --bucket "$S3_BUCKET_NAME" 2>/dev/null; then
        print_warning "S3 bucket already exists: $S3_BUCKET_NAME"
        echo -e "${YELLOW}Do you want to use the existing bucket? (Y/n): ${NC}"
        read -r response
        if [[ "$response" =~ ^[Nn]$ ]]; then
            print_error "Deployment cancelled - bucket conflict"
            exit 1
        else
            print_success "Will use existing S3 bucket"
        fi
    else
        print_success "S3 bucket name available: $S3_BUCKET_NAME"
    fi
    
    # Check if stack already exists
    if aws cloudformation describe-stacks --stack-name bankiq-platform &> /dev/null; then
        print_warning "Stack 'bankiq-platform' already exists!"
        echo -e "${YELLOW}Do you want to delete and recreate it? (y/N): ${NC}"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            print_step "Deleting existing stack..."
            aws cloudformation delete-stack --stack-name bankiq-platform
            print_step "Waiting for stack deletion (this may take 5-10 minutes)..."
            aws cloudformation wait stack-delete-complete --stack-name bankiq-platform
            print_success "Existing stack deleted"
        else
            print_error "Deployment cancelled"
            exit 1
        fi
    fi
}

# Main deployment function
main() {
    print_banner "🏦 BankIQ+ PLATFORM DEPLOYMENT 🚀"
    
    echo -e "${PURPLE}Welcome to BankIQ+ Platform Deployment!${NC}"
    echo -e "${PURPLE}This will deploy a complete banking analytics platform with:${NC}"
    echo -e "  • React UI on ECS Fargate"
    echo -e "  • AgentCore Runtime Backend Integration"
    echo -e "  • API Gateway with Lambda Proxy"
    echo -e "  • S3 Document Storage"
    echo -e "  • VPC with Security Groups"
    echo ""
    echo -e "${YELLOW}⏱️  Total deployment time: ~20-25 minutes${NC}"
    echo -e "${YELLOW}📋 Deployment phases: 5 phases${NC}"
    echo ""
    echo -e "${CYAN}Press Enter to continue or Ctrl+C to cancel...${NC}"
    read -r
    
    # Phase 0: Agent Deployment
    print_banner "🤖 PHASE 0/5: AGENT DEPLOYMENT TO AGENTCORE"
    print_step "Checking if Strands agent exists..."
    
    if [ ! -f "backend/banking_strands_agent.py" ]; then
        print_error "Agent file not found: backend/banking_strands_agent.py"
        exit 1
    fi
    print_success "Agent file found"
    
    print_step "Deploying Strands agent to AgentCore Runtime..."
    print_info "This will build and deploy the banking agent (3-5 minutes)"
    
    cd backend
    if ! command -v strands &> /dev/null; then
        print_warning "Strands CLI not found. Installing automatically..."
        pip install strands-agents bedrock-agentcore
        print_success "Strands CLI installed successfully"
    else
        print_success "Strands CLI found"
    fi
    
    # Generate unique agent name
    TIMESTAMP=$(date +%s)
    USER_ID=$(whoami | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]//g')
    UNIQUE_SUFFIX="${USER_ID}-${TIMESTAMP}"
    
    print_step "Creating unique agent: banking-strands-agent-${UNIQUE_SUFFIX}"
    
    # Create temporary agent file with unique name
    cp banking_strands_agent.py banking_strands_agent_${UNIQUE_SUFFIX}.py
    
    # Deploy unique agent
    strands deploy banking_strands_agent_${UNIQUE_SUFFIX}.py
    
    # Clean up temporary file
    rm banking_strands_agent_${UNIQUE_SUFFIX}.py
    
    # Get agent ARN from deployment output
    AGENT_ARN=$(grep "Agent: arn:aws:bedrock-agentcore" deployment_info.txt | cut -d' ' -f2 || echo "")
    if [ -z "$AGENT_ARN" ]; then
        print_error "Could not extract agent ARN from deployment"
        exit 1
    fi
    
    cd ..
    print_success "Unique agent deployed: banking-strands-agent-${UNIQUE_SUFFIX}"
    print_success "Agent ARN: $AGENT_ARN"
    
    # Phase 1: Prerequisites
    print_banner "📋 PHASE 1/5: PREREQUISITES CHECK"
    check_prerequisites
    
    # Get IP address
    print_step "Getting your public IP address..."
    YOUR_IP=$(curl -s https://checkip.amazonaws.com)
    if [ -z "$YOUR_IP" ]; then
        print_error "Failed to get IP address"
        exit 1
    fi
    print_success "Your IP: $YOUR_IP"
    
    # Phase 2: Infrastructure Deployment
    print_banner "🏗️  PHASE 2/5: INFRASTRUCTURE DEPLOYMENT"
    print_step "Deploying AWS infrastructure (VPC, ECS, ALB, API Gateway)..."
    print_info "This creates ~25 AWS resources and takes 10-15 minutes"
    
    aws cloudformation create-stack \
      --stack-name bankiq-platform \
      --template-body file://bank-iq-plus-agentic.yaml \
      --parameters ParameterKey=YourIPAddress,ParameterValue=$YOUR_IP ParameterKey=AgentARNParameter,ParameterValue=$AGENT_ARN \
      --capabilities CAPABILITY_IAM
    
    print_success "CloudFormation stack creation initiated"
    print_step "Waiting for infrastructure deployment..."
    
    # Monitor stack creation with progress
    while true; do
        STATUS=$(aws cloudformation describe-stacks --stack-name bankiq-platform --query 'Stacks[0].StackStatus' --output text 2>/dev/null || echo "PENDING")
        case $STATUS in
            "CREATE_COMPLETE")
                print_success "Infrastructure deployment completed!"
                break
                ;;
            "CREATE_FAILED"|"ROLLBACK_COMPLETE"|"ROLLBACK_FAILED")
                print_error "Infrastructure deployment failed with status: $STATUS"
                print_error "Check CloudFormation console for details"
                exit 1
                ;;
            *)
                echo -ne "\r${CYAN}Status: $STATUS - Still deploying...${NC}"
                sleep 10
                ;;
        esac
    done
    echo ""
    
    # Get stack outputs
    print_step "Retrieving deployment information..."
    ECR_UI_URI=$(aws cloudformation describe-stacks \
      --stack-name bankiq-platform \
      --query 'Stacks[0].Outputs[?OutputKey==`UIECRRepository`].OutputValue' \
      --output text)
    
    APP_URL=$(aws cloudformation describe-stacks \
      --stack-name bankiq-platform \
      --query 'Stacks[0].Outputs[?OutputKey==`ApplicationURL`].OutputValue' \
      --output text)
    
    API_URL=$(aws cloudformation describe-stacks \
      --stack-name bankiq-platform \
      --query 'Stacks[0].Outputs[?OutputKey==`APIGatewayURL`].OutputValue' \
      --output text)
    
    S3_BUCKET=$(aws cloudformation describe-stacks \
      --stack-name bankiq-platform \
      --query 'Stacks[0].Outputs[?OutputKey==`S3Bucket`].OutputValue' \
      --output text)
    
    print_success "Retrieved all deployment URLs and resources"
    
    # Phase 3: Container Build & Push
    print_banner "🐳 PHASE 3/5: CONTAINER BUILD & DEPLOYMENT"
    
    # ECR Login
    print_step "Logging into Amazon ECR..."
    aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_UI_URI
    print_success "ECR login successful"
    
    # Update frontend configuration
    print_step "Configuring frontend environment..."
    cat > frontend/.env << EOF
REACT_APP_API_BASE_URL=$API_URL
REACT_APP_S3_BUCKET=$S3_BUCKET
REACT_APP_AGENT_ARN=$AGENT_ARN
EOF
    print_success "Frontend configuration updated"
    
    # Build container
    print_step "Building React UI container (this may take 3-5 minutes)..."
    cd frontend
    docker build --platform linux/amd64 -t bankiq-ui . --quiet
    print_success "Container build completed"
    
    # Tag and push
    print_step "Pushing container to ECR..."
    docker tag bankiq-ui:latest $ECR_UI_URI:latest
    docker push $ECR_UI_URI:latest --quiet
    cd ..
    print_success "Container pushed to ECR"
    
    # Phase 4: Service Deployment
    print_banner "🚀 PHASE 4/5: SERVICE DEPLOYMENT"
    
    print_step "Deploying UI service to ECS Fargate..."
    aws ecs update-service \
      --cluster bankiq-platform-cluster \
      --service bankiq-ui-service \
      --force-new-deployment > /dev/null
    
    print_step "Waiting for service to become stable..."
    aws ecs wait services-stable \
      --cluster bankiq-platform-cluster \
      --services bankiq-ui-service
    
    print_success "Service deployment completed"
    
    # Final Success Banner
    print_banner "🎉 DEPLOYMENT SUCCESSFUL! 🎉"
    
    echo -e "${GREEN}✅ BankIQ+ Platform is now live and ready!${NC}"
    echo ""
    echo -e "${CYAN}🎯 ACCESS YOUR PLATFORM:${NC}"
    echo -e "   ${YELLOW}Frontend UI:${NC} $APP_URL"
    echo -e "   ${YELLOW}API Gateway:${NC} $API_URL"
    echo ""
    echo -e "${CYAN}🔧 DEPLOYED COMPONENTS:${NC}"
    echo -e "   ✅ React UI on ECS Fargate"
    echo -e "   ✅ AgentCore Runtime Backend"
    echo -e "   ✅ API Gateway Integration"
    echo -e "   ✅ S3 Document Storage ($S3_BUCKET)"
    echo -e "   ✅ VPC with Public/Private Subnets"
    echo -e "   ✅ Application Load Balancer"
    echo -e "   ✅ CloudWatch Logging"
    echo ""
    echo -e "${CYAN}🔒 SECURITY FEATURES:${NC}"
    echo -e "   🛡️  IP-restricted access ($YOUR_IP only)"
    echo -e "   🛡️  Private subnets for containers"
    echo -e "   🛡️  IAM roles with minimal permissions"
    echo -e "   🛡️  HTTPS-ready infrastructure"
    echo ""
    echo -e "${PURPLE}📊 Your banking analytics platform is ready!${NC}"
    echo -e "${PURPLE}🏦 Start analyzing peer bank performance and SEC filings!${NC}"
    echo ""
    echo -e "${YELLOW}💡 Next steps:${NC}"
    echo -e "   1. Open $APP_URL in your browser"
    echo -e "   2. Try the Peer Analytics with major banks"
    echo -e "   3. Upload financial documents for analysis"
    echo -e "   4. Chat with AI about banking metrics"
    echo ""
}

# Run main function
main