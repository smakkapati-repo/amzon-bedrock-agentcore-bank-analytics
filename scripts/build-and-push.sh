#!/bin/bash

# BankIQ+ - Build and Push to ECR Public
# Run this script to build and push your image for friends to use

set -e

# Configuration
REPO_NAME="bankiq-platform"
IMAGE_TAG="latest"
AWS_REGION="us-east-1"

echo "🏗️  Building BankIQ+ Docker image..."

# Build the image for x86_64 architecture (ECS Fargate compatible)
docker build --platform linux/amd64 -t $REPO_NAME .

echo "🔍 Getting ECR Public login..."

# Login to ECR Public (us-east-1 only for public)
aws ecr-public get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin public.ecr.aws

echo "📦 Creating ECR repository (if it doesn't exist)..."

# Create repository (ignore error if exists)
aws ecr-public create-repository --repository-name $REPO_NAME --region $AWS_REGION 2>/dev/null || echo "Repository already exists"

# Get the repository URI
REPO_URI=$(aws ecr-public describe-repositories --repository-names $REPO_NAME --region $AWS_REGION --query 'repositories[0].repositoryUri' --output text)

echo "🏷️  Tagging image as $REPO_URI:$IMAGE_TAG"

# Tag the image
docker tag $REPO_NAME:latest $REPO_URI:$IMAGE_TAG

echo "🚀 Pushing to ECR Public..."

# Push the image
docker push $REPO_URI:$IMAGE_TAG

echo "✅ Success! Your image is now available at:"
echo "   $REPO_URI:$IMAGE_TAG"
echo ""
echo "🎯 Update your Fargate template with this image URI"
echo "💡 Your friends can now deploy instantly using the Fargate template!"