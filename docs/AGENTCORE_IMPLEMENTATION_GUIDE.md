# AgentCore Implementation Guide - Complete Knowledge Transfer

This document contains everything you need to implement Strands agents on AWS Bedrock AgentCore in any project.

## Quick Start Summary

### What We Built
- **Strands Agent** deployed on AWS Bedrock AgentCore
- **React UI** for chat interface
- **Express Backend** to proxy requests
- **Python Bridge** to invoke AgentCore
- **5 Tools** for the agent (time, calculate, random, info, word count)

### Architecture
```
React (3002) → Express (3001) → Python Script → AgentCore CLI → AWS AgentCore → Strands Agent → Claude
```

---

## 1. Agent Code Template

### File: `agent/my_agent.py`

```python
from bedrock_agentcore import BedrockAgentCoreApp
from strands import Agent, tool
from datetime import datetime
import json

app = BedrockAgentCoreApp()

# Define your tools
@tool
def your_tool_name(param: str) -> str:
    """Tool description - this tells the agent what it does.
    
    Args:
        param: Parameter description
        
    Returns:
        What the tool returns
    """
    # Your tool logic here
    return "result"

# Create agent with tools
agent = Agent(tools=[your_tool_name])

agent.system_prompt = """You are a helpful AI assistant.

Available tools:
- your_tool_name(param): Description

Use tools when appropriate."""

@app.entrypoint
def invoke(payload):
    user_message = payload.get("prompt", "Hello!")
    result = agent(user_message)
    return {
        "result": result.message,
        "agent": "YourAgentName",
        "runtime": "AgentCore"
    }

if __name__ == "__main__":
    app.run()
```

### File: `agent/requirements.txt`
```
bedrock-agentcore
strands-agents
```

---

## 2. Deployment Commands

```bash
# Install CLI
pip install bedrock-agentcore strands-agents bedrock-agentcore-starter-toolkit

# Configure agent
cd agent
agentcore configure -e my_agent.py

# Deploy to AgentCore
agentcore launch

# Test
agentcore invoke '{"prompt": "test"}'

# View logs
agentcore logs --follow

# Delete agent
agentcore delete
```

---

## 3. Backend API (Node.js + Python Bridge)

### File: `backend/server.js`

```javascript
const express = require('express');
const cors = require('cors');
const { spawn } = require('child_process');

const app = express();
const PORT = process.env.PORT || 3001;

app.use(cors());
app.use(express.json());

app.post('/api/invoke-agent', async (req, res) => {
  const { inputText, sessionId } = req.body;

  if (!inputText) {
    return res.status(400).json({ error: 'Missing inputText' });
  }

  try {
    const python = spawn('python3', [__dirname + '/invoke-agentcore.py']);
    
    let output = '';
    let error = '';
    
    python.stdout.on('data', (data) => {
      output += data.toString();
    });
    
    python.stderr.on('data', (data) => {
      error += data.toString();
    });
    
    python.stdin.write(JSON.stringify({
      prompt: inputText,
      sessionId: sessionId
    }));
    python.stdin.end();
    
    python.on('close', (code) => {
      if (code !== 0) {
        return res.status(500).json({ error: error || 'Failed to invoke agent' });
      }
      
      try {
        const result = JSON.parse(output);
        res.json({ 
          output: result.output || 'No response',
          sessionId: result.sessionId,
          runtime: 'AgentCore'
        });
      } catch (e) {
        res.status(500).json({ error: 'Failed to parse response' });
      }
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.listen(PORT, () => {
  console.log(`Backend running on port ${PORT}`);
});
```

### File: `backend/invoke-agentcore.py`

