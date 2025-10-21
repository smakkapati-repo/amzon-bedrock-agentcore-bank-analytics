#!/bin/bash
set -e

echo "=========================================="
echo "Deploy AgentCore Agent"
echo "=========================================="

# Get script directory and navigate to backend
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "${SCRIPT_DIR}/../../backend"

# Set UTF-8 encoding
export PYTHONIOENCODING=utf-8
export LC_ALL=C.UTF-8

# Check if agentcore is installed
if ! command -v agentcore &> /dev/null; then
    echo "ERROR: agentcore CLI not found. Install: pip install bedrock-agentcore-starter-toolkit"
    exit 1
fi

# Clean up stale config
if [ -f ".bedrock_agentcore.yaml" ]; then
    echo "Removing stale config..."
    rm .bedrock_agentcore.yaml
fi

echo "Creating fresh config..."
agentcore configure --entrypoint bank_iq_agent_v1.py

# Deploy agent with local-build (cross-platform compatible)
echo "Deploying agent with local-build mode..."
PYTHONIOENCODING=utf-8 agentcore launch -a bank_iq_agent_v1 --local-build 2>&1 | tee /tmp/agent_deploy.log

# Extract agent ARN
AGENT_ARN=$(grep -oE 'arn:aws:bedrock-agentcore:[^[:space:]]+:runtime/bank_iq_agent_v1-[a-zA-Z0-9]+' /tmp/agent_deploy.log | head -1)

if [ -z "$AGENT_ARN" ]; then
    echo "ERROR: Failed to extract agent ARN"
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
echo "PHASE 1 COMPLETE"
echo "Agent ARN: $AGENT_ARN"
echo "Saved to: /tmp/agent_arn.txt"
echo ""
echo "Next: Run phase2-infrastructure.sh"
