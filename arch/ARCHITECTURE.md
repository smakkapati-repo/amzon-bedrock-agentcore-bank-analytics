# BankIQ+ Architecture Overview

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend│    │  Flask Backend  │    │   AWS Bedrock   │
│   (Port 3000)   │◄──►│   (Port 8001)   │◄──►│   Claude AI     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       
         │                       ▼                       
         │              ┌─────────────────┐              
         │              │  External APIs  │              
         │              │  • SEC EDGAR    │              
         │              │  • FDIC Data    │              
         │              └─────────────────┘              
         │                       │                       
         ▼                       ▼                       
┌─────────────────┐    ┌─────────────────┐              
│     Nginx       │    │  FAISS Vector   │              
│  Reverse Proxy  │    │    Database     │              
│   (Port 80)     │    │   (RAG System)  │              
└─────────────────┘    └─────────────────┘              
```

## Component Details

### Frontend (React)
- **Framework**: React 18 with Material-UI
- **State Management**: React hooks (useState, useEffect)
- **Routing**: React Router for navigation
- **Charts**: Recharts for data visualization
- **API Layer**: Axios-based service layer

### Backend (Flask)
- **Framework**: Flask with CORS support
- **AI Integration**: AWS Bedrock SDK
- **Vector Search**: FAISS for RAG functionality
- **File Processing**: PyPDF2 for PDF parsing
- **External APIs**: SEC EDGAR, FDIC integration

### Data Flow

#### Peer Analytics Flow
```
User Input → React Component → API Service → Flask Endpoint → 
Data Processing → AWS Bedrock Analysis → Response → UI Update
```

#### Financial Reports Flow
```
Document Upload → PDF Processing → Text Extraction → 
Vector Embedding → FAISS Search → Context Building → 
AI Analysis → Streaming Response → Real-time UI Update
```

## Deployment Architecture

### AWS Infrastructure
- **EC2 Instance**: t3.medium with auto-scaling capability
- **Security Groups**: IP-restricted access
- **IAM Roles**: Bedrock access permissions
- **Nginx**: Reverse proxy and load balancing

### Service Management
- **Systemd Services**: Auto-restart capabilities
- **Process Monitoring**: Built-in health checks
- **Log Management**: Centralized logging

## Security Model

### Network Security
- Security Groups restrict access to user's IP only
- No SSH access required for normal operation
- HTTPS ready (certificate can be added)

### Application Security
- No hardcoded credentials
- IAM role-based AWS access
- Input validation and sanitization
- CORS properly configured

## Scalability Considerations

### Horizontal Scaling
- Frontend: Can be served from CDN
- Backend: Multiple Flask instances behind load balancer
- Database: FAISS can be distributed

### Performance Optimization
- Vector search caching
- API response caching
- Nginx static file serving
- Compressed responses

## Monitoring & Observability

### Application Metrics
- API response times
- Error rates
- User session tracking
- Resource utilization

### AWS Integration
- CloudWatch logs
- Bedrock usage metrics
- EC2 performance monitoring

## Data Management

### Vector Database (FAISS)
- Pre-processed SEC filing embeddings
- Fast similarity search
- Memory-efficient storage

### File Processing
- PDF text extraction
- CSV parsing and validation
- Real-time document analysis

### External Data Sources
- SEC EDGAR API for live filings
- FDIC API for banking metrics
- Real-time data synchronization