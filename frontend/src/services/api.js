// Use environment variable or default to localhost
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:3001';

async function callBackend(inputText) {
  const response = await fetch(`${BACKEND_URL}/api/invoke-agent`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ inputText })
  });
  
  if (!response.ok) {
    throw new Error(`Backend error: ${response.status}`);
  }
  
  const data = await response.json();
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
    const response = await callBackend(prompt);
    
    // The agent returns data in format: "DATA: {...json...}\n\nAnalysis text"
    try {
      // Look for DATA: prefix
      const dataMatch = response.match(/DATA:\s*(\{[\s\S]*?\})\s*\n/);
      if (dataMatch) {
        const parsed = JSON.parse(dataMatch[1]);
        // Remove the DATA: line from analysis
        const analysisText = response.replace(/DATA:[\s\S]*?\}\s*\n/, '').trim();
        
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

  async chatWithAI(question, bankName) {
    const response = await callBackend(`${question} about ${bankName}`);
    return { response, sources: [] };
  },

  async generateFullReport(bankName) {
    return callBackend(`Generate comprehensive financial report for ${bankName}`);
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
  }
};