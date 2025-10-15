# BankIQ+ - AI-Powered Banking Analytics Platform

> **AWS Bedrock AgentCore** implementation with **Strands framework** for intelligent banking analytics

## 🚀 Quick Start

```bash
# 1. Deploy agent to AgentCore
cd backend
agentcore configure -e banking_agent_simple.py
agentcore launch

# 2. Start the application
cd ..
./scripts/start-dev.sh
```

Open http://localhost:3000

## 📁 Project Structure

```
peer-bank-analytics-agentic/
├── backend/                    # Agent & API Server
│   ├── banking_agent_simple.py # Strands agent (10 tools)
│   ├── server.js              # Express backend
│   ├── invoke-agentcore.py    # Python bridge
│   └── .bedrock_agentcore.yaml # Agent config
├── frontend/                   # React UI
│   ├── src/components/        # UI components
│   │   ├── PeerAnalytics.js   # Bank comparison
│   │   └── FinancialReports.js # SEC filings & chat
│   └── src/services/api.js    # Backend API calls
├── scripts/                    # Utility scripts
│   ├── start-dev.sh           # Start everything
│   ├── start-frontend.sh      # Frontend only
│   ├── test-local.sh          # Test setup
│   └── deploy-complete.sh     # Production deploy
├── deployment/                 # Deployment configs
│   └── bank-iq-plus-fargate.yaml # Fargate CloudFormation
├── docs/                       # Documentation
│   ├── SETUP.md               # Setup guide
│   ├── QUICK_START.md         # 3-step guide
│   ├── DEPLOY_SIMPLE.md       # Deployment guide
│   ├── CHECKLIST.md           # Verification
│   ├── AGENT_TOOLS_UPDATED.md # Tool docs
│   └── SUMMARY.md             # Overview
└── README.md                   # This file
```

## ✨ Features

### Peer Bank Analytics
- **Live Data**: Real-time FDIC banking metrics
- **Upload CSV**: Custom data analysis
- **AI Insights**: Claude-powered analysis
- **Interactive Charts**: Performance visualization

### Financial Reports
- **Live EDGAR**: Real-time SEC filings
- **Document Upload**: Analyze your own reports
- **AI Chat**: Ask questions about documents
- **Comprehensive Reports**: Full bank analysis

## 🛠️ Technology Stack

- **AI**: AWS Bedrock AgentCore + Claude Sonnet 4.5
- **Agent Framework**: Strands
- **Backend**: Express.js + Python bridge
- **Frontend**: React + Material-UI
- **Data**: FDIC API, SEC EDGAR API
- **Deployment**: ECS Fargate (optional)

## 📖 Documentation

- **[SETUP.md](docs/SETUP.md)** - Quick setup guide
- **[QUICK_START.md](docs/QUICK_START.md)** - 3-step guide
- **[DEPLOY_SIMPLE.md](docs/DEPLOY_SIMPLE.md)** - Detailed deployment
- **[CHECKLIST.md](docs/CHECKLIST.md)** - Verification steps
- **[AGENT_TOOLS_UPDATED.md](docs/AGENT_TOOLS_UPDATED.md)** - Tool documentation

## 🎯 Agent Tools (10 total)

1. **get_fdic_data** - Current FDIC banking data
2. **compare_banks** - Peer performance comparison
3. **get_sec_filings** - SEC EDGAR filings
4. **generate_bank_report** - Comprehensive analysis
5. **answer_banking_question** - General Q&A
6. **search_banks** - Bank search by name/ticker
7. **upload_csv_to_s3** - Upload CSV data
8. **analyze_csv_peer_performance** - Analyze CSV
9. **upload_document_to_s3** - Upload documents
10. **chat_with_documents** - Chat with docs/filings

## 🔧 Development

### Prerequisites
- AWS Account with Bedrock access
- Node.js 18+
- Python 3.9+
- AWS CLI configured

### Local Development
```bash
# Backend
cd backend
npm install
npm start

# Frontend (new terminal)
cd frontend
npm install
npm start
```

### Testing
```bash
./scripts/test-local.sh
```

## 🚀 Production Deployment

```bash
./scripts/deploy-complete.sh
```

Or use Fargate CloudFormation:
```bash
aws cloudformation create-stack \
  --stack-name bankiq-plus \
  --template-body file://deployment/bank-iq-plus-fargate.yaml \
  --parameters ParameterKey=YourIPAddress,ParameterValue=$(curl -s https://checkip.amazonaws.com)
```

## 💰 Cost Estimate

- **Local Development**: FREE (only AgentCore API calls)
- **AgentCore**: ~$0.01-0.10 per 1K invocations
- **Claude API**: ~$0.003 per 1K input tokens
- **Production (Fargate)**: ~$15-30/month

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Open Pull Request

## 📄 License

MIT License - see LICENSE file

## 🆘 Support

- Check agent logs: `agentcore logs --follow`
- Check backend logs: Terminal where `npm start` runs
- Review documentation in `docs/` folder

---

**Built with ❤️ for the financial services community**

Authors: Shashi Makkapati, Senthil Kamala Rathinam, Jacob Scheatzle
