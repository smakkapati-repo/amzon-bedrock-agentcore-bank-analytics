import React from 'react';
import { Typography, Box, Grid, Card, CardContent, Chip, Paper } from '@mui/material';
import AccountBalanceIcon from '@mui/icons-material/AccountBalance';
import AnalyticsIcon from '@mui/icons-material/Analytics';
import AssessmentIcon from '@mui/icons-material/Assessment';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import SecurityIcon from '@mui/icons-material/Security';
import CloudIcon from '@mui/icons-material/Cloud';

function Home() {
  const features = [
    {
      icon: <AnalyticsIcon sx={{ fontSize: 48, color: 'primary.main' }} />,
      title: 'Peer Bank Analytics',
      description: 'Compare banking metrics across peer institutions with real-time FDIC data and AI insights',
      status: 'Live FDIC API'
    },
    {
      icon: <AssessmentIcon sx={{ fontSize: 48, color: 'primary.main' }} />,
      title: 'Financial Reports Analyzer',
      description: 'Analyze SEC filings and financial reports with live EDGAR API and document upload',
      status: 'SEC EDGAR API'
    },
    {
      icon: <TrendingUpIcon sx={{ fontSize: 48, color: 'primary.main' }} />,
      title: 'Risk Assessment',
      description: 'Comprehensive risk analysis with predictive modeling and stress testing',
      status: 'Coming Soon'
    }
  ];

  const stats = [
    { label: 'Banks Analyzed', value: '29+', color: '#00778f' },
    { label: 'Metrics Tracked', value: '6+', color: '#00a897' },
    { label: 'Analysis Modes', value: '3', color: '#02c59b' },
    { label: 'AI Models', value: '2', color: '#A020F0' }
  ];

  return (
    <Box>
      {/* Hero Section */}
      <Paper 
        elevation={0} 
        sx={{ 
          background: 'linear-gradient(135deg, #A020F0 0%, #8B1A9B 50%, #6A1B9A 100%)',
          color: 'white',
          p: 6,
          borderRadius: 3,
          mb: 4
        }}
      >
        <Box textAlign="center">
          <AccountBalanceIcon sx={{ fontSize: 80, mb: 2 }} />
          <Typography variant="h2" component="h1" gutterBottom sx={{ fontWeight: 600 }}>
            BankIQ+
          </Typography>
          <Typography variant="h5" sx={{ opacity: 0.9, mb: 3 }}>
            Advanced Banking Analytics & Risk Assessment Platform
          </Typography>
          <Chip 
            icon={<CloudIcon />} 
            label="Powered by AWS Bedrock AgentCore Runtime" 
            sx={{ 
              backgroundColor: 'rgba(255,255,255,0.2)', 
              color: 'white',
              fontSize: '1rem',
              py: 2
            }} 
          />
        </Box>
      </Paper>

      {/* Stats Section */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {stats.map((stat, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card sx={{ textAlign: 'center', p: 2, backgroundColor: stat.color, color: 'white' }}>
              <Typography variant="h3" sx={{ fontWeight: 700, mb: 1 }}>
                {stat.value}
              </Typography>
              <Typography variant="body1" sx={{ opacity: 0.9 }}>
                {stat.label}
              </Typography>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Features Section */}
      <Typography variant="h4" gutterBottom sx={{ mb: 3, fontWeight: 600 }}>
        Platform Features
      </Typography>
      
      <Grid container spacing={4}>
        {features.map((feature, index) => (
          <Grid item xs={12} md={4} key={index}>
            <Card 
              sx={{ 
                height: '100%',
                p: 3,
                transition: 'all 0.3s ease',
                '&:hover': { 
                  transform: 'translateY(-8px)', 
                  boxShadow: '0 12px 24px rgba(160, 32, 240, 0.15)'
                }
              }}
            >
              <CardContent sx={{ textAlign: 'center' }}>
                <Box sx={{ mb: 2 }}>
                  {feature.icon}
                </Box>
                <Typography variant="h6" component="h3" gutterBottom sx={{ fontWeight: 600 }}>
                  {feature.title}
                </Typography>
                <Typography color="text.secondary" sx={{ mb: 2, minHeight: 60 }}>
                  {feature.description}
                </Typography>
                <Chip 
                  label={feature.status}
                  size="small"
                  color={feature.status === 'Coming Soon' ? 'default' : 'primary'}
                  variant={feature.status === 'Coming Soon' ? 'outlined' : 'filled'}
                />
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Technology Stack */}
      <Box sx={{ mt: 6, p: 4, backgroundColor: '#f8f9fa', borderRadius: 3 }}>
        <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, textAlign: 'center', mb: 3 }}>
          Technology Stack
        </Typography>
        <Grid container spacing={2} justifyContent="center">
          {['AWS Bedrock AgentCore', 'Claude Sonnet 4.5', 'Strands Framework', 'FDIC API', 'SEC EDGAR', 'React', 'Material-UI', 'Amazon S3'].map((tech) => (
            <Grid item key={tech}>
              <Chip 
                label={tech} 
                variant="outlined" 
                sx={{ 
                  borderColor: 'primary.main',
                  color: 'primary.main',
                  fontWeight: 500
                }}
              />
            </Grid>
          ))}
        </Grid>
      </Box>
    </Box>
  );
}

export default Home;