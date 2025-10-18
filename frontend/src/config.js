// Auto-generated - CloudFront + ECS Backend
export const API_URL = 'https://dnv0bw0r7w1h4.cloudfront.net';
export const ENVIRONMENT = 'production';
export const CLOUDFRONT_URL = 'https://dnv0bw0r7w1h4.cloudfront.net';

// Cognito Configuration (Always Enabled)
export const cognitoConfig = {
  region: 'us-east-1',
  userPoolId: 'us-east-1_bU7q0CBCT',
  userPoolWebClientId: 'v7udbhmlm4vcp97i2f8lt8vn2',
  oauth: {
    domain: 'bankiq-auth-164543933824.auth.us-east-1.amazoncognito.com',
    scope: ['email', 'openid', 'profile'],
    redirectSignIn: typeof window !== 'undefined' ? window.location.origin : 'http://localhost:3000',
    redirectSignOut: typeof window !== 'undefined' ? window.location.origin : 'http://localhost:3000',
    responseType: 'code'
  }
};
