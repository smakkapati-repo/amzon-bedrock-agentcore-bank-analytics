# BankIQ+ - AI Banking Analytics Platform
**Authors:** Shashi Makkapati, Senthil Kamala Rathinam, Jacob Scheatzle

## Background & Strategic Context

The advent of Generative AI has revolutionized how financial institutions process and interpret complex banking data. BankIQ+ represents a paradigm shift from traditional rule-based analytics to intelligent, context-aware financial analysis. By integrating AWS Bedrock AgentCore with Claude Sonnet 4.5, real-time FDIC data, and SEC EDGAR filings, the platform doesn't just present numbers—it understands relationships between metrics, identifies emerging trends, and generates human-like insights.

The AI agent can instantly correlate a bank's declining Net Interest Margin with industry-wide patterns, explain strategic implications of capital changes, or predict potential regulatory concerns based on CRE concentration trends. This GenAI-powered approach transforms raw regulatory data into conversational insights, enabling bank executives to ask natural language questions like "Why is our ROA underperforming compared to similar-sized banks?" and receive comprehensive, contextual analysis that considers market conditions, regulatory environment, and peer performance.

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

## 🏗️ AWS Architecture

![BankIQ+ AWS Architecture](arch/bankiq_plus_agentcore_architecture.png)

**Key Components:**
- **CloudFront CDN**: Global content delivery with 300-second timeout
- **Application Load Balancer**: Routes API traffic to ECS containers
- **ECS Fargate**: Serverless containers in private subnets
- **AWS Bedrock AgentCore**: Managed AI agent runtime with 12 tools
- **Claude Sonnet 4.5**: Advanced AI analysis and conversational memory
- **S3 Storage**: Frontend hosting and document uploads
- **VPC with Multi-AZ**: High availability deployment
- **IAM Roles**: Minimal permissions for secure access
- **CloudWatch**: Comprehensive logging and monitoring

### Architecture Deep Dive

BankIQ+ follows a modern, cloud-native architecture built on AWS services with security-first design. User requests flow through [CloudFront](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Introduction.html) for global content delivery, routing static files from [S3](https://docs.aws.amazon.com/s3/) and API calls to the [Application Load Balancer](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/introduction.html). The ALB distributes traffic to containerized applications running on [Amazon ECS Fargate](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/AWS_Fargate.html), eliminating server management while providing automatic scaling.

The platform's intelligence comes from [AWS Bedrock AgentCore](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html), which orchestrates 12 specialized tools for banking analytics. The agent uses [Claude Sonnet 4.5](https://www.anthropic.com/claude) for natural language understanding and maintains conversational memory across sessions. External data integration includes FDIC APIs for real-time banking metrics and SEC EDGAR APIs for financial filings. Documents uploaded to S3 are analyzed using PyPDF2 for metadata extraction and Claude for comprehensive analysis.

Security is embedded throughout: Fargate containers run in private subnets, [IAM roles](https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction.html) provide fine-grained access control, and [CloudWatch](https://docs.aws.amazon.com/cloudwatch/) enables comprehensive monitoring. The architecture eliminates API Gateway's 30-second timeout limitation, supporting long-running queries up to 300 seconds. Infrastructure is deployed through [CloudFormation](https://docs.aws.amazon.com/cloudformation/) templates, ensuring consistent, repeatable deployments.

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

## ✨ Platform Features

### 📊 Peer Bank Analytics
- **500+ Banks**: Access entire SEC EDGAR database
- **Live FDIC Data**: Real-time financial metrics and trends
- **Custom CSV Upload**: Analyze your own peer data
- **AI-Powered Comparison**: Automated tool selection by Claude

### 📋 Financial Reports Analyzer
- **SEC Filings**: 10-K and 10-Q analysis for any public bank
- **Document Upload**: Analyze your own financial PDFs
- **Conversational Memory**: Context-aware across queries
- **AI Chat**: Interactive Q&A about uploaded documents

### 🔧 Analysis Modes
1. **Live FDIC**: Real-time banking metrics from FDIC Call Reports
2. **SEC EDGAR**: Direct integration with SEC.gov APIs
3. **Document Upload**: PDF analysis with metadata extraction
4. **Chat Mode**: Conversational analysis with memory

## 🏦 Supported Banks & Metrics

**500+ Banks** from SEC EDGAR database including:
- JPMorgan Chase, Bank of America, Wells Fargo, Citigroup
- Goldman Sachs, Morgan Stanley, U.S. Bancorp, PNC Financial
- Capital One, Truist Financial, Webster Financial, and 490+ more

**Key Banking Metrics:**
- **ROA** - Return on Assets: Net income as % of average assets
- **ROE** - Return on Equity: Net income as % of average equity
- **NIM** - Net Interest Margin: Interest spread as % of assets
- **Efficiency Ratio** - Operating expenses as % of revenue
- **Loan-to-Deposit** - Loans as % of deposits
- **CRE Concentration** - Commercial real estate loans as % of capital

## 🎯 AI Agent Tools (12 total)

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

## 🚀 Deployment Guide

### Prerequisites

**Required:**
- AWS Account with administrative access
- AWS Bedrock access enabled (see setup below)
- AWS CLI configured (`aws configure`)
- Docker installed
- Node.js 18+
- Python 3.11+
- AgentCore CLI: `pip install bedrock-agentcore-starter-toolkit`

**Enable Bedrock Access:**
1. Go to [AWS Bedrock Console](https://console.aws.amazon.com/bedrock/)
2. Navigate to **Model Access** in the left sidebar
3. Click **Request model access**
4. Enable: **Anthropic Claude Sonnet 4.5**
5. Wait for approval (usually instant)

### One-Command Deployment

```bash
# Clone repository
git clone https://github.com/smakkapati-repo/peer-bank-analytics-agentic.git
cd peer-bank-analytics-agentic

# Deploy everything
./cfn/scripts/deploy-all.sh
```

**Deployment Time**: ~15-20 minutes

**What Gets Deployed:**
- ✅ AgentCore agent with 12 AI tools
- ✅ VPC with public/private subnets
- ✅ Application Load Balancer
- ✅ ECS Fargate cluster and service
- ✅ CloudFront distribution
- ✅ S3 buckets (frontend + documents)
- ✅ ECR repository with Docker image
- ✅ IAM roles with minimal permissions
- ✅ CloudWatch log groups

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
