#!/bin/bash
set -e

STACK_NAME=${1:-bankiq}
REGION=${2:-us-east-1}

echo "=========================================="
echo "Deploy Backend (CodeBuild Version)"
echo "=========================================="

# Get agent ARN
if [ -f "/tmp/agent_arn.txt" ]; then
    AGENT_ARN=$(cat /tmp/agent_arn.txt)
    echo "Agent ARN: $AGENT_ARN"
else
    echo "ERROR: Agent ARN not found. Run phase2-agent.sh first."
    exit 1
fi

# Get infrastructure outputs
BACKEND_ECR=$(aws cloudformation describe-stacks --stack-name ${STACK_NAME}-infra --region $REGION --query 'Stacks[0].Outputs[?OutputKey==`BackendECR`].OutputValue' --output text)
echo "Backend ECR: $BACKEND_ECR"

# Create CodeBuild project for backend
echo "🚀 Creating CodeBuild project for backend..."

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Create CodeBuild project via CloudFormation
# Use portable temp directory
TEMP_DIR="$(pwd)/temp"
mkdir -p "$TEMP_DIR"

cat > "$TEMP_DIR/backend-codebuild.yaml" << EOF
AWSTemplateFormatVersion: '2010-09-09'
Description: 'CodeBuild project for BankIQ+ Backend'

Parameters:
  ProjectName:
    Type: String
    Default: ${STACK_NAME}
  
