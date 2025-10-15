# Project Structure

## 📁 Directory Organization

```
peer-bank-analytics-agentic/
│
├── backend/                           # Backend Services
│   ├── banking_agent_simple.py        # Main Strands agent (10 tools)
│   ├── server.js                      # Express API server
│   ├── invoke-agentcore.py            # Python bridge to AgentCore
│   ├── package.json                   # Node dependencies
│   ├── requirements.txt               # Python dependencies
│   ├── .bedrock_agentcore.yaml        # Agent configuration
│   └── [other agent files]            # Legacy agents (optional)
│
├── frontend/                          # React Application
│   ├── src/
│   │   ├── components/
│   │   │   ├── PeerAnalytics.js       # Bank comparison UI
│   │   │   ├── FinancialReports.js    # SEC filings & chat UI
│   │   │   ├── Home.js                # Landing page
│   │   │   └── Navbar.js              # Navigation
│   │   ├── services/
│   │   │   └── api.js                 # Backend API client
│   │   ├── App.js                     # Main app component
│   │   └── index.js                   # Entry point
│   ├── public/                        # Static assets
│   ├── package.json                   # Dependencies
│   └── nginx.conf                     # Production config
│
├── scripts/                           # Utility Scripts
│   ├── start-dev.sh                   # Start everything locally
│   ├── start-frontend.sh              # Start frontend only
│   ├── test-local.sh                  # Test the setup
│   └── deploy-complete.sh             # Production deployment
│
├── deployment/                        # Deployment Configurations
│   └── bank-iq-plus-fargate.yaml      # AWS Fargate CloudFormation
│
├── docs/                              # Documentation
│   ├── SETUP.md                       # Quick setup guide
│   ├── QUICK_START.md                 # 3-step quick start
│   ├── DEPLOY_SIMPLE.md               # Detailed deployment
│   ├── CHECKLIST.md                   # Verification checklist
│   ├── AGENT_TOOLS_UPDATED.md         # Tool documentation
│   ├── SUMMARY.md                     # Project overview
│   ├── AGENTCORE_IMPLEMENTATION_GUIDE.md # Complete guide
│   ├── PROJECT_STRUCTURE.md           # This file
│   ├── architecture_details.md        # Architecture docs
│   ├── DEPLOYMENT-GUIDE.md            # Deployment guide
│   └── archive/                       # Old documentation
│
├── arch/                              # Architecture Diagrams
│   └── bankiq_plus_agentcore_architecture.png
│
├── test-simple/                       # Simple test examples
├── amazon-bedrock-agentcore-samples/  # AWS samples (reference)
├── strands-sdk/                       # Strands SDK (reference)
├── sec-edgar-mcp/                     # SEC EDGAR MCP (reference)
│
├── .gitignore                         # Git ignore rules
├── .dockerignore                      # Docker ignore rules
├── Dockerfile                         # Docker configuration
├── LICENSE                            # MIT License
├── README.md                          # Main readme
└── requirements.txt                   # Root Python deps
```

## 🎯 Key Files

### Backend
- **`banking_agent_simple.py`** - Main agent with 10 tools
- **`server.js`** - Express backend (port 3001)
- **`invoke-agentcore.py`** - Python bridge to AgentCore CLI
- **`.bedrock_agentcore.yaml`** - Agent configuration

### Frontend
- **`PeerAnalytics.js`** - Bank comparison with Live/Upload modes
- **`FinancialReports.js`** - SEC filings and document chat
- **`api.js`** - Backend API integration

### Scripts
- **`start-dev.sh`** - One-command local startup
- **`deploy-complete.sh`** - Production deployment

### Documentation
- **`SETUP.md`** - Start here for setup
- **`QUICK_START.md`** - 3-step quick start
- **`AGENT_TOOLS_UPDATED.md`** - Tool reference

## 📦 Dependencies

### Backend
```json
{
  "express": "^4.18.2",
  "cors": "^2.8.5"
}
```

```txt
bedrock-agentcore
strands-agents
boto3
requests
```

### Frontend
```json
{
  "react": "^18.2.0",
  "@mui/material": "^5.14.0",
  "recharts": "^2.8.0"
}
```

## 🔄 Data Flow

```
User → React UI (3000)
  ↓
Express Backend (3001)
  ↓
Python Bridge
  ↓
AgentCore CLI
  ↓
AWS AgentCore Runtime
  ↓
Strands Agent (10 tools)
  ↓
Claude Sonnet 4.5
  ↓
Response back to User
```

## 🗂️ File Purposes

### Root Level
- **README.md** - Main project documentation
- **LICENSE** - MIT license
- **Dockerfile** - Container configuration
- **.gitignore** - Git exclusions

### Backend
- Agent code and API server
- Python bridge for AgentCore
- Configuration files

### Frontend
- React application
- UI components
- API integration

### Scripts
- Development utilities
- Deployment automation
- Testing tools

### Deployment
- CloudFormation templates
- Infrastructure as code

### Docs
- Setup guides
- API documentation
- Architecture details

## 🚀 Getting Started

1. Read **README.md** for overview
2. Follow **docs/SETUP.md** for setup
3. Use **scripts/start-dev.sh** to start
4. Check **docs/CHECKLIST.md** to verify

## 📝 Notes

- All scripts are in `scripts/` folder
- All documentation is in `docs/` folder
- All deployment configs are in `deployment/` folder
- Root level is clean with only essential files

---

**Clean, organized, and easy to navigate!** 🎉
