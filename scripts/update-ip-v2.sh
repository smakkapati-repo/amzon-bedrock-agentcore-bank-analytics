#!/bin/bash
# Update allowed IP address for BankIQ+ v2.0

set -e

if [ -z "$1" ]; then
    echo "Usage: ./scripts/update-ip-v2.sh YOUR_NEW_IP"
    echo ""
    echo "Example: ./scripts/update-ip-v2.sh 1.2.3.4"
    echo ""
    echo "Current IP detection:"
    CURRENT_IP=$(curl -s https://checkip.amazonaws.com)
    echo "   Your current IP: $CURRENT_IP"
    echo ""
    read -p "Use this IP? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        NEW_IP=$CURRENT_IP
    else
        exit 1
    fi
else
    NEW_IP=$1
fi

NEW_IP_CIDR="${NEW_IP}/32"

echo "🔄 Updating BankIQ+ v2.0 IP Restriction"
echo "========================================"
echo ""
echo "New IP: $NEW_IP_CIDR"
echo ""

BACKEND_STACK="bankiq-v2-backend"

echo "Updating CloudFormation stack..."
aws cloudformation update-stack \
  --stack-name $BACKEND_STACK \
  --use-previous-template \
  --parameters ParameterKey=YourIPAddress,ParameterValue=$NEW_IP_CIDR \
  --capabilities CAPABILITY_NAMED_IAM

echo "⏳ Waiting for stack update to complete..."
aws cloudformation wait stack-update-complete --stack-name $BACKEND_STACK

echo "✅ IP address updated!"
echo ""
echo "New allowed IP: $NEW_IP_CIDR"
echo ""
echo "You can now access the API from this IP."