```python
#!/usr/bin/env python3
import json
import sys
import subprocess
import uuid

def invoke_agent(prompt, session_id=None):
    # Generate valid session ID (33+ chars required)
    if not session_id or len(session_id) < 33:
        session_id = str(uuid.uuid4())
    
    # Call agentcore CLI
    cmd = ['agentcore', 'invoke', json.dumps({'prompt': prompt})]
    cmd.extend(['--session-id', session_id])
    
    result = subprocess.run(
        cmd,
        cwd='../agent',
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        raise Exception(f"AgentCore failed: {result.stderr}")
    
    # Parse response
    output_text = result.stdout.strip()
    response_start = output_text.find('Response:')
    
    if response_start == -1:
        raise Exception("No Response found")
    
    response_json_str = output_text[response_start + len('Response:'):].strip()
    response_json_str = response_json_str.replace('\n', ' ')
    
    try:
        response_data = json.loads(response_json_str)
        
        if isinstance(response_data, dict) and 'result' in response_data:
            result_data = response_data['result']
            if isinstance(result_data, dict) and 'content' in result_data:
                content = result_data['content']
                if isinstance(content, list) and len(content) > 0:
                    text = content[0].get('text', '')
                    return {
                        'output': text,
                        'sessionId': session_id
                    }
        
        return {
            'output': response_json_str,
            'sessionId': session_id
        }
    except Exception:
        return {
            'output': response_json_str,
            'sessionId': session_id
        }

if __name__ == '__main__':
    data = json.loads(sys.stdin.read())
    result = invoke_agent(data['prompt'], data.get('sessionId'))
    print(json.dumps(result))
```

### File: `backend/package.json`

```json
{
  "name": "agentcore-backend",
  "version": "1.0.0",
  "dependencies": {
    "express": "^4.18.2",
    "cors": "^2.8.5"
  },
  "scripts": {
    "start": "node server.js"
  }
}
```

---

## 4. React Integration

### Update your React component:

```javascript
import React, { useState } from 'react';

function ChatWithAgent() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [sessionId, setSessionId] = useState('');
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim()) return;

    setLoading(true);
    setMessages(prev => [...prev, { role: 'user', content: input }]);
    
    try {
      const response = await fetch('http://localhost:3001/api/invoke-agent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          inputText: input,
          sessionId: sessionId
        })
      });

      const data = await response.json();
      
      if (data.sessionId && !sessionId) {
        setSessionId(data.sessionId);
      }

      setMessages(prev => [...prev, { 
        role: 'agent', 
        content: data.output 
      }]);
    } catch (error) {
      setMessages(prev => [...prev, { 
        role: 'error', 
        content: error.message 
      }]);
    } finally {
      setLoading(false);
      setInput('');
    }
  };

  return (
    <div>
      <div className="messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={msg.role}>
            {msg.content}
          </div>
        ))}
      </div>
      
      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
        disabled={loading}
      />
      
      <button onClick={sendMessage} disabled={loading}>
        {loading ? 'Sending...' : 'Send'}
      </button>
    </div>
  );
}

export default ChatWithAgent;
```

---

## 5. Tool Examples

### Time Tool
```python
@tool
def get_current_time() -> str:
    """Get current date and time."""
    from datetime import datetime
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
```

### Calculator Tool
```python
@tool
def calculate(expression: str) -> str:
    """Evaluate math expression."""
    try:
        result = eval(expression)
        return f"Result: {result}"
    except:
        return "Invalid expression"
```

### API Call Tool
```python
@tool
def fetch_data(endpoint: str) -> str:
    """Fetch data from API."""
    import requests
    response = requests.get(endpoint)
    return response.json()
```

### Database Query Tool
```python
@tool
def query_database(sql: str) -> str:
    """Query database."""
    # Your DB logic
    return "Query results"
```

---

## 6. IAM Permissions Required

### For AgentCore Deployment
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock-agentcore:*",
        "bedrock:InvokeModel",
        "iam:CreateRole",
        "iam:AttachRolePolicy",
        "ecr:*",
        "codebuild:*",
        "logs:*"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## 7. Common Issues & Solutions

