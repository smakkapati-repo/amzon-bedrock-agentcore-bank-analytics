import React, { useState } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { Box, Tabs, Tab, AppBar, Toolbar, Typography, Container } from '@mui/material';
import CssBaseline from '@mui/material/CssBaseline';
import AccountBalanceIcon from '@mui/icons-material/AccountBalance';
import AnalyticsIcon from '@mui/icons-material/Analytics';
import AssessmentIcon from '@mui/icons-material/Assessment';
import Home from './components/Home';
import PeerAnalytics from './components/PeerAnalytics';
import FinancialReports from './components/FinancialReports';

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

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

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
          </Toolbar>
          <Tabs 
            value={tabValue} 
            onChange={handleTabChange} 
            sx={{ 
              backgroundColor: 'rgba(255,255,255,0.1)',
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