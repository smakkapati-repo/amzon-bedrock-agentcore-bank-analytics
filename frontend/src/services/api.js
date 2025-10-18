import { API_URL } from '../config';

// Use CloudFront URL for production
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || API_URL;

async function callBackend(inputText) {
  const response = await fetch(`${BACKEND_URL}/api/invoke-agent`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ inputText })
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Backend error: ${response.status}`);
  }
  
  const data = await response.json();
  
  // Check if backend returned an error in the response body
  if (data.error) {
    throw new Error(data.error);
  }
  
  return data.output;
}

export const api = {
  async getSECReports(bankName, year, useRag, cik) {
    // Use direct backend endpoint for faster, more reliable SEC filings
    if (cik && cik !== '0000000000') {
      try {
        const response = await fetch(`${BACKEND_URL}/api/get-sec-filings`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ bankName, cik })
        });
        
        const data = await response.json();
        
        if (data.success) {
          return {
            response: data.response,
            '10-K': data['10-K'] || [],
            '10-Q': data['10-Q'] || []
          };
        }
      } catch (e) {
        console.error('Direct SEC fetch failed:', e);
      }
    }
    
    // Fallback to agent
    let prompt = `Get all SEC filings for ${bankName} for years 2024 and 2025. I need both 10-K annual reports and 10-Q quarterly reports.`;
    const response = await callBackend(prompt);
    
    // Try to parse DATA: format first
    try {
      const dataMatch = response.match(/DATA:\s*(\{[\s\S]*?\})\s*\n/);
      if (dataMatch) {
        const parsed = JSON.parse(dataMatch[1]);
        if (parsed['10-K'] || parsed['10-Q']) {
          return { 
            response, 
            '10-K': (parsed['10-K'] || []).map(f => ({
              form: f.form_type,
              filing_date: f.filing_date,
              accession: f.accession_number,
              url: f.url
            })),
            '10-Q': (parsed['10-Q'] || []).map(f => ({
              form: f.form_type,
              filing_date: f.filing_date,
              accession: f.accession_number,
              url: f.url
            }))
          };
        }
      }
      
      // Fallback: Look for filings array
      const jsonMatch = response.match(/\{[\s\S]*?"filings"[\s\S]*?\[[\s\S]*?\][\s\S]*?\}/);
      if (jsonMatch) {
        const parsed = JSON.parse(jsonMatch[0]);
        if (parsed.filings && Array.isArray(parsed.filings)) {
          const tenK = parsed.filings.filter(f => f.form_type === '10-K');
          const tenQ = parsed.filings.filter(f => f.form_type === '10-Q');
          return { 
            response, 
            '10-K': tenK.map(f => ({
              form: f.form_type,
              filing_date: f.filing_date,
              accession: f.accession_number,
              url: f.url
            })),
            '10-Q': tenQ.map(f => ({
              form: f.form_type,
              filing_date: f.filing_date,
              accession: f.accession_number,
              url: f.url
            }))
          };
        }
      }
    } catch (e) {
      console.log('Could not parse SEC filings:', e);
    }
    
    return { response, '10-K': [], '10-Q': [] };
  },

  async analyzePeers(baseBank, peerBanks, metric) {
    const prompt = `Compare ${baseBank} vs ${peerBanks.join(', ')} using ${metric}`;
    
    // Use async job pattern
    const job = await this.submitJob(prompt);
    const result = await this.pollJobUntilComplete(job.jobId);
    const response = result.result;
    
    // The agent returns data in format: "DATA: {...json...}\n\nAnalysis text"
    try {
      // Look for DATA: prefix - handle both regular and escaped JSON
      const dataMatch = response.match(/DATA:\s*(\{[\s\S]*?\})(?:\s*\n|##)/);
      if (dataMatch) {
        const parsed = JSON.parse(dataMatch[1]);
        // Remove the DATA: line from analysis
        const analysisText = response.replace(/DATA:[\s\S]*?\}(?:\s*\n|##)/, '').trim();
        
        return { 
          success: true, 
          result: {
            data: parsed.data || [],
            analysis: analysisText || parsed.analysis || response,
            base_bank: parsed.base_bank || baseBank,
            peer_banks: parsed.peer_banks || peerBanks
          }
        };
      }
      
      // Fallback: Look for JSON object anywhere in the response
      const jsonMatch = response.match(/\{[\s\S]*?"data"[\s\S]*?\[[\s\S]*?\][\s\S]*?\}/);
      if (jsonMatch) {
        const parsed = JSON.parse(jsonMatch[0]);
        if (parsed.data && Array.isArray(parsed.data)) {
          // Remove JSON from analysis text
          const analysisText = response.replace(jsonMatch[0], '').trim();
          
          return { 
            success: true, 
            result: {
              data: parsed.data,
              analysis: analysisText || parsed.analysis || response,
              base_bank: parsed.base_bank || baseBank,
              peer_banks: parsed.peer_banks || peerBanks
            }
          };
        }
      }
    } catch (e) {
      console.log('Could not parse JSON from response:', e);
    }
    
    // If no structured data, return the text analysis
    return { 
      success: true, 
      result: { 
        analysis: response, 
        data: [],
        note: 'Analysis provided by AgentCore AI - chart data not available'
      } 
    };
  },

  async getFDICData() {
    const response = await callBackend('Get FDIC banking data for major banks');
    // Backend returns text response, we mark it as coming from AgentCore
    return { 
      success: true, 
      result: { 
        data: [], 
        data_source: 'AgentCore AI Analysis (FDIC Call Reports 2023-2025)' 
      } 
    };
  },

  async chatWithAI(question, bankName, reports, useRag, cik) {
    // Build context-aware prompt
    let prompt = question;
    
    if (bankName) {
      prompt = `${question} about ${bankName}`;
      
      // Add available reports context if provided
      if (reports && (reports['10-K']?.length > 0 || reports['10-Q']?.length > 0)) {
        const reportsList = [
          ...(reports['10-K'] || []).map(r => `${r.form} filed ${r.filing_date}`),
          ...(reports['10-Q'] || []).map(r => `${r.form} filed ${r.filing_date}`)
        ].slice(0, 5).join(', ');
        
        prompt += `. Available SEC filings: ${reportsList}`;
      }
    }
    
    const response = await callBackend(prompt);
    return { response, sources: [] };
  },

  async generateFullReport(bankName) {
    return callBackend(`Generate comprehensive financial report for ${bankName}`);
  },

  // Async job methods
  async submitJob(inputText, jobType = 'agent-invocation') {
    const response = await fetch(`${BACKEND_URL}/api/jobs/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ inputText, jobType })
    });
    
    if (!response.ok) {
      throw new Error(`Job submission failed: ${response.status}`);
    }
    
    return response.json();
  },

  async checkJobStatus(jobId) {
    const response = await fetch(`${BACKEND_URL}/api/jobs/${jobId}`);
    
    if (!response.ok) {
      throw new Error(`Job status check failed: ${response.status}`);
    }
    
    return response.json();
  },

  async getJobResult(jobId) {
    const response = await fetch(`${BACKEND_URL}/api/jobs/${jobId}/result`);
    
    if (!response.ok) {
      throw new Error(`Job result retrieval failed: ${response.status}`);
    }
    
    return response.json();
  },

  // Poll for job completion
  async pollJobUntilComplete(jobId, maxAttempts = 120, intervalMs = 2000) {
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      const status = await this.checkJobStatus(jobId);
      
      if (status.status === 'completed' || status.status === 'failed') {
        return this.getJobResult(jobId);
      }
      
      // Wait before next poll
      await new Promise(resolve => setTimeout(resolve, intervalMs));
    }
    
    throw new Error('Job polling timeout');
  },

  async searchBanks(query) {
    // Use direct backend endpoint for faster, more reliable search
    try {
      const response = await fetch(`${BACKEND_URL}/api/search-banks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });
      
      const data = await response.json();
      
      if (data.success && data.results) {
        console.log('Search results:', data.results);
        return data.results;
      }
      
      return [];
    } catch (e) {
      console.error('Search failed:', e);
      return [];
    }
  },

  async chatWithLocalFiles(formData) {
    const message = formData.get('message');
    const response = await callBackend(`Chat about documents: ${message}`);
    return { response, sources: [] };
  },

  async uploadPDFs(files, bankName = '') {
    const response = await fetch(`${BACKEND_URL}/api/upload-pdf`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ files, bankName })
    });
    
    if (!response.ok) {
      throw new Error(`Upload failed: ${response.status}`);
    }
    
    return response.json();
  },

  // Streaming method
  async callAgentStream(inputText, onChunk, onComplete, onError) {
    try {
      const response = await fetch(`${BACKEND_URL}/api/invoke-agent-stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ inputText })
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6));
            if (data.chunk) {
              onChunk(data.chunk);
            } else if (data.done) {
              onComplete();
            } else if (data.error) {
              onError(data.error);
            }
          }
        }
      }
    } catch (error) {
      onError(error.message);
    }
  }
};
