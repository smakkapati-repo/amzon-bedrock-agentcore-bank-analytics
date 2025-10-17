const express = require('express');
const cors = require('cors');
const AWS = require('aws-sdk');
const https = require('https');
const { spawn } = require('child_process');
const path = require('path');

// Configure AWS SDK - will automatically use ECS task role
AWS.config.update({ region: process.env.REGION || 'us-east-1' });

const app = express();
const PORT = process.env.PORT || 3001;

app.use(cors());
app.use(express.json({ limit: '50mb' }));

// In-memory job storage (in production, use DynamoDB or Redis)
const jobs = new Map();

// Job statuses
const JOB_STATUS = {
  PENDING: 'pending',
  PROCESSING: 'processing',
  COMPLETED: 'completed',
  FAILED: 'failed'
};

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', service: 'BankIQ+ Backend' });
});

app.get('/api/health', (req, res) => {
  res.json({ status: 'healthy', service: 'BankIQ+ Backend' });
});

// Main agent invocation endpoint
app.post('/api/invoke-agent', async (req, res) => {
  const { inputText, sessionId } = req.body;

  if (!inputText) {
    return res.status(400).json({ error: 'Missing inputText' });
  }

  console.log(`[${new Date().toISOString()}] Invoking agent: ${inputText.substring(0, 100)}...`);

  try {
    // Get agent ARN from environment
    const agentRuntimeArn = process.env.AGENTCORE_AGENT_ARN || 
      'arn:aws:bedrock-agentcore:us-east-1:164543933824:runtime/bank_iq_agent_v1-f98stM8Sv9';
    
    const region = process.env.REGION || 'us-east-1';
    // Session ID must be at least 33 characters (make it 40+ to be safe)
    const runtimeSessionId = sessionId || `session-${Date.now()}-${Math.random().toString(36).substring(2)}-${Math.random().toString(36).substring(2)}`;
    
    // Prepare request payload
    const payload = JSON.stringify({ prompt: inputText });
    
    // Build API endpoint
    const host = `bedrock-agentcore.${region}.amazonaws.com`;
    const path = `/runtimes/${encodeURIComponent(agentRuntimeArn)}/invocations`;
    
    console.log(`[${new Date().toISOString()}] Invoking AgentCore via HTTPS API...`);
    
    // Ensure credentials are loaded
    await new Promise((resolve, reject) => {
      AWS.config.getCredentials((err) => {
        if (err) reject(err);
        else resolve();
      });
    });
    
    // Sign the request using AWS Signature V4
    const endpoint = new AWS.Endpoint(host);
    const request = new AWS.HttpRequest(endpoint, region);
    
    request.method = 'POST';
    request.path = path;
    request.headers['Host'] = host;
    request.headers['Content-Type'] = 'application/json';
    request.headers['X-Amzn-Bedrock-AgentCore-Runtime-Session-Id'] = runtimeSessionId;
    request.body = payload;
    
    // Sign the request
    const signer = new AWS.Signers.V4(request, 'bedrock-agentcore');
    signer.addAuthorization(AWS.config.credentials, new Date());
    
    // Make HTTPS request
    const response = await new Promise((resolve, reject) => {
      const options = {
        hostname: host,
        path: request.path,
        method: request.method,
        headers: request.headers
      };
      
      const req = https.request(options, (res) => {
        let data = '';
        
        res.on('data', (chunk) => {
          data += chunk;
        });
        
        res.on('end', () => {
          if (res.statusCode >= 200 && res.statusCode < 300) {
            resolve({ statusCode: res.statusCode, body: data });
          } else {
            reject(new Error(`HTTP ${res.statusCode}: ${data}`));
          }
        });
      });
      
      req.on('error', reject);
      req.write(payload);
      req.end();
    });
    
    // Parse response
    const result = JSON.parse(response.body);
    
    // Extract text from nested structure: result.content[0].text or result.role/content
    let output = 'No response';
    if (result.content && Array.isArray(result.content) && result.content[0]?.text) {
      output = result.content[0].text;
    } else if (result.output) {
      output = result.output;
    } else if (result.response) {
      output = result.response;
    } else if (result.message) {
      output = result.message;
    }
    
    console.log(`[${new Date().toISOString()}] Agent response received from AgentCore`);
    
    res.json({
      output: output,
      sessionId: runtimeSessionId,
      runtime: 'AgentCore-HTTPS-ECS'
    });
  } catch (error) {
    console.error('Agent invocation error:', error);
    res.status(500).json({ 
      error: error.message,
      code: error.code || 'Unknown'
    });
  }
});

