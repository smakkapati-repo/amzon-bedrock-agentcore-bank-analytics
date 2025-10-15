// Direct AgentCore integration
window.callAgentCore = async function(prompt) {
  const response = await fetch('https://bedrock-agentcore.us-east-1.amazonaws.com/invoke-agent-runtime', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'AWS4-HMAC-SHA256 ...' // This needs proper AWS signing
    },
    body: JSON.stringify({
      agentRuntimeArn: 'arn:aws:bedrock-agentcore:us-east-1:164543933824:runtime/banking_gateway_agent-NBHIhnGMhL',
      payload: JSON.stringify({ prompt }),
      runtimeUserId: `user_${Date.now()}`
    })
  });
  
  return response.text();
};