# S3 Backup Setup for SEC Filings

## Overview
This setup creates an S3 bucket to store raw SEC filings as backup for the RAG system, providing resilience without container bloat.

## Deployment Steps

### 1. Deploy CloudFormation Stack
```bash
aws cloudformation create-stack \
  --stack-name banking-analytics \
  --template-body file://cloudformation-template.yaml \
  --parameters ParameterKey=YourIPAddress,ParameterValue=YOUR_IP_HERE \
  --capabilities CAPABILITY_IAM
```

### 2. Get S3 Bucket Name
```bash
aws cloudformation describe-stacks \
  --stack-name banking-analytics \
  --query 'Stacks[0].Outputs[?OutputKey==`SECFilingsBucket`].OutputValue' \
  --output text
```

### 3. Upload SEC Filings to S3
```bash
# Install dependencies
pip3 install boto3 requests

# Upload SEC data (takes 10-15 minutes)
python3 upload_sec_to_s3.py <bucket-name-from-step-2>
```

## How It Works

### Container Startup
1. **Try FAISS index first** (3.5 MB, instant load)
2. **If FAISS missing/corrupt**: Rebuild from S3 data
3. **If S3 fails**: Fall back to Live EDGAR API

### S3 Structure
```
bankiq-sec-filings-123456789-us-east-1/
├── JPMORGAN_CHASE/
│   ├── 2023/
│   │   ├── 10-K/
│   │   │   └── 0000019617-23-000123.txt
│   │   └── 10-Q/
│   │       ├── 0000019617-23-000456.txt
│   │       └── 0000019617-23-000789.txt
│   ├── 2024/
│   └── 2025/
├── BANK_OF_AMERICA/
└── ...
```

### Benefits
- **Container**: Stays lightweight (~500 MB)
- **Resilience**: Can rebuild FAISS if corrupted
- **Cost**: ~$15/month for 600 MB S3 storage
- **Performance**: FAISS index loads instantly
- **Backup**: Raw data preserved for analysis

### Costs
- **S3 Storage**: ~$0.023/GB/month = ~$15/month for 600 MB
- **S3 Requests**: ~$0.01/month for occasional rebuilds
- **Total**: ~$15/month for complete data backup

## Manual Operations

### Rebuild FAISS Index
If the container's FAISS index gets corrupted:
```bash
# Container will automatically rebuild from S3 on next startup
aws ecs update-service --cluster bankiq-secure-cluster \
  --service bankiq-secure-service --force-new-deployment
```

### Update S3 Data
```bash
# Re-run uploader to get latest filings
python3 upload_sec_to_s3.py <bucket-name>
```

### Check S3 Contents
```bash
aws s3 ls s3://<bucket-name> --recursive --human-readable
```

## Architecture Benefits

✅ **Best of both worlds**:
- Fast startup (FAISS index)
- Data resilience (S3 backup)
- Cost effective (~$15/month)
- No container bloat

✅ **Automatic fallback**:
- FAISS corrupted → Rebuild from S3
- S3 unavailable → Use Live EDGAR API
- Multiple layers of resilience