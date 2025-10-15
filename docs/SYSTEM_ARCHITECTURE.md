# BankIQ+ System Architecture

## Overview
BankIQ+ is a full-stack AI-powered banking analytics platform with React frontend, Node.js backend, and Python AI agent using AWS Bedrock.

---

## 🤖 AI Agents

### 1. **BankIQ+ Agent** (`bank_iq_agent_v1.py`)
- **Framework**: AgentCore (Strands) + AWS Bedrock
- **Model**: Claude Sonnet 4.5 (us.anthropic.claude-sonnet-4-5-20250929-v1:0)
- **Purpose**: Financial analysis, SEC filings, peer comparisons, document analysis
- **Invocation**: Via `/api/invoke-agent` endpoint

**Total Agents: 1**

---

## 🔧 AI Agent Tools (12 Tools)

### Data Retrieval Tools
1. **`get_fdic_data`** - Fetch FDIC Call Reports for major US banks
2. **`get_sec_filings`** - Get SEC EDGAR filings (10-K, 10-Q) with CIK support
3. **`search_banks`** - Search banks by name/ticker (cache + SEC EDGAR)

### Analysis Tools
4. **`compare_banks`** - Compare performance metrics across multiple banks
5. **`generate_bank_report`** - Generate comprehensive financial analysis reports
6. **`answer_banking_question`** - Answer general banking questions with expert analysis

### Document Management Tools
7. **`analyze_and_upload_pdf`** - Analyze PDF documents and upload to S3
8. **`upload_document_to_s3`** - Legacy upload function (redirects to analyze_and_upload_pdf)
9. **`analyze_uploaded_pdf`** - Analyze PDFs already in S3 (reads from S3, extracts text, analyzes)
10. **`chat_with_documents`** - Chat about uploaded documents or SEC filings

### CSV Data Tools
11. **`upload_csv_to_s3`** - Upload CSV data for peer analytics
12. **`analyze_csv_peer_performance`** - Analyze peer performance using uploaded CSV data

**Total Tools: 12**

---

## 🌐 Backend API Endpoints (9 Endpoints)

### Core Agent Endpoint
1. **`POST /api/invoke-agent`** - Main agent invocation endpoint
   - Accepts: `{ inputText, sessionId }`
   - Returns: Agent response with analysis

### Direct Data Endpoints (Fast, No Agent)
2. **`POST /api/search-banks`** - Direct bank search
   - Cache: 24 major banks
   - Fallback: SEC EDGAR (~13,000 companies)
   - Returns: `{ success, results: [{ name, ticker, cik }] }`

3. **`POST /api/get-sec-filings`** - Direct SEC filings retrieval
   - Accepts: `{ bankName, cik }`
   - Returns: `{ success, '10-K': [...], '10-Q': [...] }`

### Document Management Endpoints
4. **`POST /api/upload-pdf`** - Upload and analyze PDF documents
   - Extracts metadata using PyPDF2
   - Uploads to S3: `uploaded-docs/{bank}/{year}/{form_type}/{filename}`
   - Returns: `{ success, documents: [{ bank_name, form_type, year, s3_key }] }`

### CSV Data Endpoints
5. **`POST /api/store-csv-data`** - Store CSV data for peer analytics
   - Accepts: `{ data, filename }`
   - Stores in memory/S3

6. **`POST /api/analyze-local-data`** - Analyze uploaded CSV data
   - Accepts: `{ data, baseBank, peerBanks, metric }`
   - Calls agent for analysis
   - Returns: `{ analysis }`

### Utility Endpoints
7. **`GET /health`** - Health check endpoint
8. **`GET /`** - Root endpoint (returns "BankIQ+ Backend")

**Total Endpoints: 8 (+ 1 health check)**

---

## 📁 Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                          │
│  - Peer Analytics Tab                                        │
│  - Financial Reports Tab (Live + Local modes)                │
│  - Material-UI Components                                    │
└─────────────────────────────────────────────────────────────┘
                            ↓ HTTP/REST
┌─────────────────────────────────────────────────────────────┐
│                  BACKEND (Node.js/Express)                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Direct Endpoints (Fast Path)                       │   │
│  │  - /api/search-banks                                │   │
│  │  - /api/get-sec-filings                             │   │
│  │  - /api/upload-pdf                                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                            ↓                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Agent Endpoint (AI Path)                           │   │
│  │  - /api/invoke-agent                                │   │
│  │  - /api/analyze-local-data                          │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓ spawn Python process
┌─────────────────────────────────────────────────────────────┐
│              AI AGENT (Python/AgentCore)                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  BankIQ+ Agent (bank_iq_agent_v1.py)                │   │
│  │  - 12 Tools                                          │   │
│  │  - Claude Sonnet 4.5                                 │   │
│  │  - AgentCore Framework                               │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   EXTERNAL SERVICES                          │
│  - AWS Bedrock (Claude API)                                 │
│  - AWS S3 (Document Storage)                                │
│  - SEC EDGAR API (Company/Filings Data)                     │
│  - FDIC API (Banking Data)                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Key Design Decisions

### 1. **Hybrid Architecture: Direct + Agent**
- **Direct Endpoints**: Fast, reliable for simple operations (search, SEC filings)
- **Agent Endpoints**: Intelligent analysis, complex reasoning, document understanding

