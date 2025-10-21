# Windows Setup Guide

> Complete setup guide for Windows users to deploy BankIQ+ AI Banking Analytics Platform

## 🖥️ Windows Prerequisites

### One-Command Setup (Recommended)

**Run as Administrator in PowerShell:**

```powershell
# Install Chocolatey package manager
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install all required tools
choco install vscode python docker-desktop git awscli nodejs -y
```

### Alternative: Individual Installation

```powershell
# VS Code
choco install vscode -y

# Python 3.11+
choco install python -y

# Docker Desktop (requires restart)
choco install docker-desktop -y

# Git
choco install git -y

# AWS CLI
choco install awscli -y

# Node.js 18+
choco install nodejs -y
```

### Using Windows Package Manager (winget)

```powershell
winget install Microsoft.VisualStudioCode
winget install Python.Python.3.11
winget install Docker.DockerDesktop
winget install Git.Git
winget install Amazon.AWSCLI
winget install OpenJS.NodeJS
```

## 🔧 Post-Installation Setup

### 1. Restart Required
```powershell
# After Docker Desktop installation
Restart-Computer
```

### 2. Configure AWS CLI
```powershell
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key  
# Enter region: us-east-1
# Enter output format: json
```

### 3. Install AgentCore CLI
```powershell
pip install bedrock-agentcore-starter-toolkit
```

### 4. Start Docker Desktop
```powershell
# Start Docker Desktop automatically
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"

# Wait for Docker to fully start (30-60 seconds)
Write-Host "Waiting for Docker Desktop to start..."
do {
    Start-Sleep -Seconds 5
    $dockerStatus = docker version 2>$null
} while (-not $dockerStatus)
Write-Host "✅ Docker Desktop is running!"
```

**Manual alternative:**
- Launch Docker Desktop from Start Menu
- Wait for whale icon in system tray

## 🚀 Deploy BankIQ+

### Clone Repository
```powershell
git clone https://github.com/smakkapati-repo/amzon-bedrock-agentcore-bank-analytics.git
cd amzon-bedrock-agentcore-bank-analytics
```

### Run Deployment
```powershell
# Start Docker Desktop (if not already running)
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
Start-Sleep -Seconds 30

# Run deployment
./cfn/scripts/deploy-all.sh
```

## ⚠️ Windows-Specific Notes

### Docker Requirements
- **Windows 10/11 Pro/Enterprise**: Uses Hyper-V
- **Windows 10/11 Home**: Requires WSL2
- **Docker Desktop must be running** during deployment

### PowerShell Execution Policy
If you get execution policy errors:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Git Bash Alternative
You can also use Git Bash (installed with Git) to run the deployment scripts:
```bash
# In Git Bash
./cfn/scripts/deploy-all.sh
```

## 🔍 Troubleshooting

### Docker Not Running
```
Error: Cannot connect to the Docker daemon
```
**Solution:** Start Docker Desktop and wait for it to fully load

### PowerShell Execution Policy
```
Execution of scripts is disabled on this system
```
**Solution:** Run as Administrator and set execution policy

### AWS CLI Not Found
```
'aws' is not recognized as an internal or external command
```
**Solution:** Restart PowerShell/Command Prompt after installation

## ✅ Verification Commands

```powershell
# Check installations
python --version     # Should be 3.11+
node --version       # Should be 18+
docker --version     # Should show Docker version
aws --version        # Should show AWS CLI version
agentcore --help     # Should show AgentCore commands
git --version        # Should show Git version
```

## 🚀 Complete Automated Setup

**Copy-paste this entire script in PowerShell (as Administrator):**

```powershell
# 1. Install all tools
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
choco install vscode python docker-desktop git awscli nodejs -y

# 2. Install AgentCore CLI
pip install bedrock-agentcore-starter-toolkit

# 3. Restart required message
Write-Host "⚠️  RESTART REQUIRED for Docker Desktop. After restart, run the deployment script below."
Read-Host "Press Enter to restart now, or Ctrl+C to restart manually"
Restart-Computer
```

**After restart, run this deployment script:**

```powershell
# Configure AWS (enter your credentials when prompted)
aws configure

# Start Docker Desktop
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
Write-Host "Waiting for Docker Desktop to start..."
Start-Sleep -Seconds 45

# Clone and deploy
git clone https://github.com/smakkapati-repo/amzon-bedrock-agentcore-bank-analytics.git
cd amzon-bedrock-agentcore-bank-analytics
./cfn/scripts/deploy-all.sh
```

## 🎯 Quick Start Summary

1. **Run automated setup script as Administrator**
2. **Restart computer** (automated)
3. **Run deployment script** (includes AWS config + Docker startup)
4. **Access your app** at the CloudFront URL

**Total setup time:** ~10-15 minutes + restart

## 📝 Copy-Paste Scripts Summary

**Script 1 (Pre-restart):**
```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1')); choco install vscode python docker-desktop git awscli nodejs -y; pip install bedrock-agentcore-starter-toolkit; Restart-Computer
```

**Script 2 (Post-restart):**
```powershell
aws configure; Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"; Start-Sleep -Seconds 45; git clone https://github.com/smakkapati-repo/amzon-bedrock-agentcore-bank-analytics.git; cd amzon-bedrock-agentcore-bank-analytics; ./cfn/scripts/deploy-all.sh
```

---

**Need help?** Check the main [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed deployment instructions.