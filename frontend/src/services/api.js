const API_BASE = window.location.origin;

export const api = {
  // FDIC Banking Data
  async getFDICData() {
    const response = await fetch(`${API_BASE}/api/fdic-data`);
    return response.json();
  },

  // Peer Analytics
  async analyzePeers(baseBank, peerBanks, metric) {
    const response = await fetch(`${API_BASE}/api/analyze-peers`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ baseBank, peerBanks, metric })
    });
    return response.json();
  },

  // SEC Reports
  async getSECReports(bankName, year, useRAG = true, cik = null) {
    const liveParam = useRAG ? '' : '&live=true';
    const cikParam = cik ? `&cik=${cik}` : '';
    const response = await fetch(`${API_BASE}/api/sec-reports/${bankName}?year=${year}${liveParam}${cikParam}`);
    return response.json();
  },

  // AI Chat
  async chatWithAI(question, bankName, context, useRAG = true, cik = null) {
    const response = await fetch(`${API_BASE}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, bankName, context, useRAG, cik })
    });
    return response.json();
  },

  // Generate Full Report
  async generateFullReport(bankName, reports) {
    const response = await fetch(`${API_BASE}/api/generate-report`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ bankName, reports })
    });
    return response.json();
  },

  // Search Banks
  async searchBanks(query) {
    const response = await fetch(`${API_BASE}/api/search-banks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });
    return response.json();
  },

  // Chat with Local Files
  async chatWithLocalFiles(formData) {
    const response = await fetch(`${API_BASE}/api/chat-local`, {
      method: 'POST',
      body: formData
    });
    return response.json();
  }
};