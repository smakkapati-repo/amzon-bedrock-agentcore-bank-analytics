import React, { useState, useEffect } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { Box, Tabs, Tab, AppBar, Toolbar, Typography, Container, IconButton, CircularProgress } from '@mui/material';
import CssBaseline from '@mui/material/CssBaseline';
import AccountBalanceIcon from '@mui/icons-material/AccountBalance';
import AnalyticsIcon from '@mui/icons-material/Analytics';
import AssessmentIcon from '@mui/icons-material/Assessment';
import LogoutIcon from '@mui/icons-material/Logout';
import { Amplify } from '@aws-amplify/core';
import { Auth } from '@aws-amplify/auth';
import { cognitoConfig } from './config';
import Home from './components/Home';
import PeerAnalytics from './components/PeerAnalytics';
import FinancialReports from './components/FinancialReports';
import Login from './components/Login';

// Configure Amplify with Cognito
Amplify.configure({
  Auth: cognitoConfig
});
console.log('[Auth] Cognito authentication enabled');

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#A020F0',
    },
    secondary: {
      main: '#8B1A9B',
    },
    background: {
      default: '#FAFAFA',
      paper: '#FFFFFF',
    },
  },
  typography: {
    fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    h4: {
      fontWeight: 600,
    },
  },
  components: {
    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontSize: '1rem',
          fontWeight: 500,
        },
      },
    },
  },
});

function TabPanel({ children, value, index }) {
  return (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

function App() {
  const [tabValue, setTabValue] = useState(0);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      await Auth.currentAuthenticatedUser();
      setIsAuthenticated(true);
      console.log('[Auth] User authenticated via Cognito');
    } catch {
      setIsAuthenticated(false);
      console.log('[Auth] No Cognito session found');
    }
    setLoading(false);
  };

  const handleCognitoLogin = () => {
    // Redirect to Cognito Hosted UI
    Auth.federatedSignIn();
  };

  const handleLogout = async () => {
    try {
      await Auth.signOut();
      console.log('[Auth] Signed out from Cognito');
    } catch (err) {
      console.error('[Auth] Sign out error:', err);
    }
    setIsAuthenticated(false);
    setTabValue(0);
  };

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  if (loading) {
    return (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
          <CircularProgress />
        </Box>
      </ThemeProvider>
    );
  }

  if (!isAuthenticated) {
    return (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Login onCognitoLogin={handleCognitoLogin} />
      </ThemeProvider>
    );
  }

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ flexGrow: 1 }}>
        <AppBar position="static" elevation={0} sx={{ background: 'linear-gradient(135deg, #A020F0 0%, #8B1A9B 100%)' }}>
          <Toolbar>
            <AccountBalanceIcon sx={{ mr: 2 }} />
            <Typography variant="h4" component="div" sx={{ flexGrow: 1, fontWeight: 600 }}>
              BankIQ+
            </Typography>
            <IconButton color="inherit" onClick={handleLogout} title="Logout">
              <LogoutIcon />
            </IconButton>
          </Toolbar>
          <Tabs 
            value={tabValue} 
            onChange={handleTabChange} 
            sx={{ 
              backgroundColor: '#1e3a8a',
              '& .MuiTab-root': { color: 'rgba(255,255,255,0.8)' },
              '& .Mui-selected': { color: 'white !important' },
              '& .MuiTabs-indicator': { backgroundColor: 'white' }
            }}
          >
            <Tab icon={<AccountBalanceIcon />} label="Home" />
            <Tab icon={<AnalyticsIcon />} label="Peer Analytics" />
            <Tab icon={<AssessmentIcon />} label="Financial Reports" />
          </Tabs>
        </AppBar>
        
        <Container maxWidth="xl" sx={{ mt: 2 }}>
          <TabPanel value={tabValue} index={0}>
            <Home />
          </TabPanel>
          <TabPanel value={tabValue} index={1}>
            <PeerAnalytics />
          </TabPanel>
          <TabPanel value={tabValue} index={2}>
            <FinancialReports />
          </TabPanel>
        </Container>
      </Box>
    </ThemeProvider>
  );
}

export default App;