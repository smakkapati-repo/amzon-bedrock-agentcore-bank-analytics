#!/bin/bash

# Script to reset GitHub repo and make current code the initial commit

echo "🔄 Resetting repository to make this the initial commit..."

# Remove existing git history
rm -rf .git

# Initialize new git repository
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: BankIQ+ Banking Analytics Platform

- React frontend with Material-UI
- Flask backend with AWS Bedrock integration
- Peer analytics with 3 modes (Live/Upload/RAG)
- Financial reports analyzer with SEC EDGAR API
- One-click CloudFormation deployment
- Support for 29+ major US banks"

# Add remote (replace with your actual repo URL)
git remote add origin https://github.com/AWS-Samples-GenAI-FSI/peer-bank-analytics.git

# Force push to overwrite existing history
git push -u origin main --force

echo "✅ Repository reset complete! All previous commits removed."
echo "🚀 Your BankIQ+ platform is now the initial commit."