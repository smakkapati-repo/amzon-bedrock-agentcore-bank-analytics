# BankIQ+ v2.0 - Cloud Deployment Guide

## 🚀 Overview

BankIQ+ v2.0 deploys the application to AWS cloud infrastructure:
- **Frontend:** S3 + CloudFront (Public UI)
- **Backend:** Lambda + API Gateway (IP Restricted)
- **Agent:** Lambda Function (Python + AgentCore)

## 🔐 Security Model

```
CloudFront (Public)
  ↓ Anyone can see the UI
API Gateway (IP Restricted)
  ↓ Only YOUR IP can call APIs
Lambda Functions
  ↓
AWS Bedrock + S3
```

**Result:** UI is public but useless without API access from your IP!

---

## 📋 Prerequisites

1. **AWS Account** with:
   - Bedrock access (Claude Sonnet 4.5)
   - S3 bucket: `bankiq-uploaded-docs`
   - IAM permissions for CloudFormation, Lambda, API Gateway, S3, CloudFront

2. **AWS CLI** configured:
   ```bash
   aws configure
   ```

3. **Node.js 18+** and **Python 3.11+**

4. **v1.0 Tagged:**
   ```bash
   git describe --tags  # Should show v1.0.0
   ```

---

## 🚀 Deployment

### One-Command Deployment:
```bash
./scripts/deploy-v2.sh
```

This will:
1. ✅ Detect your IP address
2. ✅ Deploy Frontend (S3 + CloudFront)
3. ✅ Deploy Backend (Lambda + API Gateway with IP restriction)
4. ✅ Build and upload React app
5. ✅ Package and deploy Lambda functions
6. ✅ Output CloudFront URL

**Time:** ~15-20 minutes

---

## 📊 What Gets Deployed

### Frontend Stack (`bankiq-v2-frontend`)
- **S3 Bucket:** Private (CloudFront OAI only)
- **CloudFront Distribution:** Public HTTPS URL
- **Custom Error Pages:** SPA routing support

### Backend Stack (`bankiq-v2-backend`)
- **Backend Lambda:** Node.js 18 (Express wrapper)
- **Agent Lambda:** Python 3.11 (AgentCore)
- **API Gateway:** REST API with IP restriction
- **IAM Roles:** Bedrock, S3, Lambda permissions

---

## 🔧 Post-Deployment

### Access Your App:
```
https://d1234567890.cloudfront.net
```

### Login:
- Username: `admin`
- Password: `bankiq2024`

### Update Your IP:
```bash
./scripts/update-ip-v2.sh 1.2.3.4
```

---

## 🔄 Rollback to v1.0

If v2.0 has issues:

```bash
# Switch to v1.0
git checkout v1.0.0

# Start local servers
cd backend && node server.js &
cd frontend && npm start

# Access at http://localhost:3000
```

**Everything works exactly as before!** ✅

---

## 📝 Architecture Differences

| Component | v1.0 (Local) | v2.0 (Cloud) |
|-----------|--------------|--------------|
| **Frontend** | localhost:3000 | CloudFront URL |
| **Backend** | localhost:3001 | API Gateway |
| **Agent** | Subprocess | Lambda Function |
| **Startup** | Manual (2 terminals) | Automatic |
| **Access** | Local only | Public URL |
| **Scaling** | Single instance | Auto-scaling |
| **Cost** | $0 | ~$20-50/month |

---

## 💰 Cost Estimate

### Monthly Costs (Moderate Use):
- **CloudFront:** $1-5 (data transfer)
- **S3:** $1-2 (storage + requests)
- **Lambda:** $10-20 (compute time)
- **API Gateway:** $3-5 (API calls)
- **Bedrock:** $10-30 (Claude API calls)

**Total:** ~$25-60/month

### Free Tier Eligible:
- Lambda: 1M requests/month free
- API Gateway: 1M requests/month free (first 12 months)
- S3: 5GB storage free (first 12 months)

---

## 🔐 Security Features

### 1. S3 Bucket
- ✅ Private (no public access)
- ✅ CloudFront OAI only
- ✅ Versioning enabled

### 2. CloudFront
- ✅ HTTPS only
- ✅ HTTP/2 and HTTP/3
- ✅ Compression enabled

### 3. API Gateway
- ✅ IP whitelist (your IP only)
- ✅ CORS configured
- ✅ Resource policy

### 4. Lambda
- ✅ IAM roles (least privilege)
- ✅ Environment variables
- ✅ CloudWatch logging

---

## 🛠️ Maintenance

### Update Frontend:
```bash
cd frontend
npm run build
aws s3 sync build/ s3://bankiq-v2-frontend-ACCOUNT_ID/ --delete
aws cloudfront create-invalidation --distribution-id DIST_ID --paths "/*"
```

### Update Backend:
```bash
cd backend
zip -r lambda.zip lambda.js node_modules/
aws lambda update-function-code --function-name FUNCTION_NAME --zip-file fileb://lambda.zip
```

### Update Agent:
```bash
cd backend
zip -r agent.zip bank_iq_agent_v1.py python/
aws lambda update-function-code --function-name AGENT_FUNCTION_NAME --zip-file fileb://agent.zip
```

### View Logs:
```bash
# Backend logs
aws logs tail /aws/lambda/BankIQ-v2-Backend --follow

# Agent logs
aws logs tail /aws/lambda/BankIQ-v2-Agent --follow
```

---

## 🐛 Troubleshooting

### Issue: "403 Forbidden" on API calls
**Solution:** Your IP changed. Update it:
```bash
./scripts/update-ip-v2.sh
```

### Issue: CloudFront shows old version
**Solution:** Invalidate cache:
```bash
aws cloudfront create-invalidation --distribution-id DIST_ID --paths "/*"
```

### Issue: Lambda timeout
**Solution:** Increase timeout in CloudFormation template (currently 300s for agent)

### Issue: "Module not found" in Lambda
**Solution:** Reinstall dependencies and repackage:
```bash
cd backend
rm -rf node_modules
npm install --production
zip -r lambda.zip lambda.js node_modules/
```

---

## 📚 Additional Resources

- **v1.0 Docs:** See `VERSIONING.md`
- **Architecture:** See `docs/SYSTEM_ARCHITECTURE.md`
- **Deployment Details:** See `docs/DEPLOYMENT_COMPLETE.md`

---

## ✅ Checklist

Before deploying v2.0:

- [ ] v1.0 is tagged and working
- [ ] AWS CLI configured
- [ ] Bedrock access enabled
- [ ] S3 bucket `bankiq-uploaded-docs` exists
- [ ] On `v2-cloud` branch
- [ ] Know your IP address

After deploying v2.0:

- [ ] CloudFront URL accessible
- [ ] Can login to app
- [ ] API calls work from your IP
- [ ] All features functional
- [ ] Can rollback to v1.0 if needed

---

## 🎯 Summary

**v2.0 gives you:**
- ✅ Public CloudFront URL
- ✅ Auto-scaling serverless backend
- ✅ IP-restricted API (secure)
- ✅ Same features as v1.0
- ✅ Easy rollback to v1.0

**Deploy now:**
```bash
./scripts/deploy-v2.sh
```

---

*Version: 2.0.0*  
*Last Updated: October 15, 2025*
