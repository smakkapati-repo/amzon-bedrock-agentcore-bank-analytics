# Backend - Bank IQ Agent

## Active Agent

**Name:** `bank-iq-agent`  
**Version:** v1  
**File:** `bank_iq_agent_v1.py`

## Agent Details

### Configuration
```yaml
name: bank-iq-agent
runtime: python3.12
entrypoint: bank_iq_agent_v1.py
region: us-east-1
```

### Tools (10 total)
1. get_fdic_data
2. compare_banks
3. get_sec_filings
4. generate_bank_report
5. answer_banking_question
6. search_banks
7. upload_csv_to_s3
8. analyze_csv_peer_performance
9. upload_document_to_s3
10. chat_with_documents

## Files

### Active
- **`bank_iq_agent_v1.py`** - Main agent with 10 tools
- **`server.js`** - Express API server (port 3001)
- **`invoke-agentcore.py`** - Python bridge to AgentCore CLI
- **`.bedrock_agentcore.yaml`** - Agent configuration
- **`package.json`** - Node.js dependencies
- **`requirements.txt`** - Python dependencies

### Archive
- **`archive/`** - Legacy agent versions (not used)

## Deployment

```bash
# Configure agent
agentcore configure -e bank_iq_agent_v1.py

# Deploy to AWS
agentcore launch

# Test
agentcore invoke '{"prompt": "Compare JPMorgan vs Bank of America ROE"}'

# View logs
agentcore logs --follow
```

## Local Development

```bash
# Start backend server
npm install
npm start
```

Server runs on http://localhost:3001

## API Endpoints

- **GET** `/health` - Health check
- **POST** `/api/invoke-agent` - Invoke agent
  ```json
  {
    "inputText": "Your question here",
    "sessionId": "optional-session-id"
  }
  ```

## Version History

### v1 (Current)
- 10 tools for banking analytics
- Express backend with Python bridge
- AgentCore integration
- Claude Sonnet 4.5

---

**Agent Name:** `bank-iq-agent`  
**Version:** v1  
**Status:** Active
