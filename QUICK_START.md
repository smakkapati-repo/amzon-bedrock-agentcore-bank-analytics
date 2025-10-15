# BankIQ+ Quick Start Guide

## 🚀 Access the Platform

**URL**: https://d3u1t8d6jalnze.cloudfront.net

**Login**:
- Username: `admin`
- Password: `bankiq2024`

---

## 💡 What You Can Do

### 1. Peer Bank Analytics
Compare banking performance metrics across major US banks:
- Select a base bank (e.g., JPMorgan Chase)
- Choose up to 3 peer banks
- Pick a metric (ROA, ROE, NIM, etc.)
- Click "Analyze" for AI-powered insights

**Features**:
- ✅ Real-time AI analysis
- ✅ Interactive charts
- ✅ Quarterly trends
- ✅ Upload custom CSV data

### 2. Financial Reports
Analyze SEC filings and financial documents:
- Search for any publicly traded bank
- Access live 10-K and 10-Q filings
- Chat with AI about the documents
- Upload your own PDF files
- Generate comprehensive reports

**Features**:
- ✅ Live SEC EDGAR integration
- ✅ AI-powered document chat
- ✅ Full report generation
- ✅ Source citations

---

## 🎯 Sample Questions

### Peer Analytics
- "Compare JPMorgan Chase vs Bank of America on ROE"
- "How does Wells Fargo's NIM compare to peers?"
- "Analyze Citigroup's capital ratios"

### Financial Reports
- "What are the key risk factors?"
- "How is the financial performance?"
- "What are the main revenue sources?"
- "Any regulatory concerns?"

---

## 🔧 For Developers

### Start Backend Locally
```bash
cd backend
node server.js
```

### Deploy Frontend
```bash
cd frontend
npm run build
aws s3 sync build/ s3://bankiq-frontend-164543933824/ --delete
aws cloudfront create-invalidation --distribution-id EYKLKZYWGDQ8X --paths "/*"
```

### Test AgentCore
```bash
cd backend
agentcore invoke '{"prompt": "Your question here"}'
```

---

## 📞 Support

For issues or questions, check:
- [Full Documentation](./docs/DEPLOYMENT_COMPLETE.md)
- [Architecture Plan](./docs/ARCHITECTURE_PLAN.md)
- CloudWatch Logs for debugging

---

**Enjoy your AI-powered banking analytics!** 🏦✨
