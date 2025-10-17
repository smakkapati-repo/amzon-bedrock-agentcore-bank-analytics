# BankIQ+ - AI Banking Analytics Platform

> AWS Bedrock AgentCore + Strands framework for intelligent banking analytics

## 🚀 Quick Start

```bash
# Deploy to AWS
./cfn/scripts/deploy-all.sh

# Access at CloudFront URL (output after deployment)
```

## 📁 Project Structure

```
peer-bank-analytics-agentic/
├── backend/
│   ├── bank_iq_agent_v1.py      # Strands agent (12 tools)
│   ├── server.js                # Express API server
│   ├── Dockerfile               # Agent container
│   └── Dockerfile.backend       # Backend container
├── frontend/
│   └── src/                     # React UI
├── cfn/
│   ├── templates/               # CloudFormation templates
│   └── scripts/                 # Deployment scripts
├── arch/
│   └── banking_architecture_diagram.py  # Architecture diagram
└── DEPLOYMENT_GUIDE.md          # Complete deployment guide
```

## ✨ Features

- **Peer Bank Analytics** - FDIC data comparison
- **Financial Reports** - SEC filings analysis
- **CSV Upload** - Custom data analysis
- **Document Chat** - AI-powered Q&A

## 🏗️ Architecture

```
User (HTTPS) → CloudFront → ALB (HTTP) → ECS Fargate → AgentCore
                    ↓
                S3 (React App)
```

**Key Points:**
- No API Gateway (no 30-sec timeout!)
- CloudFront → ALB uses HTTP (secure within AWS)
- 300-second timeout for long queries
- Auto-scaling ECS Fargate

## 🛠️ Technology Stack

- **AI**: AWS Bedrock AgentCore + Claude Sonnet 4
- **Agent**: Strands framework
- **Backend**: Express.js + Python
- **Frontend**: React + Material-UI
- **Infrastructure**: ECS Fargate, ALB, CloudFront, S3

## 📖 Documentation

- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete deployment guide
- **[backend/README_AGENT.md](backend/README_AGENT.md)** - Agent documentation
- **[arch/](arch/)** - Architecture diagrams

## 🎯 Agent Tools (12 total)

1. `get_fdic_data` - Current FDIC banking data
2. `search_fdic_bank` - Search FDIC by bank name
3. `compare_banks` - Peer performance comparison
4. `get_sec_filings` - SEC EDGAR filings
5. `generate_bank_report` - Comprehensive analysis
6. `answer_banking_question` - General Q&A
7. `search_banks` - Bank search by name/ticker
8. `upload_csv_to_s3` - Upload CSV data
9. `analyze_csv_peer_performance` - Analyze CSV
10. `analyze_and_upload_pdf` - Upload and analyze PDFs
11. `analyze_uploaded_pdf` - Analyze PDFs in S3
12. `chat_with_documents` - Chat with docs/filings

## ⚠️ CRITICAL: Dockerfile Naming

**Two separate Dockerfiles:**
- `backend/Dockerfile` = Python agent (AgentCore) - DO NOT RENAME
- `backend/Dockerfile.backend` = Node.js API server (ECS)

See `backend/README_AGENT.md` for details.

## 🔧 Prerequisites

- AWS Account with Bedrock access
- AWS CLI configured
- Docker installed
- Node.js 18+
- Python 3.11+

## 🚀 Deployment

```bash
# One command deployment
./cfn/scripts/deploy-all.sh
```

**Time**: ~15-20 minutes

**What gets deployed:**
- ECS Fargate cluster with ALB
- CloudFront distribution with S3
- Docker image to ECR
- React app to S3

## 💰 Cost Estimate

Monthly costs (24/7 operation):
- ECS Fargate: $15-20
- ALB: $16-20
- CloudFront: $1-5
- S3: $1-2
- Bedrock: $10-30

**Total**: ~$50-90/month

## 🔄 Update Deployment

### Update Backend
```bash
cd backend
docker build -f Dockerfile.backend -t bankiq-backend .
# Push to ECR (see DEPLOYMENT_GUIDE.md)
```

### Update Frontend
```bash
cd frontend
npm run build
aws s3 sync build/ s3://BUCKET_NAME/ --delete
aws cloudfront create-invalidation --distribution-id DIST_ID --paths "/*"
```

## 📝 Monitoring

```bash
# View ECS logs
aws logs tail /ecs/bankiq-backend --follow

# View AgentCore logs
agentcore status
```

## 🆘 Troubleshooting

**Issue**: CloudFront returns 502
- Check ECS task health
- Check ALB target health
- View logs: `aws logs tail /ecs/bankiq-backend --follow`

**Issue**: Agent not responding
- Check AgentCore status: `agentcore status`
- Verify agent ARN in ECS task environment variables

## 📄 License

MIT License

## 👥 Authors

Shashi Makkapati, Senthil Kamala Rathinam, Jacob Scheatzle
