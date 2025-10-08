# BankIQ+ Deployment Guide

## 🚀 For You (One-Time Setup)

### Step 1: Build and Push Image to ECR Public
```bash
# Make script executable
chmod +x build-and-push.sh

# Build and push (requires AWS CLI configured)
./build-and-push.sh
```

### Step 2: Update Fargate Template
After running the script, update `fargate-template.yaml`:
```yaml
Image: public.ecr.aws/YOUR_ACTUAL_ALIAS/bankiq-platform:latest
```

### Step 3: Commit to GitHub
```bash
git add .
git commit -m "Add containerized deployment with ECR Public"
git push origin main
```

## 🎯 For Your Friends (One-Click Deploy)

### Prerequisites
- AWS Account with Bedrock access enabled
- Go to AWS Console → Bedrock → Model Access → Enable Claude models

### Deployment Steps
1. **Get Your IP Address**: Visit [whatismyip.com](https://whatismyip.com)

2. **Deploy via CloudFormation**:
   - Go to AWS Console → CloudFormation
   - Click "Create Stack" → "With new resources"
   - Upload `fargate-template.yaml`
   - Enter your IP address
   - Click "Create Stack"

3. **Wait 5 minutes** for deployment to complete

4. **Access Application**: Use the URL from CloudFormation Outputs

## 📊 What They Get

- **Complete BankIQ+ Platform** running on AWS Fargate
- **29+ Banks** available for analysis
- **3 Analysis Modes**: RAG, Live EDGAR, Local Upload
- **AI-Powered Insights** with AWS Bedrock Claude
- **Professional UI** with all features
- **Auto-scaling** and **High Availability**

## 💰 Cost Estimate

- **Fargate**: ~$15-20/month (only when running)
- **Load Balancer**: ~$18/month
- **Bedrock API**: ~$0.01-0.10 per analysis
- **Total**: ~$35/month for active usage

## 🔧 Troubleshooting

**"Stack creation failed":**
- Ensure Bedrock models are enabled in your region
- Check your IP address is correct
- Verify you have sufficient AWS permissions

**"Application not loading":**
- Wait 5-10 minutes for full deployment
- Check CloudWatch logs: `/ecs/bankiq`
- Verify Load Balancer health checks are passing

**"Bedrock access denied":**
- Go to AWS Console → Bedrock → Model Access
- Enable Claude 3 Haiku and Sonnet models
- Wait 5 minutes for activation

## 🔄 Updates

When you update the platform:
1. Run `./build-and-push.sh` to push new image
2. Friends can redeploy CloudFormation stack to get updates
3. Or use ECS service update for zero-downtime updates

---

**🎉 Your friends now have enterprise-grade banking analytics in 5 minutes!**