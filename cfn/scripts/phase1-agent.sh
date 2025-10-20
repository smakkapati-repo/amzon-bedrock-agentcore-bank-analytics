#!/bin/bash
set -e

echo "=========================================="
echo "Deploy AgentCore Agent"
echo "=========================================="

# Get script directory and navigate to backend
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "${SCRIPT_DIR}/../../backend"

# Check if agentcore is installed
if ! command -v agentcore &> /dev/null; then
    echo "❌ agentcore CLI not found. Install: pip install bedrock-agentcore-starter-toolkit"
    exit 1
fi

# Check if config exists, if not create it
if [ ! -f ".bedrock_agentcore.yaml" ]; then
    echo "⚙️  Config file not found, creating..."
    agentcore configure --entrypoint bank_iq_agent_v1.py
    echo "✅ Config file created"
fi

# Deploy agent
echo "🚀 Deploying agent..."
agentcore launch -a bank_iq_agent_v1 | tee /tmp/agent_deploy.log

# Extract agent ARN
AGENT_ARN=$(grep -oE 'arn:aws:bedrock-agentcore:[^[:space:]]+:runtime/bank_iq_agent_v1-[a-zA-Z0-9]+' /tmp/agent_deploy.log | head -1)

if [ -z "$AGENT_ARN" ]; then
    echo "❌ Failed to extract agent ARN"
    exit 1
fi

# Save agent ARN for next phase
echo "$AGENT_ARN" > /tmp/agent_arn.txt

# Add S3 permissions to AgentCore role
echo "🔐 Adding S3 permissions to AgentCore role..."
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
  }" 2>/dev/null || echo "⚠️  S3 permissions already exist or failed to add"

echo ""
echo "✅ PHASE 1 COMPLETE"
echo "Agent ARN: $AGENT_ARN"
echo "Saved to: /tmp/agent_arn.txt"
echo ""
echo "Next: Run phase2-infrastructure.sh"
