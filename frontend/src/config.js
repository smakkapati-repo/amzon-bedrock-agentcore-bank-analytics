// Auto-generated - CloudFront + ECS Backend + Cognito Auth
export const API_URL = 'https://d2429oc8ls02o2.cloudfront.net';
export const ENVIRONMENT = 'production';
export const CLOUDFRONT_URL = 'https://d2429oc8ls02o2.cloudfront.net';

export const cognitoConfig = {
  region: 'us-east-1',
  userPoolId: 'us-east-1_VRC9mAXyJ',
  userPoolWebClientId: '18n2ifmd2uahnk5mf2kpoqiak1',
  oauth: {
    domain: 'bankiq-auth-164543933824.auth.us-east-1.amazoncognito.com',
    scope: ['email', 'openid', 'profile'],
    redirectSignIn: 'https://d2429oc8ls02o2.cloudfront.net',
    redirectSignOut: 'https://d2429oc8ls02o2.cloudfront.net',
    responseType: 'code'
  }
};
