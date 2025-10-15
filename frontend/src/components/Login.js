import React, { useState } from 'react';
import { Box, Paper, TextField, Button, Typography, Alert } from '@mui/material';
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';

const Login = ({ onLogin }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Simple hardcoded credentials (replace with real auth later)
    if (username === 'admin' && password === 'bankiq2024') {
      localStorage.setItem('isAuthenticated', 'true');
      onLogin();
    } else {
      setError('Invalid username or password');
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #A020F0 0%, #8B1A9B 100%)',
      }}
    >
      <Paper
        elevation={3}
        sx={{
          p: 4,
          maxWidth: 400,
          width: '100%',
          textAlign: 'center',
        }}
      >
        <LockOutlinedIcon sx={{ fontSize: 48, color: '#A020F0', mb: 2 }} />
        <Typography variant="h4" gutterBottom sx={{ fontWeight: 600 }}>
          BankIQ+ Login
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Enter your credentials to access the platform
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <form onSubmit={handleSubmit}>
          <TextField
            fullWidth
            label="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            margin="normal"
            required
          />
          <TextField
            fullWidth
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            margin="normal"
            required
          />
          <Button
            type="submit"
            variant="contained"
            fullWidth
            sx={{
              mt: 3,
              backgroundColor: '#A020F0',
              '&:hover': { backgroundColor: '#8B1A9B' },
            }}
          >
            Login
          </Button>
        </form>

        <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
          Demo credentials: admin / bankiq2024
        </Typography>
      </Paper>
    </Box>
  );
};

export default Login;
