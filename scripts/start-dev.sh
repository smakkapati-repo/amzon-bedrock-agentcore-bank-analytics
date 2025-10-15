#!/bin/bash

echo "🚀 Starting BankIQ+ Development Environment"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js not found. Please install Node.js 18+${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Node.js $(node --version)${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 not found. Please install Python 3.9+${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python $(python3 --version)${NC}"

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${YELLOW}⚠️  AWS CLI not found. Install it to deploy agent.${NC}"
else
    echo -e "${GREEN}✅ AWS CLI $(aws --version | cut -d' ' -f1)${NC}"
fi

# Check AgentCore CLI
if ! command -v agentcore &> /dev/null; then
    echo -e "${YELLOW}⚠️  AgentCore CLI not found${NC}"
    echo "   Install with: pip install bedrock-agentcore-starter-toolkit"
    echo ""
    read -p "Install now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pip3 install bedrock-agentcore strands-agents bedrock-agentcore-starter-toolkit boto3 requests
    fi
else
    echo -e "${GREEN}✅ AgentCore CLI installed${NC}"
fi

echo ""
echo "🔧 Setting up environment..."

# Install backend dependencies
if [ ! -d "backend/node_modules" ]; then
    echo "📦 Installing backend dependencies..."
    cd backend && npm install && cd ..
else
    echo -e "${GREEN}✅ Backend dependencies installed${NC}"
fi

# Install frontend dependencies
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend && npm install && cd ..
else
    echo -e "${GREEN}✅ Frontend dependencies installed${NC}"
fi

echo ""
echo "🎯 Checking AgentCore deployment..."

# Check if agent is deployed
cd backend
if agentcore status &> /dev/null; then
    echo -e "${GREEN}✅ Agent deployed to AgentCore${NC}"
else
    echo -e "${YELLOW}⚠️  Agent not deployed yet${NC}"
    echo ""
    echo "To deploy the agent:"
    echo "  cd backend"
    echo "  agentcore configure -e banking_agent_simple.py"
    echo "  agentcore launch"
    echo ""
    read -p "Deploy now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Configuring agent..."
        agentcore configure -e banking_agent_simple.py
        echo "Deploying to AWS..."
        agentcore launch
        echo -e "${GREEN}✅ Agent deployed!${NC}"
    else
        echo -e "${YELLOW}⚠️  Skipping deployment. You'll need to deploy manually.${NC}"
    fi
fi
cd ..

echo ""
echo "🚀 Starting services..."
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start backend
echo "Starting backend on port 3001..."
cd backend
npm start &
BACKEND_PID=$!
cd ..

# Wait for backend to be ready
echo "Waiting for backend to start..."
for i in {1..30}; do
    if curl -s http://localhost:3001/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend ready${NC}"
        break
    fi
    sleep 1
done

# Start frontend
echo "Starting frontend on port 3000..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ BankIQ+ is running!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌐 Frontend:  http://localhost:3000"
echo "🔧 Backend:   http://localhost:3001"
echo "💚 Health:    http://localhost:3001/health"
echo ""
echo "📝 Try these in the UI:"
echo "   • Compare JPMorgan Chase vs Bank of America using ROE"
echo "   • Get latest FDIC banking data"
echo "   • Generate a report for Wells Fargo"
echo ""
echo "Press Ctrl+C to stop all services"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Wait for processes
wait
