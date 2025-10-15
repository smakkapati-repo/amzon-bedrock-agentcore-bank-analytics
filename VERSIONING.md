# BankIQ+ Version Management Guide

## 📦 Current Version: v1.0.0 (Local Mode)

This guide explains how to manage versions and safely transition between v1.0 (local) and v2.0 (cloud).

---

## 🎯 Version Strategy

### v1.0 - Local Development Mode
- **Status:** ✅ Stable, Production Ready
- **Environment:** Local (localhost:3000, localhost:3001)
- **Use Case:** Development, testing, local demos
- **Branch:** `v1-local`
- **Tag:** `v1.0.0`

### v2.0 - Cloud Production Mode
- **Status:** 🔄 In Development
- **Environment:** AWS (S3, CloudFront, Lambda)
- **Use Case:** Production deployment, public access
- **Branch:** `v2-cloud`
- **Tag:** `v2.0.0` (when ready)

---

## 🚀 Quick Start

### Release v1.0 (First Time)
```bash
# Run the release script
./scripts/release-v1.sh

# This will:
# 1. Commit all changes
# 2. Create v1.0.0 tag
# 3. Create v1-local branch
# 4. Prepare for v2.0 development
```

### Start v2.0 Development
```bash
# Run the v2 setup script
./scripts/start-v2-cloud.sh

# This will:
# 1. Create v2-cloud branch
# 2. Generate v2.0 planning docs
# 3. Set up development environment
```

---

## 🔄 Switching Between Versions

### Switch to v1.0 (Local Mode)
```bash
# Option 1: Use stable release
git checkout v1.0.0

# Option 2: Use latest v1.x development
git checkout v1-local

# Start local servers
cd backend && node server.js &
cd frontend && npm start
```

### Switch to v2.0 (Cloud Mode)
```bash
# Switch to v2 development branch
git checkout v2-cloud

# Deploy to cloud (when ready)
./scripts/deploy-complete.sh
```

### Return to Main
```bash
git checkout main
```

---

## 📊 Version Comparison

| Feature | v1.0 (Local) | v2.0 (Cloud) |
|---------|--------------|--------------|
| **Frontend** | localhost:3000 | CloudFront URL |
| **Backend** | localhost:3001 | API Gateway |
| **Agent** | Subprocess | Lambda Layer |
| **Startup** | Manual (2 terminals) | Automatic |
| **Scaling** | Single instance | Auto-scaling |
| **Cost** | $0 (local) | ~$20-50/month |
| **Access** | Local only | Public URL |
| **SSL** | No | Yes (HTTPS) |
| **Monitoring** | Console logs | CloudWatch |

---

## 🛠️ Common Commands

### Check Current Version
```bash
git describe --tags
# Output: v1.0.0 or v2.0.0
```

### List All Versions
```bash
git tag
# Output:
# v1.0.0
# v2.0.0
```

### View Version History
```bash
git log --oneline --decorate --graph
```

### Create New v1.x Release
```bash
# Make changes on v1-local branch
git checkout v1-local

# Make your changes...
git add .
git commit -m "v1.1.0: Add new feature"

# Tag the release
git tag -a v1.1.0 -m "Release v1.1.0"

# Push
git push origin v1-local --tags
```

---

## 🔐 Safety Features

### 1. **Separate Branches**
- `main` - Stable releases only
- `v1-local` - v1.x development
- `v2-cloud` - v2.x development

### 2. **Git Tags**
- `v1.0.0` - Stable local version
- `v2.0.0` - Stable cloud version (when ready)

### 3. **Easy Rollback**
```bash
# If v2.0 has issues, instantly revert:
git checkout v1.0.0

# Everything works exactly as before!
```

---

## 📝 Development Workflow

### Working on v1.x (Local Improvements)
```bash
# 1. Switch to v1 development
git checkout v1-local

# 2. Make changes
# ... edit files ...

# 3. Test locally
cd backend && node server.js &
cd frontend && npm start

# 4. Commit and tag
git add .
git commit -m "Improve feature X"
git tag v1.1.0
git push origin v1-local --tags
```

### Working on v2.x (Cloud Deployment)
```bash
# 1. Switch to v2 development
git checkout v2-cloud

# 2. Make cloud-specific changes
# ... edit deployment files ...

# 3. Test deployment
./scripts/deploy-complete.sh

# 4. Commit and tag (when stable)
git add .
git commit -m "Cloud deployment ready"
git tag v2.0.0
git push origin v2-cloud --tags
```

---

## 🎯 Best Practices

### 1. **Always Tag Releases**
```bash
git tag -a v1.1.0 -m "Description"
```

### 2. **Keep Branches Synced**
```bash
# Merge v1 improvements into v2
git checkout v2-cloud
git merge v1-local
```

### 3. **Test Before Tagging**
- v1.x: Test locally
- v2.x: Test in AWS staging environment

### 4. **Document Changes**
Update `VERSION.md` with each release

---

## 🆘 Troubleshooting

### "I'm on the wrong version!"
```bash
# Check where you are
git branch
git describe --tags

# Go to v1.0
git checkout v1.0.0

# Go to v2.0
git checkout v2.0.0
```

### "v2.0 broke something!"
```bash
# Instant rollback to v1.0
git checkout v1.0.0

# Start local servers
cd backend && node server.js &
cd frontend && npm start

# Everything works!
```

### "I want the latest v1.x features"
```bash
git checkout v1-local
```

---

## 📚 Additional Resources

- **Version History:** See `VERSION.md`
- **v2.0 Plan:** See `docs/V2_CLOUD_PLAN.md` (after running start-v2-cloud.sh)
- **Deployment:** See `docs/DEPLOYMENT_COMPLETE.md`
- **Architecture:** See `docs/SYSTEM_ARCHITECTURE.md`

---

## 🎉 Summary

1. **v1.0 is stable** - Use it anytime with `git checkout v1.0.0`
2. **v2.0 is in development** - Work on it with `git checkout v2-cloud`
3. **Easy rollback** - Always safe to revert to v1.0
4. **Separate branches** - v1 and v2 development don't interfere

**You can always go back to v1.0 if v2.0 has issues!** 🛡️

---

*Last Updated: October 15, 2025*
