#!/bin/bash
set -e

ROLE_NAME="AmazonBedrockAgentCoreSDKRuntime-us-east-1-491c2288f3"
BUCKET_NAME="${1:-bankiq-uploaded-docs-prod}"

echo "Adding S3 permissions to AgentCore role..."

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
  }"

echo "✅ S3 permissions added to $ROLE_NAME"
