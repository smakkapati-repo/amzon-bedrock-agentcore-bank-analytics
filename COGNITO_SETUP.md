# Cognito Authentication Setup

## Status: ✅ Ready to Deploy

All code is committed to the `feature/cognito-auth` branch.

## What Was Done

### 1. Cognito Stack (Deployed)
- ✅ User Pool created: `us-east-1_bU7q0CBCT`
- ✅ App Client created: `v7udbhmlm4vcp97i2f8lt8vn2`
- ✅ Hosted UI domain: `bankiq-auth-164543933824.auth.us-east-1.amazoncognito.com`
- ✅ Test user created: `admin@bankiq.com`

### 2. Backend Changes
- ✅ JWT verification middleware (`auth-middleware.js`)
- ✅ Protected API routes with `verifyToken`
- ✅ Optional authentication via `AUTH_ENABLED` flag
- ✅ Dependencies: `jsonwebtoken`, `jwks-rsa`

### 3. Frontend Changes
- ✅ AWS Amplify Auth integration
- ✅ Cognito Hosted UI login
- ✅ JWT tokens sent with API requests
- ✅ Optional authentication via `USE_COGNITO` flag
- ✅ Fallback to old login when Cognito disabled

## Configuration

### Cognito Details
```
User Pool ID: us-east-1_bU7q0CBCT
Client ID: v7udbhmlm4vcp97i2f8lt8vn2
Region: us-east-1
Domain: bankiq-auth-164543933824.auth.us-east-1.amazoncognito.com
```

### Test Credentials
```
Email: admin@bankiq.com
Password: (set during first login)
```

## Deployment Options

### Option A: Deploy with Cognito DISABLED (Safe Test)
Deploy the full app with authentication disabled to verify nothing broke:

```bash
# Backend environment variables
AUTH_ENABLED=false

# Frontend environment variable
REACT_APP_USE_COGNITO=false
```

### Option B: Deploy with Cognito ENABLED
Enable Cognito authentication:

```bash
# Backend environment variables
AUTH_ENABLED=true
COGNITO_REGION=us-east-1
COGNITO_USER_POOL_ID=us-east-1_bU7q0CBCT

# Frontend environment variable
REACT_APP_USE_COGNITO=true
```

## Next Steps

1. **Test Locally First** (Recommended)
   ```bash
   # Install dependencies
   cd backend && npm install
   cd ../frontend && npm install
   
   # Run backend (auth disabled)
   cd backend
   AUTH_ENABLED=false npm start
   
   # Run frontend (auth disabled)
   cd frontend
   REACT_APP_USE_COGNITO=false npm start
   ```

2. **Deploy to AWS**
   - Update CloudFormation templates to add Cognito env vars
   - Deploy with auth disabled first
   - Test the app works
   - Enable auth and redeploy

3. **Update Callback URLs**
   - Once CloudFront URL is known, update Cognito callback URLs
   - Update `frontend/src/config.js` with production URL

## Rollback Plan

If anything goes wrong:
```bash
# Switch back to main branch
git checkout main

# Delete Cognito stack (optional)
aws cloudformation delete-stack --stack-name bankiq-auth --region us-east-1

# Redeploy from main
./cfn/scripts/deploy-all.sh
```

## Testing Cognito

### Test Hosted UI
Visit: https://bankiq-auth-164543933824.auth.us-east-1.amazoncognito.com/login?client_id=v7udbhmlm4vcp97i2f8lt8vn2&response_type=code&redirect_uri=http://localhost:3000

### Create Additional Users
```bash
aws cognito-idp admin-create-user \
  --user-pool-id us-east-1_bU7q0CBCT \
  --username user@example.com \
  --user-attributes Name=email,Value=user@example.com Name=email_verified,Value=true \
  --temporary-password TempPass123! \
  --region us-east-1
```

## Benefits

✅ **Secure** - Industry-standard OAuth 2.0 + JWT
✅ **Scalable** - Handles millions of users
✅ **Managed** - AWS handles password reset, email verification
✅ **Optional** - Can be disabled without breaking the app
✅ **Backward Compatible** - Old login still works as fallback

## Cost

- **Free tier:** 50,000 MAUs (Monthly Active Users)
- **After free tier:** $0.0055 per MAU
- **Current usage:** ~$0/month (well within free tier)
