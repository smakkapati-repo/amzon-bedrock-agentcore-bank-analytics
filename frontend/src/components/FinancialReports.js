import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, Card, CardContent, Grid, Button,
  TextField, Paper, Chip, List, ListItem, ListItemText,
  CircularProgress, Alert, Switch, FormControlLabel, Autocomplete
} from '@mui/material';
import ChatIcon from '@mui/icons-material/Chat';
import DescriptionIcon from '@mui/icons-material/Description';
import DownloadIcon from '@mui/icons-material/Download';
import CloudIcon from '@mui/icons-material/Cloud';
import StorageIcon from '@mui/icons-material/Storage';
import SearchIcon from '@mui/icons-material/Search';
import { api } from '../services/api';

function FinancialReports() {
  const [selectedBank, setSelectedBank] = useState('');
  const [chatMessage, setChatMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [reports, setReports] = useState({ '10-K': [], '10-Q': [] });
  const [loading, setLoading] = useState(false);
  const [chatLoading, setChatLoading] = useState(false);
  const [error, setError] = useState('');
  const [fullReport, setFullReport] = useState('');
  const [reportLoading, setReportLoading] = useState(false);
  const [sources, setSources] = useState([]);
  const [mode, setMode] = useState('live'); // 'live' or 'local'
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [analyzedDocs, setAnalyzedDocs] = useState([]);
  const [searchBank, setSearchBank] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [selectedBankCik, setSelectedBankCik] = useState(null);

  const banks = [
    'JPMORGAN CHASE & CO', 'BANK OF AMERICA CORP', 'WELLS FARGO & COMPANY', 
    'CITIGROUP INC', 'U.S. BANCORP', 'PNC FINANCIAL SERVICES',
    'TRUIST FINANCIAL CORP', 'CAPITAL ONE FINANCIAL', 'REGIONS FINANCIAL CORP', 'FIFTH THIRD BANCORP'
  ];

  useEffect(() => {
    if (selectedBank && mode !== 'local') {
      loadReports();
    }
  }, [selectedBank, mode]);

  const loadReports = async () => {
    try {
      setLoading(true);
      const data = await api.getSECReports(selectedBank, 2024, mode === 'rag', selectedBankCik);
      setReports(data);
    } catch (err) {
      setError('Failed to load SEC reports');
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = async (predefinedMessage = null) => {
    const messageToSend = predefinedMessage || chatMessage;
    if (!messageToSend.trim()) return;
    
    if (!predefinedMessage) setChatMessage('');
    setChatHistory(prev => [...prev, { role: 'user', content: messageToSend }]);
    
    try {
      setChatLoading(true);
      
      // Add empty assistant message
      setChatHistory(prev => [...prev, { 
        role: 'assistant', 
        content: '',
        sources: []
      }]);
      
      let response;
      if (mode === 'local') {
        const formData = new FormData();
        formData.append('message', messageToSend);
        uploadedFiles.forEach(file => {
          formData.append('files', file);
        });
        response = await api.chatWithLocalFiles(formData);
      } else {
        response = await api.chatWithAI(messageToSend, selectedBank, reports, mode === 'rag', selectedBankCik);
      }
      setChatHistory(prev => {
        const newHistory = [...prev];
        const lastIndex = newHistory.length - 1;
        if (newHistory[lastIndex] && newHistory[lastIndex].role === 'assistant') {
          newHistory[lastIndex].content = response.response;
          newHistory[lastIndex].sources = response.sources || [];
        }
        return newHistory;
      });
      

      
    } catch (err) {
      setChatHistory(prev => [...prev, { role: 'assistant', content: 'Error: Failed to get AI response' }]);
    } finally {
      setChatLoading(false);
    }
  };

  const generateFullReport = async () => {
    try {
      setReportLoading(true);
      setFullReport('');
      setError('');
      
      const response = await fetch('/api/generate-report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ bankName: selectedBank, reports, useRAG: mode === 'rag', mode: mode, analyzedDocs: analyzedDocs })
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
            const dataContent = line.slice(6).trim();
            
            // Check for end of stream signal
            if (dataContent === '[DONE]') {
              setReportLoading(false);
              return;
            }
            
            try {
              const data = JSON.parse(dataContent);
              
              if (data.chunk) {
                setFullReport(prev => prev + data.chunk);
              }
              
              if (data.complete) {
                setFullReport(data.report);
                setReportLoading(false);
                return;
              }
              
              if (data.error) {
                setError(data.error);
                setReportLoading(false);
                return;
              }
            } catch (e) {
              // Skip invalid JSON
            }
          }
        }
      }
    } catch (err) {
      setError('Failed to generate full report');
      setReportLoading(false);
    }
  };

  const handleBankSearch = async () => {
    if (!searchBank.trim()) return;
    
    try {
      setSearching(true);
      setError('');
      setSearchResults([]);
      setSelectedBank('');
      setSelectedBankCik(null);
      setReports({ '10-K': [], '10-Q': [] });
      
      const results = await api.searchBanks(searchBank);
      setSearchResults(results);
      
      if (results.length === 0) {
        setError(`Sorry, I couldn't find "${searchBank}" in our supported banks database. Please search for banking and financial institutions only (e.g., Goldman Sachs, Morgan Stanley, Ally Financial).`);
      }
    } catch (err) {
      setError('Failed to search banks');
    } finally {
      setSearching(false);
    }
  };

  const downloadReport = () => {
    const bankName = selectedBank.replace(/[^a-zA-Z0-9]/g, '_');
    const element = document.createElement('a');
    const file = new Blob([fullReport], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = `${bankName}_Financial_Analysis_Report.txt`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 600 }}>
          Financial Reports Analyzer
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, p: 1, border: '1px solid #ddd', borderRadius: 2, backgroundColor: '#f5f5f5' }}>
          <Button 
            variant={mode === 'local' ? 'contained' : 'text'} 
            size="small"
            onClick={() => {
              setMode('local');
              setSelectedBank('');
              setChatHistory([]);
              setFullReport('');
              setReports({ '10-K': [], '10-Q': [] });
              setError('');
              setReportLoading(false);
            }}
            startIcon={<DescriptionIcon />}
            sx={{ minWidth: 80, fontSize: '0.8rem' }}
          >
            Local
          </Button>

          <Button 
            variant={mode === 'live' ? 'contained' : 'text'} 
            size="small"
            onClick={() => {
              setMode('live');
              setSelectedBank('');
              setChatHistory([]);
              setFullReport('');
              setReports({ '10-K': [], '10-Q': [] });
              setUploadedFiles([]);
              setAnalyzedDocs([]);
              setError('');
              setReportLoading(false);
            }}
            startIcon={<CloudIcon />}
            sx={{ minWidth: 80, fontSize: '0.8rem' }}
          >
            Live
          </Button>
        </Box>
      </Box>

      {/* Bank Selection */}
      <Grid container spacing={4} sx={{ mb: 4 }}>
        <Grid item xs={12}>
          {mode === 'live' ? (
            <>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <CloudIcon /> Live EDGAR Mode - Real-time SEC Data (Banking Companies Only)
              </Typography>
              <Grid container spacing={2}>
                {Object.entries({
                  "ALLY FINANCIAL INC": "0001479094",
                  "AMERICAN EXPRESS COMPANY": "0000004962",
                  "BANK OF NEW YORK MELLON CORP": "0001390777",
                  "BB&T CORPORATION": "0000092230",
                  "CHARLES SCHWAB CORPORATION": "0000316709",
                  "COMERICA INCORPORATED": "0000028412",
                  "DISCOVER FINANCIAL SERVICES": "0001393612",
                  "FIFTH THIRD BANCORP": "0000035527",
                  "FIRST REPUBLIC BANK": "0001132979",
                  "GOLDMAN SACHS GROUP INC": "0000886982",
                  "HUNTINGTON BANCSHARES INC": "0000049196",
                  "JPMORGAN CHASE & CO": "0000019617",
                  "KEYCORP": "0000091576",
                  "M&T BANK CORP": "0000036405",
                  "MORGAN STANLEY": "0000895421",
                  "NORTHERN TRUST CORP": "0000073124",
                  "PNC FINANCIAL SERVICES GROUP INC": "0000713676",
                  "REGIONS FINANCIAL CORP": "0001281761",
                  "STATE STREET CORP": "0000093751",
                  "SUNTRUST BANKS INC": "0000750556",
                  "SYNCHRONY FINANCIAL": "0001601712",
                  "TRUIST FINANCIAL CORP": "0001534701",
                  "U.S. BANCORP": "0000036104",
                  "WELLS FARGO & COMPANY": "0000072971",
                  "ZIONS BANCORPORATION": "0000109380",
                  "BANK OF AMERICA CORP": "0000070858",
                  "CITIGROUP INC": "0000831001",
                  "CAPITAL ONE FINANCIAL CORP": "0000927628"
                }).map(([bankName, cik]) => (
                  <Grid item key={bankName}>
                    <Button
                      variant={selectedBank === bankName ? 'contained' : 'outlined'}
                      onClick={() => {
                        setSelectedBank(bankName);
                        setSelectedBankCik(cik);
                        setChatHistory([]);
                        setFullReport('');
                        setReports({ '10-K': [], '10-Q': [] });
                        setError('');
                      }}
                      sx={{ textTransform: 'none', fontSize: '0.8rem' }}
                    >
                      🏦 {bankName.replace(' INC', '').replace(' CORP', '').replace(' GROUP', '').replace(' CORPORATION', '')}
                    </Button>
                  </Grid>
                ))}
              </Grid>
            </>
          ) : (
            <>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <DescriptionIcon /> Local Upload - Your Documents
              </Typography>
              <input type="file" multiple accept=".pdf" onChange={(e) => {
                const files = Array.from(e.target.files);
                setUploadedFiles(files);
                setAnalyzedDocs([]);
              }} style={{display: 'none'}} id="file-upload" />
              <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mb: 2 }}>
                <label htmlFor="file-upload">
                  <Button variant="outlined" component="span">Choose PDF Files</Button>
                </label>
                {uploadedFiles.length > 0 && (
                  <Button 
                    variant="contained" 
                    onClick={async () => {
                      const formData = new FormData();
                      uploadedFiles.forEach(file => formData.append('files', file));
                      
                      try {
                        setLoading(true);
                        const response = await fetch('/api/analyze-pdfs', {
                          method: 'POST',
                          body: formData
                        });
                        const result = await response.json();
                        setAnalyzedDocs(result.documents);
                      } catch (err) {
                        setError('PDF analysis failed');
                      } finally {
                        setLoading(false);
                      }
                    }}
                    disabled={loading}
                  >
                    {loading ? <CircularProgress size={20} sx={{ mr: 1 }} /> : '📤'} Upload
                  </Button>
                )}
              </Box>
              
              {analyzedDocs.length > 0 && (
                <Alert severity="success" sx={{ mb: 2 }}>
                  ✅ Successfully uploaded {analyzedDocs.map(doc => `${doc.bank_name} ${doc.form_type}`).join(', ')} document{analyzedDocs.length > 1 ? 's' : ''}
                </Alert>
              )}
              
              {uploadedFiles.length > 0 && analyzedDocs.length === 0 && (
                <List>
                  {uploadedFiles.map((file, i) => (
                    <ListItem key={i}>
                      <ListItemText primary={file.name} secondary={`${(file.size/1024/1024).toFixed(2)} MB`} />
                      <Button onClick={() => {
                        setUploadedFiles(prev => prev.filter((_, idx) => idx !== i));
                        setAnalyzedDocs(prev => prev.filter((_, idx) => idx !== i));
                      }}>Remove</Button>
                    </ListItem>
                  ))}
                </List>
              )}
            </>
          )}
        </Grid>
      </Grid>

      {(selectedBank || (mode === 'local' && uploadedFiles.length > 0)) && (
        <Grid container spacing={4}>
          {/* Available Reports */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                  <DescriptionIcon sx={{ mr: 1 }} />
                  {mode === 'local' ? 'Uploaded Documents' : 'Available SEC Filings'}
                </Typography>
                {loading ? (
                  <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                    <CircularProgress />
                  </Box>
                ) : mode === 'local' ? (
                  <List>
                    {analyzedDocs.map((doc, index) => (
                      <ListItem key={index} sx={{ border: '1px solid #e0e0e0', borderRadius: 1, mb: 1 }}>
                        <ListItemText
                          primary={
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Chip 
                                label={doc.form_type} 
                                size="small" 
                                color={doc.form_type === '10-K' ? 'primary' : 'secondary'}
                              />
                              <Typography variant="body1" sx={{ fontWeight: 500 }}>
                                {doc.bank_name} - {doc.form_type} {doc.year}
                              </Typography>
                            </Box>
                          }
                          secondary={`File: ${doc.filename} (${(doc.size/1024/1024).toFixed(2)} MB)`}
                        />
                      </ListItem>
                    ))}
                  </List>
                ) : (
                  <List>
                    {[...reports['10-K'], ...reports['10-Q']].map((report, index) => (
                      <ListItem key={index} sx={{ border: '1px solid #e0e0e0', borderRadius: 1, mb: 1 }}>
                        <ListItemText
                          primary={
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Chip 
                                label={report.form || report.type} 
                                size="small" 
                                color={report.form === '10-K' ? 'primary' : 'secondary'}
                              />
                              <Typography variant="body1" sx={{ fontWeight: 500 }}>
                                {report.accession || report.title}
                              </Typography>
                            </Box>
                          }
                          secondary={`Filed: ${report.filing_date || report.date}`}
                        />
                      </ListItem>
                    ))}
                  </List>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* Chat Interface */}
          <Grid item xs={12} md={6}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                  <ChatIcon sx={{ mr: 1 }} />
                  AI Chat Interface
                </Typography>
                
                {/* Chat History */}
                <Paper 
                  elevation={0} 
                  sx={{ 
                    height: 400, 
                    p: 2, 
                    mb: 2, 
                    backgroundColor: '#f8f9fa',
                    overflowY: 'auto'
                  }}
                >
                  {chatHistory.length === 0 ? (
                    <Typography color="text.secondary" sx={{ fontStyle: 'italic' }}>
                      {mode === 'local' ? 'Ask questions about your uploaded documents...' : `Ask questions about ${selectedBank}'s financial reports...`}
                    </Typography>
                  ) : (
                    chatHistory.map((message, index) => (
                      <Box key={index} sx={{ mb: 2 }}>
                        <Typography 
                          variant="body2" 
                          sx={{ 
                            fontWeight: 600,
                            color: message.role === 'user' ? 'primary.main' : 'secondary.main'
                          }}
                        >
                          {message.role === 'user' ? 'You:' : 'AI:'}
                        </Typography>
                        <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', mb: 1 }}>
                          {message.content}
                        </Typography>
                        {message.sources && message.sources.length > 0 && (
                          <Box sx={{ mt: 1 }}>
                            <Typography variant="caption" sx={{ fontWeight: 600, color: 'text.secondary' }}>
                              Sources:
                            </Typography>
                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                              {message.sources.map((source, idx) => (
                                <Chip 
                                  key={idx}
                                  label={`${source.filing_type} ${source.year}`}
                                  size="small"
                                  variant="outlined"
                                  sx={{ fontSize: '0.7rem' }}
                                />
                              ))}
                            </Box>
                          </Box>
                        )}
                      </Box>
                    ))
                  )}
                  
                  {chatLoading && (
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="body2" sx={{ fontWeight: 600, color: 'secondary.main' }}>AI:</Typography>
                      <Typography>Analyzing financial reports...</Typography>
                    </Box>
                  )}
                </Paper>

                {/* Chat Input */}
                {/* Sample Questions */}
                <Typography variant="body2" sx={{ mb: 1, fontWeight: 600 }}>Sample Questions:</Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                  {[
                    'What are the key risk factors?',
                    'How is the financial performance?', 
                    'What are the main revenue sources?',
                    'Any regulatory concerns?'
                  ].map((question) => (
                    <Button 
                      key={question}
                      variant="outlined"
                      size="small"
                      onClick={() => handleSendMessage(question)}
                      disabled={chatLoading}
                    >
                      {question}
                    </Button>
                  ))}
                </Box>
                
                <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                  <TextField
                    fullWidth
                    placeholder="Ask about risk factors, financial performance, etc."
                    value={chatMessage}
                    onChange={(e) => setChatMessage(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                    size="small"
                  />
                  <Button 
                    variant="contained" 
                    onClick={() => handleSendMessage()}
                    disabled={!chatMessage.trim() || chatLoading || (mode === 'local' && uploadedFiles.length === 0)}
                  >
                    {chatLoading ? 'Analyzing...' : 'Send'}
                  </Button>
                </Box>
                
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Button 
                    variant="contained" 
                    fullWidth
                    onClick={generateFullReport}
                    disabled={loading || reportLoading}
                    sx={{ backgroundColor: '#A020F0', '&:hover': { backgroundColor: '#8B1A9B' } }}
                  >
                    {reportLoading ? <CircularProgress size={20} sx={{ mr: 1 }} /> : '🚀'} Generate Full Analysis
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Full Report Display */}
      {fullReport && (
        <Card sx={{ mt: 4 }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                📊 Full Financial Analysis Report{mode === 'local' ? ' - Uploaded Documents' : ` - ${selectedBank}`}
              </Typography>
              <Button 
                variant="outlined" 
                onClick={downloadReport}
                startIcon={<DownloadIcon />}
              >
                Download Report
              </Button>
            </Box>
            <Paper 
              elevation={0} 
              sx={{ 
                p: 3, 
                backgroundColor: '#f8f9fa',
                maxHeight: 600,
                overflowY: 'auto',
                border: '1px solid #e0e0e0'
              }}
            >
              <Typography 
                variant="body1" 
                sx={{ 
                  whiteSpace: 'pre-wrap',
                  fontFamily: 'monospace',
                  fontSize: '0.9rem',
                  lineHeight: 1.6
                }}
              >
                {fullReport}
              </Typography>
            </Paper>
          </CardContent>
        </Card>
      )}


      
      {!selectedBank && mode === 'live' && (
        <Paper sx={{ p: 4, textAlign: 'center', backgroundColor: '#f8f9fa' }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            ☁️ Live EDGAR Mode - Banking Companies Only
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Select any of the 29 major banks above for real-time SEC filing analysis. Platform is designed for banking and financial institutions only.
          </Typography>
        </Paper>
      )}
      
      {mode === 'local' && uploadedFiles.length === 0 && (
        <Paper sx={{ p: 4, textAlign: 'center', backgroundColor: '#f8f9fa' }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            📄 Local Upload Mode - Your Documents
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Upload your own 10-K/10-Q PDF files for private analysis. Files are processed securely.
          </Typography>
        </Paper>
      )}
    </Box>
  );
}

export default FinancialReports;