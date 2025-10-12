/**
 * AgentCore Service - Handles communication with AgentCore backend
 */
class AgentService {
  constructor() {
    this.baseURL = window.location.origin;
    this.websocket = null;
    this.eventSource = null;
    this.listeners = new Map();
    this.connected = false;
  }

  // HTTP connection for Strands agent
  async connectAgent() {
    try {
      const response = await fetch(`${this.baseURL}/api/agent-status`);
      const status = await response.json();
      
      if (status.status === 'connected') {
        this.connected = true;
        this.emit('connection', { status: 'connected', method: 'http' });
        console.log('Strands Agent connected via HTTP');
      }
    } catch (error) {
      this.connected = false;
      this.emit('connection', { status: 'disconnected' });
      console.log('Agent connection failed');
    }
  }

  // Send message via WebSocket
  sendWebSocketMessage(type, data) {
    if (this.websocket?.readyState === WebSocket.OPEN) {
      this.websocket.send(JSON.stringify({ type, ...data }));
      return true;
    }
    return false;
  }

  // Chat with AI using agents
  async chatWithAgent(question, bankName, useRAG = true) {
    // Try WebSocket first
    if (this.sendWebSocketMessage('chat_question', {
      question,
      bank_name: bankName,
      use_rag: useRAG
    })) {
      return { streaming: true, method: 'websocket' };
    }

    // Fallback to HTTP
    const response = await fetch(`${this.baseURL}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question,
        bankName,
        useRAG
      })
    });

    return await response.json();
  }

  // Generate report with streaming
  async generateReport(bankName, mode = 'rag') {
    // Try WebSocket first
    if (this.sendWebSocketMessage('generate_report', {
      bank_name: bankName,
      mode
    })) {
      return { streaming: true, method: 'websocket' };
    }

    // Fallback to SSE
    return this.generateReportSSE(bankName, mode);
  }

  // SSE fallback for report generation
  generateReportSSE(bankName, mode) {
    return new Promise((resolve, reject) => {
      this.eventSource = new EventSource(`${this.baseURL}/api/generate-report`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ bankName, mode })
      });

      this.eventSource.onmessage = (event) => {
        if (event.data === '[DONE]') {
          this.eventSource.close();
          resolve({ streaming: true, method: 'sse', status: 'complete' });
          return;
        }

        try {
          const data = JSON.parse(event.data);
          this.emit('report_chunk', data);
        } catch (e) {
          this.emit('report_chunk', { chunk: event.data });
        }
      };

      this.eventSource.onerror = (error) => {
        console.error('SSE error:', error);
        this.eventSource.close();
        reject(error);
      };
    });
  }

  // Peer analysis using agents
  async analyzePeers(baseBank, peerBanks, metric) {
    // Try WebSocket first
    if (this.sendWebSocketMessage('peer_analysis', {
      base_bank: baseBank,
      peer_banks: peerBanks,
      metric
    })) {
      return { streaming: true, method: 'websocket' };
    }

    // Fallback to HTTP
    const response = await fetch(`${this.baseURL}/api/analyze-peers`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        baseBank,
        peerBanks,
        metric
      })
    });

    return await response.json();
  }

  // Event listener management
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  off(event, callback) {
    if (this.listeners.has(event)) {
      const callbacks = this.listeners.get(event);
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => callback(data));
    }
  }

  // Cleanup connections
  disconnect() {
    if (this.websocket) {
      this.websocket.close();
      this.websocket = null;
    }
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
    this.listeners.clear();
  }
}

export default new AgentService();