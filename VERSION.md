# BankIQ+ Version History

## v1.0.0 - Local Development Mode (October 15, 2025)

### 🎉 Initial Release - Fully Functional Local Development

**Status:** ✅ Production Ready (Local Mode)

### Features
- ✅ Peer Analytics with Live FDIC Data
- ✅ Financial Reports (Live + Local modes)
- ✅ Bank Search (24 major banks + SEC EDGAR fallback)
- ✅ SEC Filings Retrieval (10-K, 10-Q)
- ✅ PDF Upload with Metadata Extraction
- ✅ AI-Powered Document Analysis
- ✅ CSV Data Upload and Analysis
- ✅ Real-time Chat with AI Agent

### Architecture
- **Frontend:** React on localhost:3000
- **Backend:** Node.js Express on localhost:3001
- **Agent:** Python AgentCore (subprocess)
- **AI Model:** Claude Sonnet 4.5 via AWS Bedrock
- **Storage:** AWS S3 for documents

### Components
- 1 AI Agent (12 tools)
- 8 API Endpoints (3 direct, 5 agent-powered)
- 2 Frontend Tabs
- Hybrid architecture (fast + intelligent)

### Known Limitations
- Runs locally only
- Requires 2 terminal windows
- No auto-scaling
- Manual startup required

---

## v2.0.0 - CloudFront Production Mode (Planned)

### 🚀 Cloud Deployment

**Status:** 🔄 In Development

### Planned Features
- ☐ Frontend on S3 + CloudFront
- ☐ Backend on AWS Lambda + API Gateway
- ☐ Auto-scaling
- ☐ Custom domain
- ☐ HTTPS/SSL
- ☐ CDN caching
- ☐ Production monitoring
- ☐ Automated deployments

### Architecture Changes
- **Frontend:** S3 + CloudFront (static hosting)
- **Backend:** Lambda + API Gateway (serverless)
- **Agent:** Lambda Layer (on-demand)
- **Database:** DynamoDB (optional)
- **Monitoring:** CloudWatch

---

## Version Strategy

### v1.x - Local Development
- v1.0.0 - Initial release
- v1.1.0 - Bug fixes and improvements
- v1.2.0 - New features (local mode)

### v2.x - Cloud Production
- v2.0.0 - Initial cloud deployment
- v2.1.0 - Performance optimizations
- v2.2.0 - New cloud features

### Branching Strategy
```
main (v1.0.0 - stable local)
  ↓
v1-local (v1.x development)
  ↓
v2-cloud (v2.x development)
```

---

## Rollback Strategy

### To revert from v2.0 to v1.0:
```bash
git checkout v1.0.0
# or
git checkout v1-local
```

### To switch between versions:
```bash
# Check current version
git describe --tags

# List all versions
git tag

# Switch to v1.0
git checkout v1.0.0

# Switch to v2.0 (when ready)
git checkout v2.0.0
```

---

*Last Updated: October 15, 2025*
