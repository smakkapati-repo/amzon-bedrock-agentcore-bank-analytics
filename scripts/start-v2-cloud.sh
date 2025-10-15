#!/bin/bash
# Start v2.0 Cloud Development

echo "🚀 Starting BankIQ+ v2.0 Cloud Development"
echo "=========================================="
echo ""

# Check if v1.0.0 tag exists
if ! git tag | grep -q "v1.0.0"; then
    echo "❌ Error: v1.0.0 tag not found"
    echo "Please run ./scripts/release-v1.sh first"
    exit 1
fi

echo "✅ v1.0.0 tag found"
echo ""

# Create v2-cloud branch from main
echo "Creating v2-cloud branch from main..."
git checkout main
git checkout -b v2-cloud 2>/dev/null || git checkout v2-cloud

echo "✅ On v2-cloud branch"
echo ""

# Create v2.0 planning document
cat > docs/V2_CLOUD_PLAN.md << 'EOF'
# BankIQ+ v2.0 - Cloud Deployment Plan

## Objective
Deploy BankIQ+ to AWS cloud infrastructure for production use.

## Architecture Changes

### Frontend
- **Current (v1.0):** React Dev Server (localhost:3000)
- **Target (v2.0):** S3 + CloudFront
  - Static build: `npm run build`
  - S3 bucket: `bankiq-frontend`
  - CloudFront distribution
  - Custom domain (optional)

### Backend
- **Current (v1.0):** Node.js Express (localhost:3001)
- **Target (v2.0):** AWS Lambda + API Gateway
  - Serverless functions
  - API Gateway REST API
  - Auto-scaling
  - Pay-per-use pricing

### Agent
- **Current (v1.0):** Python subprocess
- **Target (v2.0):** Lambda Layer
  - Packaged with dependencies
  - Invoked by backend Lambda
  - Shared across functions

### Storage
- **Current (v1.0):** S3 (documents only)
- **Target (v2.0):** S3 + DynamoDB
  - S3: Documents, static assets
  - DynamoDB: Session data, cache (optional)

## Deployment Steps

### Phase 1: Frontend (S3 + CloudFront)
1. Build React app: `npm run build`
2. Create S3 bucket
3. Upload build files
4. Configure CloudFront
5. Update CORS settings
6. Test frontend

### Phase 2: Backend (Lambda + API Gateway)
1. Package Node.js backend
2. Create Lambda functions
3. Set up API Gateway
4. Configure environment variables
5. Test endpoints

### Phase 3: Agent (Lambda Layer)
1. Package Python dependencies
2. Create Lambda Layer
3. Attach to backend Lambda
4. Test agent invocation

### Phase 4: Integration
1. Update frontend API URLs
2. Configure CORS
3. Test end-to-end
4. Performance testing
5. Security review

## Rollback Plan

### If v2.0 has issues:
```bash
# Revert to v1.0
git checkout v1.0.0

# Or use v1-local for latest v1.x
git checkout v1-local

# Restart local servers
cd backend && node server.js &
cd frontend && npm start
```

## Success Criteria
- [ ] Frontend loads from CloudFront
- [ ] All API endpoints work
- [ ] Agent responds correctly
- [ ] PDF upload works
- [ ] Performance < 3s for most operations
- [ ] Cost < $50/month for moderate use

## Timeline
- Week 1: Frontend deployment
- Week 2: Backend deployment
- Week 3: Agent integration
- Week 4: Testing and optimization

---

*Created: October 15, 2025*
EOF

echo "✅ Created docs/V2_CLOUD_PLAN.md"
echo ""

echo "📊 Current Status:"
echo "  Version: v2.0.0-dev"
echo "  Branch: v2-cloud"
echo "  Base: v1.0.0"
echo ""

echo "📝 Next Steps:"
echo "  1. Review: docs/V2_CLOUD_PLAN.md"
echo "  2. Start with frontend: deployment/frontend-s3-cloudfront.yaml"
echo "  3. Then backend: deployment/backend-lambda.yaml"
echo "  4. Test thoroughly before tagging v2.0.0"
echo ""

echo "🔄 To switch back to v1.0:"
echo "  git checkout v1.0.0"
echo "  # or"
echo "  git checkout v1-local"
echo ""

echo "✅ v2.0 development environment ready!"