// Store CSV data endpoint (for local mode)
app.post('/api/store-csv-data', (req, res) => {
  const { data, filename } = req.body;
  console.log(`[${new Date().toISOString()}] Stored CSV data: ${filename} (${data.length} rows)`);
  // In production, you'd store this in a database or S3
  // For now, just acknowledge receipt
  res.json({ success: true, message: 'CSV data received', rows: data.length });
});

// Analyze local CSV data endpoint
app.post('/api/analyze-local-data', async (req, res) => {
  const { data, baseBank, peerBanks, metric } = req.body;
  
  console.log(`[${new Date().toISOString()}] Analyzing local CSV data: ${baseBank} vs ${peerBanks.join(', ')} on ${metric}`);
  
  try {
    // Format the data for the agent
    const inputText = `Analyze this peer banking data comparing ${baseBank} vs ${peerBanks.join(', ')} on metric: ${metric}. 

Data summary: ${data.length} data points
Sample: ${JSON.stringify(data.slice(0, 3))}

Provide a 2-paragraph analysis highlighting:
1. Performance comparison between the banks
2. Key trends and insights from the data

Keep it concise and business-focused.`;
    
    // Get agent ARN from environment
    const agentRuntimeArn = process.env.AGENTCORE_AGENT_ARN || 
      'arn:aws:bedrock-agentcore:us-east-1:164543933824:runtime/bank_iq_agent_v1-f98stM8Sv9';
    
    const region = process.env.REGION || 'us-east-1';
    const runtimeSessionId = `session-${Date.now()}-${Math.random().toString(36).substring(2)}-${Math.random().toString(36).substring(2)}`;
    
    const payload = JSON.stringify({ prompt: inputText });
    const host = `bedrock-agentcore.${region}.amazonaws.com`;
    const path = `/runtimes/${encodeURIComponent(agentRuntimeArn)}/invocations`;
    
    await new Promise((resolve, reject) => {
      AWS.config.getCredentials((err) => {
        if (err) reject(err);
        else resolve();
      });
    });
    
    const endpoint = new AWS.Endpoint(host);
    const request = new AWS.HttpRequest(endpoint, region);
    
    request.method = 'POST';
    request.path = path;
    request.headers['Host'] = host;
    request.headers['Content-Type'] = 'application/json';
    request.headers['X-Amzn-Bedrock-AgentCore-Runtime-Session-Id'] = runtimeSessionId;
    request.body = payload;
    
    const signer = new AWS.Signers.V4(request, 'bedrock-agentcore');
    signer.addAuthorization(AWS.config.credentials, new Date());
    
    const response = await new Promise((resolve, reject) => {
      const options = {
        hostname: host,
        path: request.path,
        method: request.method,
        headers: request.headers
      };
      
      const req = https.request(options, (res) => {
        let data = '';
        res.on('data', (chunk) => { data += chunk; });
        res.on('end', () => {
          if (res.statusCode >= 200 && res.statusCode < 300) {
            resolve({ statusCode: res.statusCode, body: data });
          } else {
            reject(new Error(`HTTP ${res.statusCode}: ${data}`));
          }
        });
      });
      
      req.on('error', reject);
      req.write(payload);
      req.end();
    });
    
    const result = JSON.parse(response.body);
    let output = 'No response';
    if (result.content && Array.isArray(result.content) && result.content[0]?.text) {
      output = result.content[0].text;
    } else if (result.output) {
      output = result.output;
    }
    
    console.log(`[${new Date().toISOString()}] Analysis complete`);
    res.json({ analysis: output });
    
  } catch (error) {
    console.error(`[${new Date().toISOString()}] Analysis error:`, error);
    res.status(500).json({ error: error.message });
  }
});

