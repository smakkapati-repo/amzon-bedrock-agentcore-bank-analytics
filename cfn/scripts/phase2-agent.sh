#!/bin/bash
set -e

echo "=========================================="
echo "Deploy AgentCore Agent"
echo "=========================================="

# Get script directory and navigate to backend
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "${SCRIPT_DIR}/../../backend"

# Set UTF-8 encoding and force us-west-2 region for AgentCore
export PYTHONIOENCODING=utf-8
export LC_ALL=C.UTF-8
export AWS_DEFAULT_REGION=us-west-2
echo "🌍 Forcing region to us-west-2 for AgentCore deployment"

# Check if agentcore is installed
if ! command -v agentcore &> /dev/null; then
    echo "ERROR: agentcore CLI not found. Install: pip install bedrock-agentcore-starter-toolkit"
    exit 1
fi

# Create IAM role if it doesn't exist
echo "Creating IAM role for AgentCore..."
aws iam create-role --role-name bank_iq_agent_v1 --assume-role-policy-document '{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "bedrock-agentcore.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}' 2>/dev/null || echo "Role already exists or creation failed"

# Attach basic permissions
aws iam attach-role-policy --role-name bank_iq_agent_v1 --policy-arn arn:aws:iam::aws:policy/service-role/AmazonBedrockAgentCoreServiceRolePolicy 2>/dev/null || echo "Policy already attached"

# Add ECR permissions
aws iam put-role-policy --role-name bank_iq_agent_v1 --policy-name ECRAccess --policy-document '{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchGetImage",
        "ecr:GetDownloadUrlForLayer"
      ],
      "Resource": "*"
    }
  ]
}' 2>/dev/null || echo "ECR policy already attached"

echo "Waiting for IAM role propagation..."
sleep 10

# Check if config exists, if not create it
if [ ! -f ".bedrock_agentcore.yaml" ]; then
    echo "Config file not found, creating..."
    printf "bank_iq_agent_v1\n\n\n\n\n\n\n\n" | agentcore configure --entrypoint bank_iq_agent_v1.py
    echo "Config file created"
fi

# Check if agent already exists
echo "Checking agent status..."
AGENT_ARN=""

# Try to get ARN from agentcore status first
if agentcore status 2>/dev/null | grep -q "Agent ARN:"; then
    AGENT_ARN=$(agentcore status 2>/dev/null | grep "Agent ARN:" -A 1 | tail -1 | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//' | sed 's/│//g')
    echo "✅ Found existing agent: $AGENT_ARN"
else
    # Deploy new agent
    echo "Deploying new agent..."
    PYTHONIOENCODING=utf-8 agentcore launch -a bank_iq_agent_v1 --auto-update-on-conflict 2>&1 | tee /tmp/agent_deploy.log
    
    # Extract agent ARN from deployment log
    AGENT_ARN=$(grep -oE 'arn:aws:bedrock-agentcore:[^[:space:]]+:runtime/bank_iq_agent_v1-[a-zA-Z0-9]+' /tmp/agent_deploy.log | head -1)
    
    if [ -z "$AGENT_ARN" ]; then
        # Try to get from status after deployment
        sleep 5
        if agentcore status 2>/dev/null | grep -q "Agent ARN:"; then
            AGENT_ARN=$(agentcore status 2>/dev/null | grep "Agent ARN:" -A 1 | tail -1 | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//' | sed 's/│//g')
            echo "✅ Extracted ARN from status: $AGENT_ARN"
        fi
    fi
fi

if [ -z "$AGENT_ARN" ]; then
    echo "ERROR: Failed to extract agent ARN"
    echo "Try running: agentcore status"
    exit 1
fi

# Save agent ARN for next phase
echo "$AGENT_ARN" > /tmp/agent_arn.txt

# Add S3 permissions to AgentCore role
echo "Adding S3 permissions to AgentCore role..."
ROLE_NAME="AmazonBedrockAgentCoreSDKRuntime-us-east-1-491c2288f3"
BUCKET_NAME="bankiq-uploaded-docs-prod"

aws iam put-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-name S3ReadAccess \
  --policy-document "{
    \"Version\": \"2012-10-17\",
    \"Statement\": [
      {
        \"Effect\": \"Allow\",
        \"Action\": [
          \"s3:GetObject\",
          \"s3:ListBucket\"
        ],
        \"Resource\": [
          \"arn:aws:s3:::${BUCKET_NAME}\",
          \"arn:aws:s3:::${BUCKET_NAME}/*\"
        ]
      }
    ]
  }" 2>/dev/null || echo "WARNING: S3 permissions already exist or failed to add"

echo ""
echo "✅ PHASE 2 COMPLETE"
echo "Agent ARN: $AGENT_ARN"
echo "Saved to: /tmp/agent_arn.txt"
echo ""
echo "Next: Run phase3-backend-codebuild.sh"
