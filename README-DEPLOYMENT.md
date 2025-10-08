# BankIQ+ One-Click Deployment Guide

## 🚀 Quick Deploy to AWS

Deploy the complete BankIQ+ platform with a single click using AWS CloudFormation.

### Prerequisites
- AWS Account with Bedrock access enabled
- Basic AWS permissions (EC2, IAM, VPC)

### One-Click Deployment

1. **Upload to GitHub** (if not already done):
   ```bash
   git add .
   git commit -m "BankIQ+ complete platform"
   git push origin main
   ```

2. **Deploy via CloudFormation**:
   - Go to AWS Console → CloudFormation
   - Click "Create Stack" → "With new resources"
   - Upload `deploy-template.yaml`
   - Fill parameters:
     - **InstanceType**: t3.medium (recommended)
     - **AllowedCIDR**: 0.0.0.0/0 (or restrict to your IP)

3. **Access Your Application**:
   - Stack Outputs will show the Application URL
   - Example: `http://ec2-xx-xx-xx-xx.compute-1.amazonaws.com`

### What Gets Deployed

- **EC2 Instance** (t3.medium) with:
  - React frontend (port 3000)
  - Flask backend (port 8001)
  - Nginx reverse proxy (port 80)
- **VPC & Security Groups**
- **IAM Role** with Bedrock permissions
- **Auto-startup services** for both frontend/backend

### Post-Deployment Setup

1. **Enable Bedrock Models** (one-time setup):
   ```bash
   # SSH to instance
   ssh -i your-key.pem ec2-user@your-instance-ip
   
   # Check if Bedrock models are enabled in AWS Console
   # Go to Bedrock → Model Access → Enable Claude models
   ```

2. **Verify Services**:
   ```bash
   sudo systemctl status bankiq-backend
   sudo systemctl status bankiq-frontend
   sudo systemctl status nginx
   ```

### Architecture

```
Internet → ALB/Nginx (Port 80) → React App (Port 3000)
                                ↓
                               Flask API (Port 8001) → AWS Bedrock
```

### Costs Estimate
- **EC2 t3.medium**: ~$30/month
- **Bedrock API calls**: Pay per use (~$0.01-0.10 per analysis)
- **Data transfer**: Minimal for typical usage

### Troubleshooting

**Backend not starting?**
```bash
sudo journalctl -u bankiq-backend -f
```

**Frontend not accessible?**
```bash
sudo journalctl -u bankiq-frontend -f
sudo systemctl restart nginx
```

**Bedrock permissions?**
- Ensure your AWS region has Bedrock enabled
- Check IAM role has BedrockFullAccess policy

### Customization

**Update the application**:
```bash
cd /opt/bankiq
git pull origin main
sudo systemctl restart bankiq-backend bankiq-frontend
```

**Change ports/config**:
- Edit `/etc/systemd/system/bankiq-*.service`
- Edit `/etc/nginx/conf.d/bankiq.conf`
- Restart services

### Security Notes

- Default setup allows access from anywhere (0.0.0.0/0)
- For production, restrict CIDR to your IP range
- Consider adding SSL/TLS certificate
- Monitor Bedrock usage for cost control

### Support

For issues:
1. Check CloudFormation stack events
2. SSH to instance and check service logs
3. Verify Bedrock model access in AWS Console

---

**🎉 Your BankIQ+ platform should be live and ready for banking analytics!**