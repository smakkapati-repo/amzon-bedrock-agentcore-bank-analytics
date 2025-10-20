// Auto-generated - CloudFront + ECS Backend + Cognito Auth
export const API_URL = 'https://dta7ft4631owm.cloudfront.net';
export const ENVIRONMENT = 'production';
export const CLOUDFRONT_URL = 'https://dta7ft4631owm.cloudfront.net';

export const cognitoConfig = {
  region: 'us-east-1',
  userPoolId: 'us-east-1_Gb5Vklj7D',
  userPoolWebClientId: '6mb6o5ktkaukn2rej4cjtvgb3',
  oauth: {
    domain: 'bankiq-auth-164543933824.auth.us-east-1.amazoncognito.com',
    scope: ['email', 'openid', 'profile'],
    redirectSignIn: 'https://dta7ft4631owm.cloudfront.net',
    redirectSignOut: 'https://dta7ft4631owm.cloudfront.net',
    responseType: 'code'
  }
};
