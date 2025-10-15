/**
 * BankIQ+ v2.0 Backend Lambda Handler
 * Wraps Express server for AWS Lambda + API Gateway
 */

const serverless = require('serverless-http');
const express = require('express');
const { spawn } = require('child_process');
const path = require('path');
const AWS = require('aws-sdk');

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

// CORS
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  if (req.method === 'OPTIONS') {
    return res.sendStatus(200);
  }
  next();
});

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'BankIQ+ v2.0 Backend', environment: 'Lambda' });
});

// Main agent invocation endpoint
app.post('/api/invoke-agent', async (req, res) => {
  const { inputText, sessionId } = req.body;

  if (!inputText) {
    return res.status(400).json({ error: 'Missing inputText' });
  }

  console.log(`[${new Date().toISOString()}] Invoking agent: ${inputText.substring(0, 100)}...`);

  try {
    // Use existing AgentCore deployment (same as v1.0)
    // AgentCore CLI is available in Lambda via Lambda Layer
    const { execSync } = require('child_process');
    
    const agentcoreCmd = sessionId 
      ? `agentcore invoke '${JSON.stringify({ prompt: inputText })}' --session-id ${sessionId}`
      : `agentcore invoke '${JSON.stringify({ prompt: inputText })}'`;
    
    const output = execSync(agentcoreCmd, {
      encoding: 'utf-8',
      maxBuffer: 10 * 1024 * 1024 // 10MB
    });
    
    const result = JSON.parse(output);
    console.log(`[${new Date().toISOString()}] Agent response received from AgentCore`);
    
    res.json({
      output: result.output || result.message || 'No response',
      sessionId: result.sessionId || sessionId,
      runtime: 'AgentCore'
    });
  } catch (error) {
    console.error('Agent invocation error:', error);
    res.status(500).json({ error: error.message });
  }
});

// Import all other routes from server.js
// (We'll need to refactor server.js to export routes)

// For now, include essential endpoints inline
// TODO: Refactor server.js to be Lambda-compatible

// Direct SEC filings endpoint
app.post('/api/get-sec-filings', async (req, res) => {
  const { bankName, cik } = req.body;
  
  if (!bankName && !cik) {
    return res.status(400).json({ error: 'Missing bankName or cik' });
  }
  
  try {
    console.log(`[${new Date().toISOString()}] Fetching SEC filings for ${bankName} (CIK: ${cik})`);
    
    const axios = require('axios');
    const targetCik = cik || '0000000000';
    
    if (targetCik === '0000000000') {
      return res.json({ success: false, error: 'Invalid CIK', '10-K': [], '10-Q': [] });
    }
    
    const headers = { 'User-Agent': 'BankIQ Analytics contact@bankiq.com' };
    const url = `https://data.sec.gov/submissions/CIK${targetCik}.json`;
    
    const response = await axios.get(url, { headers, timeout: 10000 });
    const data = response.data;
    const filings = data.filings?.recent || {};
    
    const forms = filings.form || [];
    const dates = filings.filingDate || [];
    const accessions = filings.accessionNumber || [];
    
    const tenK = [];
    const tenQ = [];
    
    for (let i = 0; i < forms.length; i++) {
      const form = forms[i];
      const date = dates[i];
      const accession = accessions[i];
      
      if (date && (date.startsWith('2024') || date.startsWith('2025'))) {
        const filing = {
          form: form,
          filing_date: date,
          accession: accession,
          url: `https://www.sec.gov/cgi-bin/viewer?action=view&cik=${targetCik.replace(/^0+/, '')}&accession_number=${accession}&xbrl_type=v`
        };
        
        if (form === '10-K') tenK.push(filing);
        else if (form === '10-Q') tenQ.push(filing);
      }
    }
    
    tenK.sort((a, b) => b.filing_date.localeCompare(a.filing_date));
    tenQ.sort((a, b) => b.filing_date.localeCompare(a.filing_date));
    
    console.log(`[${new Date().toISOString()}] Found ${tenK.length} 10-K and ${tenQ.length} 10-Q filings`);
    
    res.json({
      success: true,
      response: `Found ${tenK.length} 10-K and ${tenQ.length} 10-Q filings for ${bankName}`,
      '10-K': tenK.slice(0, 5),
      '10-Q': tenQ.slice(0, 10)
    });
    
  } catch (error) {
    console.error('SEC filings error:', error.message);
    res.json({ success: false, error: error.message, '10-K': [], '10-Q': [] });
  }
});

