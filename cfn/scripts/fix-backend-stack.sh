#!/bin/bash
set -e

STACK_NAME=${1:-bankiq}
REGION=${2:-us-east-1}

echo "🔧 Fixing existing backend CodeBuild stack..."

# Check if stack exists
if aws cloudformation describe-stacks --stack-name ${STACK_NAME}-backend-codebuild --region $REGION >/dev/null 2>&1; then
    echo "Stack exists. Deleting..."
    aws cloudformation delete-stack --stack-name ${STACK_NAME}-backend-codebuild --region $REGION
    echo "⏳ Waiting for stack deletion..."
    aws cloudformation wait stack-delete-complete --stack-name ${STACK_NAME}-backend-codebuild --region $REGION
    echo "✅ Stack deleted successfully"
else
    echo "Stack does not exist"
fi

echo "✅ Ready to run phase3-backend-codebuild.sh"