Resources:
  CodeBuildServiceRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub "\${ProjectName}-backend-codebuild-role"
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: codebuild.amazonaws.com
            Action: sts:AssumeRole
      Policies:
        - PolicyName: CodeBuildPolicy
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - logs:CreateLogGroup
                  - logs:CreateLogStream
                  - logs:PutLogEvents
                Resource: !Sub "arn:aws:logs:\${AWS::Region}:\${AWS::AccountId}:log-group:/aws/codebuild/*"
              - Effect: Allow
                Action:
                  - ecr:BatchCheckLayerAvailability
                  - ecr:GetDownloadUrlForLayer
                  - ecr:BatchGetImage
                  - ecr:GetAuthorizationToken
                  - ecr:PutImage
                  - ecr:InitiateLayerUpload
                  - ecr:UploadLayerPart
                  - ecr:CompleteLayerUpload
                Resource: "*"
              - Effect: Allow
                Action:
                  - s3:GetObject
                  - s3:GetObjectVersion
                Resource: "*"

  BackendCodeBuildProject:
    Type: AWS::CodeBuild::Project
    Properties:
      Name: !Sub "\${ProjectName}-backend-builder"
      ServiceRole: !GetAtt CodeBuildServiceRole.Arn
      Artifacts:
        Type: NO_ARTIFACTS
      Environment:
        Type: LINUX_CONTAINER
        ComputeType: BUILD_GENERAL1_MEDIUM
        Image: aws/codebuild/amazonlinux2-x86_64-standard:5.0
        PrivilegedMode: true
        EnvironmentVariables:
          - Name: AWS_DEFAULT_REGION
            Value: !Ref AWS::Region
          - Name: AWS_ACCOUNT_ID
            Value: !Ref AWS::AccountId
          - Name: IMAGE_REPO_NAME
            Value: ${STACK_NAME}-backend-prod
          - Name: IMAGE_TAG
            Value: latest
      Source:
        Type: S3
        BuildSpec: |
          version: 0.2
          phases:
            pre_build:
              commands:
                - echo Logging in to Amazon ECR...
                - aws ecr get-login-password --region \$AWS_DEFAULT_REGION | docker login --username AWS --password-stdin \$AWS_ACCOUNT_ID.dkr.ecr.\$AWS_DEFAULT_REGION.amazonaws.com
            build:
              commands:
                - echo Build started on \`date\`
                - echo Building the Docker image...
                - docker build -f Dockerfile.backend -t \$IMAGE_REPO_NAME:\$IMAGE_TAG .
                - docker tag \$IMAGE_REPO_NAME:\$IMAGE_TAG \$AWS_ACCOUNT_ID.dkr.ecr.\$AWS_DEFAULT_REGION.amazonaws.com/\$IMAGE_REPO_NAME:\$IMAGE_TAG
            post_build:
              commands:
                - echo Build completed on \`date\`
                - echo Pushing the Docker image...
                - docker push \$AWS_ACCOUNT_ID.dkr.ecr.\$AWS_DEFAULT_REGION.amazonaws.com/\$IMAGE_REPO_NAME:\$IMAGE_TAG

Outputs:
  CodeBuildProject:
    Description: CodeBuild project name
    Value: !Ref BackendCodeBuildProject
EOF

# Deploy CodeBuild stack
aws cloudformation create-stack \
  --stack-name ${STACK_NAME}-backend-codebuild \
  --template-body file://"$TEMP_DIR/backend-codebuild.yaml" \
  --parameters ParameterKey=ProjectName,ParameterValue=$STACK_NAME \
  --capabilities CAPABILITY_NAMED_IAM \
  --region $REGION

echo "⏳ Waiting for CodeBuild project creation..."
aws cloudformation wait stack-create-complete --stack-name ${STACK_NAME}-backend-codebuild --region $REGION

# Upload source to S3
echo "📦 Uploading backend source to S3..."
cd "${SCRIPT_DIR}/../../backend"

# Create source zip
zip -r "$TEMP_DIR/backend-source.zip" . -x "*.git*" "node_modules/*" ".bedrock_agentcore.yaml"

# Upload to S3 (use existing bucket from infrastructure)
S3_BUCKET=$(aws cloudformation describe-stacks --stack-name ${STACK_NAME}-infra --region $REGION --query 'Stacks[0].Outputs[?OutputKey==`FrontendBucket`].OutputValue' --output text)
aws s3 cp "$TEMP_DIR/backend-source.zip" s3://$S3_BUCKET/backend-source.zip

# Start CodeBuild
echo "🚀 Starting CodeBuild..."
BUILD_ID=$(aws codebuild start-build \
  --project-name ${STACK_NAME}-backend-builder \
  --source-location s3://$S3_BUCKET/backend-source.zip \
  --query 'build.id' --output text)

echo "📋 CodeBuild started: $BUILD_ID"
echo "⏳ Waiting for build to complete..."

# Wait for build to complete
aws codebuild batch-get-builds --ids $BUILD_ID --query 'builds[0].buildStatus' --output text
while [ "$(aws codebuild batch-get-builds --ids $BUILD_ID --query 'builds[0].buildStatus' --output text)" = "IN_PROGRESS" ]; do
  echo "Building..."
  sleep 30
done

BUILD_STATUS=$(aws codebuild batch-get-builds --ids $BUILD_ID --query 'builds[0].buildStatus' --output text)
if [ "$BUILD_STATUS" != "SUCCEEDED" ]; then
  echo "❌ CodeBuild failed: $BUILD_STATUS"
  exit 1
fi

echo "✅ Backend image built and pushed via CodeBuild"

# Deploy backend stack (same as original)
echo "🚀 Deploying backend stack..."
aws cloudformation create-stack \
  --stack-name ${STACK_NAME}-backend \
  --template-body file://${SCRIPT_DIR}/../templates/backend.yaml \
  --parameters \
    ParameterKey=ProjectName,ParameterValue=$STACK_NAME \
    ParameterKey=Environment,ParameterValue=prod \
    ParameterKey=AgentArn,ParameterValue="$AGENT_ARN" \
  --capabilities CAPABILITY_IAM \
  --region $REGION

echo "⏳ Waiting for backend deployment (7-10 minutes)..."
aws cloudformation wait stack-create-complete --stack-name ${STACK_NAME}-backend --region $REGION

# Get backend URL
BACKEND_URL=$(aws cloudformation describe-stacks --stack-name ${STACK_NAME}-backend --region $REGION --query 'Stacks[0].Outputs[?OutputKey==`BackendUrl`].OutputValue' --output text)

echo ""
echo "✅ PHASE 3 COMPLETE (CodeBuild Version)"
echo "Backend URL: $BACKEND_URL"
echo ""
echo "Next: Run phase4-frontend.sh"

# Cleanup temp directory
rm -rf "$TEMP_DIR"