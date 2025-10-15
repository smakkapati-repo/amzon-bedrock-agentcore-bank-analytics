# UI to Agent Tool Mapping

## ✅ Complete Coverage Analysis

### UI API Calls → Agent Tools

| UI Component | API Method | Natural Language Prompt | Agent Tool Used | Status |
|--------------|-----------|------------------------|-----------------|--------|
| **PeerAnalytics** | `getFDICData()` | "Get FDIC banking data for major banks" | `get_fdic_data()` | ✅ |
| **PeerAnalytics** | `analyzePeers()` | "Compare {bank} vs {peers} using {metric}" | `compare_banks()` | ✅ |
| **FinancialReports** | `getSECReports()` | "Get SEC filings for {bank} for year {year}" | `get_sec_filings()` | ✅ |
| **FinancialReports** | `generateFullReport()` | "Generate comprehensive financial report for {bank}" | `generate_bank_report()` | ✅ |
| **FinancialReports** | `chatWithAI()` | "{question} about {bank}" | `answer_banking_question()` | ✅ |
| **FinancialReports** | `searchBanks()` | Search query | `search_banks()` | ✅ |
| **FinancialReports** | `chatWithLocalFiles()` | "Chat about documents: {message}" | `chat_with_documents()` | ✅ |

## Agent Tools (10 total)

### Core Banking Tools
1. ✅ **get_fdic_data()** - Get current FDIC banking data
   - Used by: PeerAnalytics (Live Data mode)
   - Prompt: "Get FDIC banking data for major banks"

2. ✅ **compare_banks(base_bank, peer_banks, metric)** - Compare banks
   - Used by: PeerAnalytics (Live Data mode)
   - Prompt: "Compare JPMorgan Chase vs Bank of America using ROE"

3. ✅ **get_sec_filings(bank_name, form_type)** - Get SEC filings
   - Used by: FinancialReports (Live EDGAR mode)
   - Prompt: "Get SEC filings for Goldman Sachs for year 2024"

4. ✅ **generate_bank_report(bank_name)** - Generate comprehensive report
   - Used by: FinancialReports (Full Report button)
   - Prompt: "Generate comprehensive financial report for Wells Fargo"

5. ✅ **answer_banking_question(question, context)** - General Q&A
   - Used by: FinancialReports (Chat)
   - Prompt: "What is Net Interest Margin? about JPMorgan Chase"

### Document & Data Tools
6. ✅ **search_banks(query)** - Search for banks
   - Used by: FinancialReports (Bank search)
   - Prompt: Agent extracts from context

7. ✅ **upload_csv_to_s3(csv_content, filename)** - Upload CSV
   - Used by: PeerAnalytics (Upload CSV mode)
   - Prompt: Agent extracts from context

8. ✅ **analyze_csv_peer_performance(s3_key, base_bank, peer_banks, metric)** - Analyze CSV
   - Used by: PeerAnalytics (Upload CSV analysis)
   - Prompt: Agent extracts from context

9. ✅ **upload_document_to_s3(file_content, filename, bank_name)** - Upload docs
   - Used by: FinancialReports (Local upload mode)
   - Prompt: Agent extracts from context

10. ✅ **chat_with_documents(question, s3_key, bank_name, use_live, form_type)** - Chat with docs
    - Used by: FinancialReports (Chat with uploaded docs or SEC filings)
    - Prompt: "Chat about documents: {message}"

## UI Features Coverage

### Peer Analytics Component
| Feature | Tools Used | Status |
|---------|-----------|--------|
| Live Data mode | `get_fdic_data`, `compare_banks` | ✅ |
| Upload CSV mode | `upload_csv_to_s3`, `analyze_csv_peer_performance` | ✅ |
| Bank selection | `search_banks` | ✅ |
| Metric comparison | `compare_banks` | ✅ |
| Chart display | Data from `compare_banks` | ✅ |

### Financial Reports Component
| Feature | Tools Used | Status |
|---------|-----------|--------|
| Live EDGAR mode | `get_sec_filings`, `chat_with_documents` | ✅ |
| Local upload mode | `upload_document_to_s3`, `chat_with_documents` | ✅ |
| Bank search | `search_banks` | ✅ |
| Full report | `generate_bank_report` | ✅ |
| Chat with AI | `answer_banking_question`, `chat_with_documents` | ✅ |
| Document Q&A | `chat_with_documents` | ✅ |

## How It Works

### Natural Language Flow
```
User Action (UI)
  ↓
API Call with natural language prompt
  ↓
Backend receives: "Compare JPMorgan vs Bank of America using ROE"
  ↓
Python bridge sends to AgentCore
  ↓
Agent receives prompt
  ↓
Claude analyzes prompt and decides: "Use compare_banks() tool"
  ↓
Strands executes: compare_banks("JPMorgan Chase", ["Bank of America"], "ROE")
  ↓
Tool returns: JSON with data and analysis
  ↓
Claude formats response
  ↓
Response flows back to UI
  ↓
UI displays: Chart + Analysis
```

## Verification

### All UI Features Covered ✅
- ✅ Peer Analytics - Live Data
- ✅ Peer Analytics - Upload CSV
- ✅ Financial Reports - Live EDGAR
- ✅ Financial Reports - Local Upload
- ✅ Financial Reports - Chat
- ✅ Financial Reports - Full Report
- ✅ Bank Search

### All Agent Tools Mapped ✅
- ✅ All 10 tools have UI features that use them
- ✅ All UI features have corresponding agent tools
- ✅ Natural language prompts work for all features

## Summary

**✅ COMPLETE COVERAGE**

- **UI Features:** 7 major features
- **Agent Tools:** 10 tools
- **Coverage:** 100%
- **Status:** All UI features have corresponding agent tools

Your agent has everything the UI needs! 🎉

---

**Agent Name:** `bank-iq-agent` (v1)  
**File:** `backend/bank_iq_agent_v1.py`  
**Tools:** 10  
**UI Coverage:** 100%