// Direct bank search endpoint
app.post('/api/search-banks', async (req, res) => {
  const { query } = req.body;
  
  if (!query) {
    return res.status(400).json({ error: 'Missing query' });
  }
  
  try {
    console.log(`[${new Date().toISOString()}] Searching for banks: ${query}`);
    
    const majorBanks = [
      {"name": "JPMORGAN CHASE & CO", "ticker": "JPM", "cik": "0000019617"},
      {"name": "BANK OF AMERICA CORP", "ticker": "BAC", "cik": "0000070858"},
      {"name": "WELLS FARGO & COMPANY", "ticker": "WFC", "cik": "0000072971"},
      {"name": "CITIGROUP INC", "ticker": "C", "cik": "0000831001"},
      {"name": "GOLDMAN SACHS GROUP INC", "ticker": "GS", "cik": "0000886982"},
      {"name": "MORGAN STANLEY", "ticker": "MS", "cik": "0000895421"},
      {"name": "U.S. BANCORP", "ticker": "USB", "cik": "0000036104"},
      {"name": "PNC FINANCIAL SERVICES GROUP INC", "ticker": "PNC", "cik": "0000713676"},
      {"name": "CAPITAL ONE FINANCIAL CORP", "ticker": "COF", "cik": "0000927628"},
      {"name": "TRUIST FINANCIAL CORP", "ticker": "TFC", "cik": "0001534701"},
      {"name": "CHARLES SCHWAB CORP", "ticker": "SCHW", "cik": "0000316709"},
      {"name": "BANK OF NEW YORK MELLON CORP", "ticker": "BK", "cik": "0001126328"},
      {"name": "STATE STREET CORP", "ticker": "STT", "cik": "0000093751"},
      {"name": "FIFTH THIRD BANCORP", "ticker": "FITB", "cik": "0000035527"},
      {"name": "CITIZENS FINANCIAL GROUP INC", "ticker": "CFG", "cik": "0000759944"},
      {"name": "KEYCORP", "ticker": "KEY", "cik": "0000091576"},
      {"name": "REGIONS FINANCIAL CORP", "ticker": "RF", "cik": "0001281761"},
      {"name": "M&T BANK CORP", "ticker": "MTB", "cik": "0000036270"},
      {"name": "HUNTINGTON BANCSHARES INC", "ticker": "HBAN", "cik": "0000049196"},
      {"name": "COMERICA INC", "ticker": "CMA", "cik": "0000028412"},
      {"name": "ZIONS BANCORPORATION", "ticker": "ZION", "cik": "0000109380"},
      {"name": "WEBSTER FINANCIAL CORP", "ticker": "WBS", "cik": "0000801337"},
      {"name": "FIRST HORIZON CORP", "ticker": "FHN", "cik": "0000036966"},
      {"name": "SYNOVUS FINANCIAL CORP", "ticker": "SNV", "cik": "0000312070"}
    ];
    
    const queryUpper = query.toUpperCase();
    const queryLower = query.toLowerCase();
    
    let results = majorBanks.filter(bank => 
      bank.name.toLowerCase().includes(queryLower) ||
      queryUpper === bank.ticker.toUpperCase() ||
      bank.ticker.toUpperCase().includes(queryUpper)
    );
    
    // If no results in cache, search SEC EDGAR
    if (results.length === 0) {
      try {
        const axios = require('axios');
        const edgarUrl = 'https://www.sec.gov/files/company_tickers.json';
        const edgarResponse = await axios.get(edgarUrl, {
          headers: { 'User-Agent': 'BankIQ Analytics contact@bankiq.com' },
          timeout: 5000
        });
        
        const companies = Object.values(edgarResponse.data);
        const edgarResults = companies.filter(company => 
          company.title.toLowerCase().includes(queryLower) ||
          (company.ticker && company.ticker.toUpperCase() === queryUpper)
        ).slice(0, 10);
        
        results = edgarResults.map(company => ({
          name: company.title,
          ticker: company.ticker || '',
          cik: String(company.cik_str).padStart(10, '0')
        }));
        
        console.log(`[${new Date().toISOString()}] Found ${results.length} companies in SEC EDGAR matching "${query}"`);
      } catch (edgarError) {
        console.error('SEC EDGAR search failed:', edgarError.message);
      }
    } else {
      console.log(`[${new Date().toISOString()}] Found ${results.length} banks in cache matching "${query}"`);
    }
    
    res.json({ success: true, results: results.slice(0, 10) });
    
  } catch (error) {
    console.error('Search error:', error);
    res.status(500).json({ error: error.message });
  }
});

// Export for Lambda
module.exports.handler = serverless(app);

// For local testing
if (require.main === module) {
  app.listen(PORT, () => {
    console.log(`✅ BankIQ+ v2.0 Backend running on port ${PORT}`);
    console.log(`   Environment: ${process.env.AGENT_LAMBDA_ARN ? 'Lambda' : 'Local'}`);
  });
}