// Upload PDF documents endpoint
app.post('/api/upload-pdf', async (req, res) => {
  const { files, bankName } = req.body;
  
  if (!files || files.length === 0) {
    return res.status(400).json({ error: 'No files provided' });
  }
  
  try {
    console.log(`[${new Date().toISOString()}] Processing ${files.length} PDF(s)...`);
    
    // Process each file
    const documents = [];
    
    for (const file of files) {
      // Step 1: Extract metadata using PyPDF2
      console.log(`[${new Date().toISOString()}] Extracting metadata from ${file.name}...`);
      
      const extractPython = spawn('python3', [path.join(__dirname, 'extract_pdf_metadata.py')]);
      
      let extractOutput = '';
      let extractError = '';
      
      await new Promise((resolve, reject) => {
        extractPython.stdout.on('data', (d) => { extractOutput += d.toString(); });
        extractPython.stderr.on('data', (d) => { extractError += d.toString(); });
        
        extractPython.stdin.write(JSON.stringify({ 
          pdf_content: file.content,
          filename: file.name
        }));
        extractPython.stdin.end();
        
        extractPython.on('close', (code) => {
          if (extractError) {
            console.log(`[${new Date().toISOString()}] Python stderr:`, extractError);
          }
          if (code !== 0) {
            console.error('Metadata extraction error:', extractError);
            resolve(); // Don't fail, use fallback
          } else {
            resolve();
          }
        });
      });
      
      // Parse extracted metadata
      let metadata = {
        bank_name: bankName || 'Unknown Bank',
        form_type: '10-K',
        year: new Date().getFullYear()
      };
      
      console.log(`[${new Date().toISOString()}] Raw extraction output:`, extractOutput.substring(0, 200));
      if (extractError) {
        console.error(`[${new Date().toISOString()}] Extraction stderr:`, extractError);
      }
      
      try {
        const extracted = JSON.parse(extractOutput);
        console.log(`[${new Date().toISOString()}] Parsed extraction result:`, JSON.stringify(extracted));
        
        if (extracted.success) {
          metadata = {
            bank_name: extracted.bank_name,
            form_type: extracted.form_type,
            year: extracted.year
          };
          console.log(`[${new Date().toISOString()}] ✅ Extracted: ${metadata.bank_name} ${metadata.form_type} ${metadata.year}`);
        } else {
          console.error(`[${new Date().toISOString()}] ❌ Extraction failed:`, extracted.error);
        }
      } catch (e) {
        console.error(`[${new Date().toISOString()}] ❌ Failed to parse metadata:`, e.message);
        console.error(`[${new Date().toISOString()}] Raw output was:`, extractOutput);
      }
      
      // Step 2: Upload to S3
      let s3Key = null;
      try {
        const AWS = require('aws-sdk');
        const s3 = new AWS.S3();
        
        // Generate S3 key: uploaded-docs/{bank_name}/{year}/{form_type}/{filename}
        const sanitizedBankName = metadata.bank_name.replace(/[^a-zA-Z0-9]/g, '_');
        s3Key = `uploaded-docs/${sanitizedBankName}/${metadata.year}/${metadata.form_type}/${file.name}`;
        
        // Decode base64 and upload
        const pdfBuffer = Buffer.from(file.content, 'base64');
        
        await s3.putObject({
          Bucket: process.env.UPLOADED_DOCS_BUCKET || 'bankiq-uploaded-docs',
          Key: s3Key,
          Body: pdfBuffer,
          ContentType: 'application/pdf',
          Metadata: {
            'bank-name': metadata.bank_name,
            'form-type': metadata.form_type,
            'year': metadata.year.toString(),
            'original-filename': file.name
          }
        }).promise();
        
        console.log(`[${new Date().toISOString()}] ✅ Uploaded to S3: ${s3Key}`);
      } catch (s3Error) {
        console.error(`[${new Date().toISOString()}] ❌ S3 upload failed:`, s3Error.message);
        // Continue anyway, just without S3 key
      }
      
      documents.push({
        bank_name: metadata.bank_name,
        form_type: metadata.form_type,
        year: metadata.year,
        filename: file.name,
        size: file.size,
        s3_key: s3Key
      });
    }
    
    console.log(`[${new Date().toISOString()}] Processed ${documents.length} document(s):`, 
      documents.map(d => `${d.bank_name} ${d.form_type} ${d.year}`).join(', '));
    res.json({ success: true, documents });
    
  } catch (error) {
    console.error('Upload error:', error);
    res.status(500).json({ error: error.message });
  }
});

