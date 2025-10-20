# BankIQ+ - AI Banking Analytics Platform (**Powered by [Amazon Bedrock AgentCore](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)**) 


**Authors:** Shashi Makkapati, Senthil Kamala Rathinam, Jacob Scheatzle

> **Technology Showcase**: This project demonstrates the capabilities of **Amazon Bedrock AgentCore** (AWS's new managed agent runtime) and the **Strands framework** for building production-ready AI agents with tool orchestration, conversational memory, and enterprise-grade security.

## 🚀 Why This Project Matters

### Amazon Bedrock AgentCore + Strands Framework
This is a **reference implementation** showcasing:
- **Amazon Bedrock AgentCore** - AWS's newly launched managed agent runtime (announced October 2025)
- **Strands Framework** - Python-based agent orchestration with 12 custom tools
- **Production Architecture** - CloudFront + ECS + Cognito + AgentCore (no API Gateway)
- **Conversational Memory** - Multi-turn conversations with context retention
- **Tool Orchestration** - Claude Sonnet 4.5 automatically selects from 12 specialized tools
- **Enterprise Security** - JWT authentication, IAM roles, private subnets

### Banking Analytics Use Case
The advent of Generative AI has revolutionized how financial institutions process and interpret complex banking data. BankIQ+ represents a paradigm shift from traditional rule-based analytics to intelligent, context-aware financial analysis. By integrating Amazon Bedrock AgentCore with Claude Sonnet 4.5, real-time FDIC data, and SEC EDGAR filings, the platform doesn't just present numbers—it understands relationships between metrics, identifies emerging trends, and generates human-like insights.

The AI agent can instantly correlate a bank's declining Net Interest Margin with industry-wide patterns, explain strategic implications of capital changes, or predict potential regulatory concerns based on CRE concentration trends. This GenAI-powered approach transforms raw regulatory data into conversational insights, enabling bank executives to ask natural language questions like "Why is our ROA underperforming compared to similar-sized banks?" and receive comprehensive, contextual analysis that considers market conditions, regulatory environment, and peer performance.

## 🚀 Quick Start

```bash
# Deploy to AWS
./cfn/scripts/deploy-all.sh

# Access at CloudFront URL (output after deployment)
```



## ✨ Features

- **Secure Authentication** - AWS Cognito with self-service signup
- **Peer Bank Analytics** - FDIC data comparison
- **Financial Reports** - SEC filings analysis
- **CSV Upload** - Custom data analysis
- **Document Chat** - AI-powered Q&A

## 🏗️ AWS Architecture

![BankIQ+ AWS Architecture](arch/bankiq_plus_agentcore_architecture.png)

**Key Components:**
- **Cognito User Pool**: Secure authentication with Hosted UI and JWT tokens
- **CloudFront CDN**: Global content delivery with 300-second timeout
- **Application Load Balancer**: Routes API traffic to ECS containers
- **ECS Fargate**: Serverless containers in private subnets with JWT verification
- **Amazon Bedrock AgentCore**: Managed AI agent runtime with 12 tools
- **Claude Sonnet 4.5**: Advanced AI analysis and conversational memory
- **S3 Storage**: Frontend hosting and document uploads
- **VPC with Multi-AZ**: High availability deployment
- **IAM Roles**: Minimal permissions for secure access
- **CloudWatch**: Comprehensive logging and monitoring

### Architecture Deep Dive

BankIQ+ follows a modern, cloud-native architecture built on AWS services with security-first design. User requests flow through [CloudFront](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Introduction.html) for global content delivery, routing static files from [S3](https://docs.aws.amazon.com/s3/) and API calls to the [Application Load Balancer](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/introduction.html). The ALB distributes traffic to containerized applications running on [Amazon ECS Fargate](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/AWS_Fargate.html), eliminating server management while providing automatic scaling.

The platform's intelligence comes from [Amazon Bedrock AgentCore](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html), which orchestrates 12 specialized tools for banking analytics. The agent uses [Claude Sonnet 4.5](https://www.anthropic.com/claude) for natural language understanding and maintains conversational memory across sessions. External data integration includes FDIC APIs for real-time banking metrics and SEC EDGAR APIs for financial filings. Documents uploaded to S3 are analyzed using PyPDF2 for metadata extraction and Claude for comprehensive analysis.

Security is embedded throughout: [AWS Cognito](https://docs.aws.amazon.com/cognito/) provides enterprise-grade authentication with OAuth 2.0 and JWT tokens, Fargate containers run in private subnets with JWT verification, [IAM roles](https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction.html) provide fine-grained access control, and [CloudWatch](https://docs.aws.amazon.com/cloudwatch/) enables comprehensive monitoring. The architecture eliminates API Gateway's 30-second timeout limitation, supporting long-running queries up to 300 seconds. Infrastructure is deployed through [CloudFormation](https://docs.aws.amazon.com/cloudformation/) templates, ensuring consistent, repeatable deployments.

## 🛠️ Technology Stack

### Core AI Platform (NEW AWS Services)
- **[Amazon Bedrock AgentCore](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)** - Managed agent runtime with built-in memory and tool orchestration
- **[Strands Framework](https://github.com/awslabs/agents-for-amazon-bedrock-sample-code)** - Python agent framework for defining tools and workflows
- **[Claude Sonnet 4.5](https://www.anthropic.com/claude)** - Foundation model for natural language understanding and reasoning

### Application Stack
- **Authentication**: [AWS Cognito](https://docs.aws.amazon.com/cognito/) + [AWS Amplify v6](https://docs.amplify.aws/) (OAuth 2.0 + JWT)
- **Backend**: [Express.js](https://expressjs.com/) (Node.js) + Python agent
- **Frontend**: [React](https://react.dev/) + [Material-UI](https://mui.com/) + AWS Amplify Auth
- **Infrastructure**: [ECS Fargate](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/AWS_Fargate.html), [ALB](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/), [CloudFront](https://docs.aws.amazon.com/cloudfront/), [S3](https://docs.aws.amazon.com/s3/)
- **Security**: [VPC](https://docs.aws.amazon.com/vpc/) private subnets, JWT verification, [IAM roles](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles.html), [Security Groups](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-groups.html)

## 📖 Documentation

- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete deployment guide with Cognito setup
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

## 🎯 AI Agent Tools (12 Custom Tools)

**Strands Framework Implementation** - Each tool is a Python function with:
- Input/output schemas (Pydantic models)
- Error handling and validation
- Integration with external APIs (FDIC, SEC EDGAR)
- S3 operations for document storage

1. `get_fdic_data` - Current FDIC banking data (live API integration)
2. `search_fdic_bank` - Search FDIC by bank name
3. `compare_banks` - Peer performance comparison with trend analysis
4. `get_sec_filings` - SEC EDGAR filings (10-K, 10-Q)
5. `generate_bank_report` - Comprehensive multi-metric analysis
6. `answer_banking_question` - General Q&A with context
7. `search_banks` - Bank search by name/ticker (500+ banks)
8. `upload_csv_to_s3` - Upload CSV data with validation
9. `analyze_csv_peer_performance` - Analyze custom CSV data
10. `analyze_and_upload_pdf` - Upload and analyze PDFs (PyPDF2 + Claude)
11. `analyze_uploaded_pdf` - Analyze PDFs in S3
12. `chat_with_documents` - Multi-turn document Q&A with memory

**Tool Orchestration**: Claude Sonnet 4.5 automatically selects the right tool(s) based on user intent. For example:
- "Compare JPMorgan and Bank of America ROA" → `compare_banks` tool
- "What are Webster's key risks?" → `get_sec_filings` + `chat_with_documents` tools
- "Analyze my custom peer data" → `upload_csv_to_s3` + `analyze_csv_peer_performance` tools

## 🌟 Amazon Bedrock AgentCore Highlights

### What is AgentCore?
Amazon Bedrock AgentCore is a **managed agent runtime** that handles:
- ✅ **Tool Orchestration** - Automatically routes requests to the right tools
- ✅ **Conversational Memory** - Maintains context across multi-turn conversations
- ✅ **Streaming Responses** - Real-time token streaming for better UX
- ✅ **Error Handling** - Automatic retries and graceful degradation
- ✅ **Observability** - Built-in CloudWatch logging and tracing
- ✅ **Scalability** - Serverless, auto-scaling infrastructure

### Why AgentCore vs. Custom Agent?
| Feature | Custom Agent | Amazon Bedrock AgentCore |
|---------|-------------|---------------|
| Infrastructure | You manage | AWS manages |
| Memory | Build yourself | Built-in |
| Tool routing | Manual logic | Automatic (Claude) |
| Scaling | Configure yourself | Auto-scales |
| Monitoring | Setup CloudWatch | Pre-integrated |
| Cost | EC2/Lambda costs | Pay per invocation |

### Strands Framework Benefits
- **Type Safety** - Pydantic schemas for all tool inputs/outputs
- **Easy Testing** - Test tools independently before deployment
- **Version Control** - Agent code in Git, deployed via CLI
- **Hot Reload** - Update agent without infrastructure changes
- **Local Development** - Test locally before deploying to AWS

### Production-Ready Features
1. **No API Gateway** - Direct CloudFront → ALB → ECS (300s timeout)
2. **JWT Authentication** - Cognito User Pool with Hosted UI
3. **Private Subnets** - ECS tasks run in private subnets with NAT
4. **IAM Least Privilege** - Separate roles for ECS, AgentCore, and users
5. **Multi-AZ Deployment** - High availability across availability zones
6. **CloudWatch Monitoring** - Comprehensive logging and metrics

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

### Step-by-Step Deployment

**Step 1: Clone Repository**
```bash
git clone https://github.com/smakkapati-repo/peer-bank-analytics-agentic.git
cd peer-bank-analytics-agentic
```

**Step 2: Install AgentCore CLI**
```bash
pip install bedrock-agentcore-starter-toolkit
agentcore --version  # Verify installation
```

**Step 3: Configure AWS CLI**
```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Enter region: us-east-1
# Enter output format: json
```

**Step 4: Deploy Everything (One Command)**
```bash
./cfn/scripts/deploy-all.sh
```

**Deployment Progress:**
- 🔵 **[1/4] AgentCore Agent** (~3-5 minutes)
  - Builds and deploys Python agent with 12 tools
  - Adds S3 permissions automatically
  - Creates conversational memory

- 🔵 **[2/4] Infrastructure** (~5-7 minutes)
  - VPC with public/private subnets
  - Application Load Balancer
  - ECS cluster
  - S3 buckets

- 🔵 **[3/4] Backend** (~3-5 minutes)
  - Builds Docker image
  - Pushes to ECR
  - Deploys ECS service

- 🔵 **[4/4] Frontend** (~2-3 minutes)
  - Builds React app
  - Uploads to S3
  - Creates CloudFront distribution

**Total Time**: ~15-20 minutes

**Step 5: Access Your Application**

After deployment completes, you'll see:
```
✅ DEPLOYMENT COMPLETE!
🌐 CloudFront URL: https://d2mlfyaj7qolx.cloudfront.net
```

Open the CloudFront URL in your browser to access BankIQ+!

## 🔍 Verify Deployment

**Check Health:**
```bash
# Get CloudFront URL
CLOUDFRONT_URL=$(aws cloudfront list-distributions --query "DistributionList.Items[?contains(Origins.Items[0].DomainName, 'bankiq-frontend')].DomainName" --output text)

# Test health endpoint
curl https://$CLOUDFRONT_URL/api/health
# Expected: {"status":"healthy","service":"BankIQ+ Backend"}
```

**View Logs:**
```bash
# ECS backend logs
aws logs tail /ecs/bankiq-backend --follow

# AgentCore logs
agentcore status
```

## 💰 Cost Estimate

Monthly costs (24/7 operation):
- ECS Fargate: $15-20
- ALB: $16-20
- CloudFront: $1-5
- S3: $1-2
- Bedrock: $10-30

**Total**: ~$50-90/month

## 🧹 Cleanup

To delete all resources:

```bash
./cfn/scripts/cleanup.sh
```

This will remove:
- ✅ CloudFormation stacks (frontend, backend, infrastructure, auth)
- ✅ Cognito User Pool and all users
- ✅ S3 buckets (with contents)
- ✅ ECR images and repositories
- ✅ ECS cluster and services
- ✅ CloudFront distribution
- ✅ AgentCore agent
- ✅ All associated resources

**Time**: ~10-15 minutes

**⚠️ Warning**: Deletes Cognito User Pool and all user accounts.

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

Apache License 2.0

## 👥 Authors

Shashi Makkapati, Senthil Kamala Rathinam, Jacob Scheatzle
