#!/bin/bash
# Release v1.0.0 - Local Development Mode

echo "🎉 Creating BankIQ+ v1.0.0 Release"
echo "=================================="
echo ""

# Check if on main branch
BRANCH=$(git branch --show-current)
if [ "$BRANCH" != "main" ]; then
    echo "❌ Error: Must be on main branch"
    echo "Current branch: $BRANCH"
    exit 1
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "📝 Uncommitted changes detected"
    echo ""
    
    # Add all files
    echo "Adding all files..."
    git add .
    
    # Show what will be committed
    echo ""
    echo "Files to be committed:"
    git status --short
    echo ""
    
    # Commit
    read -p "Enter commit message (or press Enter for default): " COMMIT_MSG
    if [ -z "$COMMIT_MSG" ]; then
        COMMIT_MSG="Release v1.0.0 - Local Development Mode

Features:
- Peer Analytics with Live FDIC Data
- Financial Reports (Live + Local modes)
- Bank Search with SEC EDGAR integration
- PDF Upload with AI Analysis
- CSV Data Analysis
- Hybrid architecture (direct + agent endpoints)

Components:
- 1 AI Agent (12 tools)
- 8 API Endpoints
- React Frontend + Node.js Backend + Python Agent"
    fi
    
    git commit -m "$COMMIT_MSG"
    echo "✅ Changes committed"
else
    echo "✅ No uncommitted changes"
fi

echo ""
echo "Creating v1.0.0 tag..."
git tag -a v1.0.0 -m "Release v1.0.0 - Local Development Mode

Fully functional local development version with:
- Peer Analytics
- Financial Reports
- AI-powered document analysis
- Hybrid architecture

Ready for production use in local mode."

echo "✅ Tag v1.0.0 created"
echo ""

# Create v1-local branch for future v1.x development
echo "Creating v1-local branch..."
git branch v1-local 2>/dev/null || echo "Branch v1-local already exists"
echo "✅ Branch v1-local ready"
echo ""

echo "📊 Version Summary:"
echo "  Current: v1.0.0"
echo "  Branch: main"
echo "  Dev Branch: v1-local"
echo ""

echo "🎯 Next Steps:"
echo "  1. Push to remote: git push origin main --tags"
echo "  2. Push v1-local: git push origin v1-local"
echo "  3. Start v2.0 development: git checkout -b v2-cloud"
echo ""

echo "✅ Release v1.0.0 complete!"
echo ""
echo "To verify:"
echo "  git describe --tags"
echo "  git log --oneline -5"