// Direct SEC filings endpoint (bypasses agent for faster results)
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
    
    // Extract 10-K and 10-Q filings
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

// Direct bank search endpoint (bypasses agent for faster results)
app.post('/api/search-banks', async (req, res) => {
  const { query } = req.body;
  
  if (!query) {
    return res.status(400).json({ error: 'Missing query' });
  }
  
  try {
    console.log(`[${new Date().toISOString()}] Searching for banks: ${query}`);
    
    // Major banks cache
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
        
        // Search SEC company tickers endpoint
        const edgarUrl = 'https://www.sec.gov/files/company_tickers.json';
        const edgarResponse = await axios.get(edgarUrl, {
          headers: { 'User-Agent': 'BankIQ Analytics contact@bankiq.com' },
          timeout: 5000
        });
        
        const companies = Object.values(edgarResponse.data);
        
        // Search in SEC data
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

// Async job submission endpoint
app.post('/api/jobs/submit', async (req, res) => {
  const { inputText, sessionId, jobType } = req.body;

  if (!inputText) {
    return res.status(400).json({ error: 'Missing inputText' });
  }

  // Generate job ID
  const jobId = `job-${Date.now()}-${Math.random().toString(36).substring(2, 10)}`;
  
  // Create job record
  jobs.set(jobId, {
    jobId,
    status: JOB_STATUS.PENDING,
    inputText,
    sessionId,
    jobType: jobType || 'agent-invocation',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  });

  console.log(`[${new Date().toISOString()}] Job ${jobId} created: ${inputText.substring(0, 100)}...`);

  // Start processing asynchronously (don't await)
  processJob(jobId).catch(err => {
    console.error(`[${new Date().toISOString()}] Job ${jobId} failed:`, err);
    const job = jobs.get(jobId);
    if (job) {
      job.status = JOB_STATUS.FAILED;
      job.error = err.message;
      job.updatedAt = new Date().toISOString();
    }
  });

  // Return job ID immediately
  res.json({ jobId, status: JOB_STATUS.PENDING });
});

// Job status check endpoint
app.get('/api/jobs/:jobId', (req, res) => {
  const { jobId } = req.params;
  const job = jobs.get(jobId);

  if (!job) {
    return res.status(404).json({ error: 'Job not found' });
  }

  // Return job status (without full result to keep response small)
  res.json({
    jobId: job.jobId,
    status: job.status,
    createdAt: job.createdAt,
    updatedAt: job.updatedAt,
    hasResult: !!job.result
  });
});

// Job result retrieval endpoint
app.get('/api/jobs/:jobId/result', (req, res) => {
  const { jobId } = req.params;
  const job = jobs.get(jobId);

  if (!job) {
    return res.status(404).json({ error: 'Job not found' });
  }

  if (job.status === JOB_STATUS.PENDING || job.status === JOB_STATUS.PROCESSING) {
    return res.json({ 
      jobId: job.jobId,
      status: job.status,
      message: 'Job still processing'
    });
  }

  if (job.status === JOB_STATUS.FAILED) {
    return res.status(500).json({
      jobId: job.jobId,
      status: job.status,
      error: job.error
    });
  }

  // Return full result
  res.json({
    jobId: job.jobId,
    status: job.status,
    result: job.result,
    sessionId: job.sessionId,
    createdAt: job.createdAt,
    completedAt: job.updatedAt
  });
});

// Process job asynchronously
async function processJob(jobId) {
  const job = jobs.get(jobId);
  if (!job) return;

  try {
    // Update status to processing
    job.status = JOB_STATUS.PROCESSING;
    job.updatedAt = new Date().toISOString();

    console.log(`[${new Date().toISOString()}] Processing job ${jobId}...`);

    // Get agent ARN from environment
    const agentRuntimeArn = process.env.AGENTCORE_AGENT_ARN || 
      'arn:aws:bedrock-agentcore:us-east-1:164543933824:runtime/bank_iq_agent_v1-f98stM8Sv9';
    
    const region = process.env.REGION || 'us-east-1';
    const runtimeSessionId = job.sessionId || `session-${Date.now()}-${Math.random().toString(36).substring(2)}-${Math.random().toString(36).substring(2)}`;
    
    const payload = JSON.stringify({ prompt: job.inputText });
    const host = `bedrock-agentcore.${region}.amazonaws.com`;
    const path = `/runtimes/${encodeURIComponent(agentRuntimeArn)}/invocations`;
    
    // Ensure credentials are loaded
    await new Promise((resolve, reject) => {
      AWS.config.getCredentials((err) => {
        if (err) reject(err);
        else resolve();
      });
    });
    
    // Sign the request
    const endpoint = new AWS.Endpoint(host);
    const request = new AWS.HttpRequest(endpoint, region);
    
    request.method = 'POST';
    request.path = path;
    request.headers['Host'] = host;
    request.headers['Content-Type'] = 'application/json';
    request.headers['X-Amzn-Bedrock-AgentCore-Runtime-Session-Id'] = runtimeSessionId;
    request.body = payload;
    
    const signer = new AWS.Signers.V4(request, 'bedrock-agentcore');
    signer.addAuthorization(AWS.config.credentials, new Date());
    
    // Make HTTPS request (no timeout limit)
    const response = await new Promise((resolve, reject) => {
      const options = {
        hostname: host,
        path: request.path,
        method: request.method,
        headers: request.headers
      };
      
      const req = https.request(options, (res) => {
        let data = '';
        res.on('data', (chunk) => { data += chunk; });
        res.on('end', () => {
          if (res.statusCode >= 200 && res.statusCode < 300) {
            resolve({ statusCode: res.statusCode, body: data });
          } else {
            reject(new Error(`HTTP ${res.statusCode}: ${data}`));
          }
        });
      });
      
      req.on('error', reject);
      req.write(payload);
      req.end();
    });
    
    // Parse response
    const result = JSON.parse(response.body);
    let output = 'No response';
    if (result.content && Array.isArray(result.content) && result.content[0]?.text) {
      output = result.content[0].text;
    } else if (result.output) {
      output = result.output;
    } else if (result.response) {
      output = result.response;
    } else if (result.message) {
      output = result.message;
    }
    
    // Update job with result
    job.status = JOB_STATUS.COMPLETED;
    job.result = output;
    job.sessionId = runtimeSessionId;
    job.updatedAt = new Date().toISOString();

    console.log(`[${new Date().toISOString()}] Job ${jobId} completed successfully`);

  } catch (error) {
    console.error(`[${new Date().toISOString()}] Job ${jobId} failed:`, error);
    job.status = JOB_STATUS.FAILED;
    job.error = error.message;
    job.updatedAt = new Date().toISOString();
  }
}

// Cleanup old jobs (run every 10 minutes)
setInterval(() => {
  const now = Date.now();
  const maxAge = 30 * 60 * 1000; // 30 minutes
  
  for (const [jobId, job] of jobs.entries()) {
    const jobAge = now - new Date(job.createdAt).getTime();
    if (jobAge > maxAge) {
      jobs.delete(jobId);
      console.log(`[${new Date().toISOString()}] Cleaned up old job: ${jobId}`);
    }
  }
}, 10 * 60 * 1000);


app.listen(PORT, () => {
  console.log(`✅ BankIQ+ Backend running on port ${PORT}`);
  console.log(`   Health check: http://localhost:${PORT}/health`);
  console.log(`   Agent API: http://localhost:${PORT}/api/invoke-agent`);
  console.log(`   Async Jobs: http://localhost:${PORT}/api/jobs/submit`);
  console.log(`   CSV Storage: http://localhost:${PORT}/api/store-csv-data`);
  console.log(`   CSV Analysis: http://localhost:${PORT}/api/analyze-local-data`);
  console.log(`   Bank Search: http://localhost:${PORT}/api/search-banks`);
});
