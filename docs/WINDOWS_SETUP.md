# Windows Setup Guide for BankIQ+

## Prerequisites for Windows

1. **Python 3.11+** - Download from [python.org](https://www.python.org/downloads/)
2. **Node.js 18+** - Download from [nodejs.org](https://nodejs.org/)
3. **Git** - Download from [git-scm.com](https://git-scm.com/)

## Step-by-Step Setup

### 1. Clone and Navigate
```cmd
git clone <repository-url>
cd current-repo
```

### 2. Setup Backend (Flask Server)
```cmd
cd backend
pip install -r requirements.txt
```

### 3. Setup Frontend (React App)
```cmd
cd ../frontend
npm install
```

## Running the Application

**You need TWO terminal windows:**

### Terminal 1 - Backend Server (Port 8001)
```cmd
cd backend
python app.py
```
**Wait for:** `Running on http://0.0.0.0:8001`

### Terminal 2 - Frontend Server (Port 3000)
```cmd
cd frontend
npm start
```
**Wait for:** `Local: http://localhost:3000`

## Access the Application
- Open browser to: `http://localhost:3000`
- Backend API runs on: `http://localhost:8001`

## Troubleshooting Windows Issues

### Python Issues
```cmd
# If 'python' command not found, try:
python3 app.py
# or
py app.py
```

### Port Already in Use
```cmd
# Kill process on port 8001
netstat -ano | findstr :8001
taskkill /PID <PID_NUMBER> /F

# Kill process on port 3000
netstat -ano | findstr :3000
taskkill /PID <PID_NUMBER> /F
```

### AWS Credentials (for AI features)
```cmd
# Install AWS CLI
pip install awscli

# Configure credentials
aws configure
```

## Common Windows Errors

**"ERR_CONNECTION_REFUSED"** = Backend not running
**"CORS request did not succeed"** = Backend not accessible
**"Failed to load resource"** = Wrong URL or server down

## Quick Test
1. Backend running? Visit: `http://localhost:8001/health`
2. Should return: `{"status": "healthy", "service": "BankIQ+"}`