### 2. **PDF Processing Pipeline**
```
Upload → PyPDF2 Extract Metadata → S3 Upload → Agent Analysis
```
- **PyPDF2**: Extracts bank name, form type, year from first 5 pages
- **S3 Storage**: `uploaded-docs/{bank}/{year}/{form_type}/{filename}`
- **Agent Tool**: `analyze_uploaded_pdf` reads from S3 and analyzes

### 3. **Search Strategy**
```
Query → Cache (24 banks) → SEC EDGAR (13k companies) → Results
```
- **Cache Hit**: Instant response
- **Cache Miss**: 1-2 second SEC EDGAR search

### 4. **SEC Filings Strategy**
```
CIK → SEC API → Parse JSON → Filter 2024-2025 → Return 10-K/10-Q
```
- Direct API call (no agent overhead)
- Filters for recent filings only

---

## 📊 Data Flow Examples

### Example 1: Search for Bank
```
User types "Webster" 
  → Frontend: api.searchBanks("Webster")
  → Backend: POST /api/search-banks
  → Cache lookup → Found: WEBSTER FINANCIAL CORP (CIK: 0000801337)
  → Return to Frontend
  → User clicks result
  → Frontend: api.getSECReports("WEBSTER FINANCIAL CORP", 2024, false, "0000801337")
  → Backend: POST /api/get-sec-filings
  → SEC API: https://data.sec.gov/submissions/CIK0000801337.json
  → Parse and filter filings
  → Return 10-K and 10-Q lists
```

### Example 2: Upload PDF
```
User uploads PDF
  → Frontend: Reads file as base64
  → Backend: POST /api/upload-pdf
  → Python: extract_pdf_metadata.py
    → PyPDF2 reads first 5 pages
    → Extracts: "WEBSTER FINANCIAL CORPORATION", "10-K", 2024
  → S3 Upload: uploaded-docs/WEBSTER_FINANCIAL_CORPORATION/2024/10-K/filing.pdf
  → Return: { bank_name, form_type, year, s3_key }
  → User clicks "Full Analysis"
  → Backend: POST /api/invoke-agent
  → Agent: Uses analyze_uploaded_pdf tool
    → Reads PDF from S3
    → Extracts text (first 50 pages)
    → Claude analyzes with Converse API
  → Return comprehensive analysis
```

### Example 3: Peer Analytics (Live Mode)
```
User selects banks and metric
  → Frontend: api.analyzePeers("JPMorgan", ["BofA", "Wells"], "ROA")
  → Backend: POST /api/invoke-agent
  → Agent: Uses compare_banks tool
    → Calls get_fdic_data tool
    → Fetches FDIC Call Reports
    → Compares metrics
    → Returns DATA: {...} + analysis
  → Frontend: Parses DATA, renders chart + analysis
```

---

## 🔐 Security & Best Practices

1. **AWS Credentials**: Uses default AWS credential chain (environment variables, IAM roles)
2. **S3 Bucket**: `bankiq-uploaded-docs` (private)
3. **API Rate Limiting**: SEC EDGAR requires User-Agent header
4. **Error Handling**: Graceful fallbacks for all external API calls
5. **Input Validation**: All endpoints validate required parameters

---

## 📈 Performance Optimizations

1. **Direct Endpoints**: Bypass agent for 10x faster responses
2. **Caching**: 24 major banks cached for instant search
3. **Streaming**: Internal streaming in tools (converse_stream)
4. **Lazy Loading**: Only load data when needed
5. **Parallel Processing**: Multiple tool calls can run concurrently

---

## 🚀 Deployment Architecture

### Local Development
- Frontend: `localhost:3000` (React Dev Server)
- Backend: `localhost:3001` (Node.js Express)
- Agent: Python subprocess (spawned on-demand)

### Production (AWS)
- Frontend: S3 + CloudFront (Static hosting)
- Backend: Lambda + API Gateway (Serverless)
- Agent: Lambda Layer (Python + dependencies)
- Storage: S3 (Documents + CSV data)

---

## 📝 Summary

| Component | Count | Details |
|-----------|-------|---------|
| **AI Agents** | 1 | BankIQ+ Agent (Claude Sonnet 4.5) |
| **AI Tools** | 12 | FDIC, SEC, Analysis, Documents, CSV |
| **API Endpoints** | 8 | Direct (3) + Agent (2) + Documents (1) + CSV (2) |
| **Frontend Tabs** | 2 | Peer Analytics, Financial Reports |
| **Data Modes** | 2 | Live (API) + Local (Upload) |
| **External APIs** | 4 | Bedrock, S3, SEC EDGAR, FDIC |

---

## 🎨 Technology Stack

**Frontend:**
- React 18
- Material-UI 5
- Recharts (Charts)
- React Router
- Axios

**Backend:**
- Node.js + Express
- AWS SDK (S3, Bedrock)
- Child Process (Python spawning)

**AI Agent:**
- Python 3
- AgentCore (Strands)
- AWS Bedrock (Claude)
- PyPDF2 (PDF parsing)
- Boto3 (AWS SDK)

**Infrastructure:**
- AWS S3 (Storage)
- AWS Bedrock (AI)
- SEC EDGAR API
- FDIC API

---

*Last Updated: October 15, 2025*
