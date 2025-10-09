#!/bin/bash

echo "Getting BankIQ+ Application URL..."
echo "=================================="

# Get the Application URL from CloudFormation stack
APP_URL=$(aws cloudformation describe-stacks \
  --stack-name banking-analytics \
  --query 'Stacks[0].Outputs[?OutputKey==`ApplicationURL`].OutputValue' \
  --output text 2>/dev/null)

if [ -z "$APP_URL" ]; then
  echo "❌ Could not find CloudFormation stack 'banking-analytics'"
  echo ""
  echo "Available stacks:"
  aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE --query 'StackSummaries[].StackName' --output table
  echo ""
  echo "If your stack has a different name, run:"
  echo "aws cloudformation describe-stacks --stack-name YOUR_STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==\`ApplicationURL\`].OutputValue' --output text"
else
  echo "✅ Your BankIQ+ Application URL:"
  echo ""
  echo "🌐 $APP_URL"
  echo ""
  echo "📋 Share this URL with your friend:"
  echo "   They should access: $APP_URL"
  echo "   NOT: http://localhost:3000"
  echo ""
  echo "🔒 Security Note:"
  echo "   Only your IP address can access this URL"
  echo "   Your friend needs to be on your network or you need to update the Security Group"
fi