// Auto-generated - CloudFront + ECS Backend + Cognito Auth
export const API_URL = 'https://dy954odc3xszb.cloudfront.net';
export const ENVIRONMENT = 'production';
export const CLOUDFRONT_URL = 'https://dy954odc3xszb.cloudfront.net';

export const cognitoConfig = {
  region: 'us-east-1',
  userPoolId: 'us-east-1_I5ghZdqla',
  userPoolWebClientId: '1ne9o3vi4hkcskr4plu0odjn0o',
  oauth: {
    domain: 'bankiq-auth-164543933824.auth.us-east-1.amazoncognito.com',
    scope: ['email', 'openid', 'profile'],
    redirectSignIn: 'https://dy954odc3xszb.cloudfront.net',
    redirectSignOut: 'https://dy954odc3xszb.cloudfront.net',
    responseType: 'code'
  }
};