### Issue: "Session ID too short"
**Solution:** Session IDs must be 33+ characters. Use UUID:
```python
import uuid
session_id = str(uuid.uuid4())  # 36 chars
```

### Issue: "No response from agent"
**Solution:** Check backend logs, ensure agentcore CLI is installed:
```bash
pip install bedrock-agentcore-starter-toolkit
```

### Issue: "Tool not being called"
**Solution:** 
1. Check tool docstring is descriptive
2. Update system prompt to mention the tool
3. Make user prompt more explicit

### Issue: "JSON parsing error"
**Solution:** Response has newlines, replace them:
```python
response_json_str = response_json_str.replace('\n', ' ')
```

---

## 8. Deployment to Production

### ECS Fargate Dockerfile
```dockerfile
FROM node:18-slim

RUN apt-get update && apt-get install -y python3 python3-pip
RUN pip3 install bedrock-agentcore strands-agents bedrock-agentcore-starter-toolkit

WORKDIR /app
COPY package*.json ./
RUN npm install --production

COPY . .

EXPOSE 3001
CMD ["node", "server.js"]
```

### Build and Deploy
```bash
# Build
docker build -t my-backend .

# Push to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
docker tag my-backend:latest <account>.dkr.ecr.us-east-1.amazonaws.com/my-backend:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/my-backend:latest

# Deploy to ECS
aws ecs update-service --cluster my-cluster --service my-service --force-new-deployment
```

---

## 9. Cost Estimates

- **AgentCore Runtime:** ~$0.01-0.10 per 1000 invocations
- **Claude Model:** ~$0.003 per 1K input tokens, ~$0.015 per 1K output tokens
- **ECS Fargate:** ~$15-30/month (0.25 vCPU, 0.5 GB)
- **Typical app:** ~$50-100/month for moderate usage

---

## 10. Key Concepts

### How Tool Calling Works
1. User asks question
2. Agent analyzes with Claude
3. Claude decides if tool needed
4. If yes: Strands executes tool function
5. Result sent back to Claude
6. Claude generates final response

### Session Management
- Sessions maintain conversation context
- Short-term memory: 30 days
- Long-term memory: Optional, extracts preferences

### AgentCore vs Bedrock Agents
- **AgentCore:** Framework-agnostic, bring your own agent
- **Bedrock Agents:** AWS-managed, predefined structure
- **AgentCore:** More flexible, supports Strands, LangChain, CrewAI

---

## 11. Testing Checklist

- [ ] Agent deploys successfully
- [ ] CLI invocation works
- [ ] Backend receives requests
- [ ] Python bridge executes
- [ ] Session IDs are valid (33+ chars)
- [ ] Tools are called correctly
- [ ] Responses are parsed properly
- [ ] React UI displays messages
- [ ] Error handling works
- [ ] Logs are accessible

---

## 12. Useful Commands

```bash
# Check agent status
agentcore status

# View logs
agentcore logs --follow

# Test locally
agentcore invoke '{"prompt": "test"}'

# Redeploy after changes
agentcore launch

# Delete agent
agentcore delete

# Check AWS credentials
aws sts get-caller-identity

# View CloudWatch logs
aws logs tail /aws/bedrock-agentcore/runtimes/<agent-id> --follow
```

---

## Summary

To implement in ANY project:

1. **Create agent/** folder with `my_agent.py` and `requirements.txt`
2. **Deploy:** `agentcore configure` → `agentcore launch`
3. **Create backend/** with `server.js` and `invoke-agentcore.py`
4. **Update React** to call `/api/invoke-agent`
5. **Test** and iterate

That's it! This pattern works for any application that needs AI agent capabilities.

---

**Agent ARN from this project:**
`arn:aws:bedrock-agentcore:us-east-1:164543933824:runtime/my_agent-vA6v5I2WBD`

**Region:** us-east-1
**Framework:** Strands
**Runtime:** AgentCore
