import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, Card, CardContent, Grid, 
  FormControl, InputLabel, Select, MenuItem, Button,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper,
  CircularProgress, Alert, Divider
} from '@mui/material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { api } from '../services/api';
import ReactMarkdown from 'react-markdown';

function PeerAnalytics() {
  const [selectedBank, setSelectedBank] = useState('');
  const [selectedPeers, setSelectedPeers] = useState([]);
  const [selectedMetric, setSelectedMetric] = useState('');
  const [loading, setLoading] = useState(false);
  const [fdicData, setFdicData] = useState(null);
  const [chartData, setChartData] = useState([]);
  const [analysis, setAnalysis] = useState('');
  const [error, setError] = useState('');
  const [dataMode, setDataMode] = useState('live'); // 'live' or 'local'
  const [uploadedData, setUploadedData] = useState(null);
  const [uploadedBanks, setUploadedBanks] = useState([]);
  const [uploadedMetrics, setUploadedMetrics] = useState([]);
  const [hasQuarterly, setHasQuarterly] = useState(false);
  const [hasMonthly, setHasMonthly] = useState(false);

  const banks = [
    'JPMorgan Chase', 'Bank of America', 'Wells Fargo', 'Citigroup', 
    'U.S. Bancorp', 'PNC Financial', 'Goldman Sachs', 'Truist Financial',
    'Capital One', 'Regions Financial', 'Fifth Third Bancorp'
  ];

  const quarterlyMetrics = [
    '[Q] Return on Assets (ROA)', '[Q] Return on Equity (ROE)', '[Q] Net Interest Margin (NIM)',
    '[Q] Tier 1 Capital Ratio', '[Q] Loan-to-Deposit Ratio (LDR)', '[Q] CRE Concentration Ratio (%)'
  ];

  const monthlyMetrics = [
    '[M] Loan Growth Rate (%)', '[M] Deposit Growth (%)', 
    '[M] Efficiency Ratio (%)', '[M] Charge-off Rate (%)'
  ];

  const [analysisType, setAnalysisType] = useState('Quarterly Metrics');
  const metrics = analysisType === 'Quarterly Metrics' ? quarterlyMetrics : monthlyMetrics;

  useEffect(() => {
    loadFDICData();
  }, []);

  const [dataSource, setDataSource] = useState('');

  const loadFDICData = async () => {
    try {
      setLoading(true);
      setError('🔄 Loading banking data... This may take 10-15 seconds for live FDIC data.');
      const response = await api.getFDICData();
      console.log('API Response:', response);
      if (response.success) {
        setFdicData(response.result);
        setDataSource(response.result.data_source || 'FDIC Call Reports');
      } else {
        throw new Error('API returned success: false');
      }
      setError(''); // Clear loading message
    } catch (err) {
      console.error('FDIC data loading failed:', err);
      setError(`❌ Failed to load banking data: ${err.message || 'Network error'}`);
      setDataSource('Error');
    } finally {
      setLoading(false);
    }
  };

  const handleAnalysis = async () => {
    if (!selectedBank || selectedPeers.length === 0 || !selectedMetric) return;
    
    try {
      setLoading(true);
      setError('');
      
      // Map React bank names to API bank names
      const bankNameMap = {
        'JPMorgan Chase': 'JPMORGAN CHASE BANK',
        'Bank of America': 'BANK OF AMERICA', 
        'Wells Fargo': 'WELLS FARGO BANK',
        'Citigroup': 'CITIBANK',
        'U.S. Bancorp': 'U.S. BANK',
        'PNC Financial': 'PNC BANK',
        'Goldman Sachs': 'GOLDMAN SACHS BANK',
        'Truist Financial': 'TRUIST BANK',
        'Capital One': 'CAPITAL ONE',
        'Regions Financial': 'REGIONS FINANCIAL CORP',
        'Fifth Third Bancorp': 'FIFTH THIRD BANCORP'
      };
      
      // Reverse mapping for chart display
      const reverseMap = {
        'JPMORGAN CHASE BANK': 'JPMorgan',
        'BANK OF AMERICA': 'BofA',
        'WELLS FARGO BANK': 'Wells',
        'CITIBANK': 'Citi',
        'U.S. BANK': 'USB',
        'PNC BANK': 'PNC',
        'GOLDMAN SACHS BANK': 'Goldman',
        'TRUIST BANK': 'Truist',
        'CAPITAL ONE': 'CapOne',
        'REGIONS FINANCIAL CORP': 'Regions',
        'FIFTH THIRD BANCORP': 'Fifth'
      };
      
      const apiBaseBank = bankNameMap[selectedBank] || selectedBank;
      const apiPeerBanks = selectedPeers.map(bank => bankNameMap[bank] || bank);
      
      let result;
      if (dataMode === 'local' && uploadedData) {
        // Convert wide format to long format for analysis
        const longFormatData = [];
        const metricName = selectedMetric.replace('[Q] ', '').replace('[M] ', '');
        
        uploadedData.forEach(row => {
          if ([apiBaseBank, ...apiPeerBanks].includes(row.Bank) && row.Metric === metricName) {
            Object.keys(row).forEach(key => {
              if (key !== 'Bank' && key !== 'Metric' && row[key]) {
                longFormatData.push({
                  Bank: row.Bank,
                  Quarter: key,
                  Metric: metricName,
                  Value: parseFloat(row[key]) || 0
                });
              }
            });
          }
        });
        
        // Generate AI analysis for local data
        try {
          const analysisResponse = await fetch('/api/analyze-local-data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              data: longFormatData,
              baseBank: apiBaseBank,
              peerBanks: apiPeerBanks,
              metric: selectedMetric
            })
          });
          const analysisResult = await analysisResponse.json();
          result = { data: longFormatData, analysis: analysisResult.analysis };
        } catch (err) {
          result = { data: longFormatData, analysis: `Analysis based on uploaded data for ${selectedMetric}` };
        }
      } else {
        const response = await api.analyzePeers(apiBaseBank, apiPeerBanks, selectedMetric);
        result = response.success ? response.result : response;
      }
      setAnalysis(result.analysis);
      
      console.log('API Response:', result);
      console.log('Selected banks:', [selectedBank, ...selectedPeers]);
      if (result.data && result.data.length > 0) {
        console.log('Raw data from API:', result.data);
        const processedData = processChartData(result.data);
        console.log('Processed chart data:', processedData);
        setChartData(processedData);
      } else {
        console.log('No data in API response');
        setChartData([]);
      }
    } catch (err) {
      console.error('Analysis error:', err);
      setError(`❌ Analysis failed: ${err.message || 'Unknown error'}`);
      setAnalysis('');
      setChartData([]);
    } finally {
      setLoading(false);
    }
  };

  const processChartData = (data) => {
    if (!data || data.length === 0) return [];
    
    const reverseMap = {
      'JPMORGAN CHASE BANK': 'JPMorgan',
      'BANK OF AMERICA': 'BofA',
      'WELLS FARGO BANK': 'Wells',
      'CITIBANK': 'Citi',
      'U.S. BANK': 'USB',
      'PNC BANK': 'PNC',
      'GOLDMAN SACHS BANK': 'Goldman',
      'TRUIST BANK': 'Truist',
      'CAPITAL ONE': 'CapOne',
      'REGIONS FINANCIAL CORP': 'Regions',
      'FIFTH THIRD BANCORP': 'Fifth'
    };
    
    const quarters = [...new Set(data.map(d => d.Quarter))].sort();
    return quarters.map(quarter => {
      const quarterData = { quarter };
      data.filter(d => d.Quarter === quarter).forEach(d => {
        const bankName = reverseMap[d.Bank] || d.Bank.replace(' BANK', '').replace(' CORP', '').split(' ')[0];
        quarterData[bankName] = d.Value;
      });
      return quarterData;
    });
  };

  const availableBanks = dataMode === 'local' && uploadedBanks.length > 0 ? uploadedBanks : banks;
  const availablePeers = availableBanks.filter(bank => bank !== selectedBank);
  const availableMetrics = dataMode === 'local' && uploadedMetrics.length > 0 ? 
    (analysisType === 'Quarterly Metrics' ? uploadedMetrics.map(m => `[Q] ${m}`) : uploadedMetrics.map(m => `[M] ${m}`)) : 
    metrics;

  // Sample data for 2023-2025 period
  const sampleData = [
    { quarter: '2023-Q1', JPMorgan: 1.25, BofA: 1.18, Wells: 1.12, Citi: 1.08 },
    { quarter: '2023-Q2', JPMorgan: 1.28, BofA: 1.22, Wells: 1.15, Citi: 1.12 },
    { quarter: '2023-Q3', JPMorgan: 1.32, BofA: 1.25, Wells: 1.18, Citi: 1.15 },
    { quarter: '2023-Q4', JPMorgan: 1.35, BofA: 1.28, Wells: 1.21, Citi: 1.18 },
    { quarter: '2024-Q1', JPMorgan: 1.38, BofA: 1.31, Wells: 1.24, Citi: 1.21 },
    { quarter: '2024-Q2', JPMorgan: 1.41, BofA: 1.34, Wells: 1.27, Citi: 1.24 },
    { quarter: '2024-Q3', JPMorgan: 1.44, BofA: 1.37, Wells: 1.30, Citi: 1.27 },
    { quarter: '2024-Q4', JPMorgan: 1.47, BofA: 1.40, Wells: 1.33, Citi: 1.30 },
    { quarter: '2025-Q1', JPMorgan: 1.50, BofA: 1.43, Wells: 1.36, Citi: 1.33 },
    { quarter: '2025-Q2', JPMorgan: 1.53, BofA: 1.46, Wells: 1.39, Citi: 1.36 }
  ];

  const tableData = [
    { bank: 'JPMorgan Chase', roa: 1.38, roe: 15.2, nim: 2.8, tier1: 12.5 },
    { bank: 'Bank of America', roa: 1.31, roe: 14.8, nim: 2.6, tier1: 11.8 },
    { bank: 'Wells Fargo', roa: 1.24, roe: 13.9, nim: 2.9, tier1: 12.1 },
    { bank: 'Citigroup', roa: 1.21, roe: 13.2, nim: 2.7, tier1: 11.9 }
  ];

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 600 }}>
            Peer Bank Analytics
          </Typography>
          {dataSource && (
            <Typography variant="caption" sx={{ color: 'text.secondary', mt: 0.5, display: 'block' }}>
              Data Source: {dataSource.includes('FDIC Call Reports') ? '🟢 FDIC Call Reports (2023-2025)' : '🟡 Mock Data'}
            </Typography>
          )}
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, p: 1, border: '1px solid #ddd', borderRadius: 2, backgroundColor: '#f5f5f5' }}>
          <Button 
            variant={dataMode === 'live' ? 'contained' : 'text'} 
            size="small"
            onClick={() => {
              setDataMode('live');
              setSelectedBank('');
              setSelectedPeers([]);
              setSelectedMetric('');
              setAnalysis('');
              setChartData([]);
              setUploadedData(null);
              setUploadedBanks([]);
              setUploadedMetrics([]);
              setError('');
            }}
            sx={{ minWidth: 80, fontSize: '0.8rem' }}
          >
            Live Data
          </Button>
          <Button 
            variant={dataMode === 'local' ? 'contained' : 'text'} 
            size="small"
            onClick={() => {
              setDataMode('local');
              setSelectedBank('');
              setSelectedPeers([]);
              setSelectedMetric('');
              setAnalysis('');
              setChartData([]);
              setError('');
            }}
            sx={{ minWidth: 80, fontSize: '0.8rem' }}
          >
            Upload CSV
          </Button>
        </Box>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      
      {/* Local Upload Section */}
      {dataMode === 'local' && (
        <Card sx={{ mb: 4, backgroundColor: '#f8f9fa' }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>📊 Upload Your Metrics Data</Typography>
            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mb: 2 }}>
              <Button 
                variant="outlined" 
                onClick={() => {
                  const link = document.createElement('a');
                  link.href = '/quarterly_template.csv';
                  link.download = 'quarterly_template.csv';
                  link.click();
                }}
              >
                📥 Quarterly Template
              </Button>
              <Button 
                variant="outlined" 
                onClick={() => {
                  const link = document.createElement('a');
                  link.href = '/monthly_template.csv';
                  link.download = 'monthly_template.csv';
                  link.click();
                }}
              >
                📥 Monthly Template
              </Button>
              <input 
                type="file" 
                accept=".csv" 
                onChange={(e) => {
                  const file = e.target.files[0];
                  if (file) {
                    const reader = new FileReader();
                    reader.onload = (event) => {
                      const csv = event.target.result;
                      const lines = csv.split('\n');
                      const headers = lines[0].split(',');
                      const data = lines.slice(1).filter(line => line.trim()).map(line => {
                        const values = line.split(',');
                        const obj = {};
                        headers.forEach((header, i) => {
                          obj[header.trim()] = values[i]?.trim();
                        });
                        return obj;
                      });
                      setUploadedData(data);
                      
                      // Store CSV data in backend
                      fetch('/api/store-csv-data', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ data: data, filename: file.name })
                      }).catch(err => console.log('CSV storage failed:', err));
                      
                      // Auto-populate fields from uploaded data
                      if (data.length > 0) {
                        // Get unique banks
                        const uniqueBanks = [...new Set(data.map(row => row.Bank))];
                        setUploadedBanks(uniqueBanks);
                        
                        // Detect quarterly vs monthly data from column headers
                        const columns = Object.keys(data[0]);
                        const quarterly = columns.some(col => col && col.includes('Q'));
                        const monthly = columns.some(col => col && (col.includes('Jan') || col.includes('Feb') || col.includes('Mar')));
                        setHasQuarterly(quarterly);
                        setHasMonthly(monthly);
                        
                        // Set analysis type
                        if (quarterly && !monthly) {
                          setAnalysisType('Quarterly Metrics');
                        } else if (monthly && !quarterly) {
                          setAnalysisType('Monthly View');
                        } else {
                          setAnalysisType('Quarterly Metrics'); // Default
                        }
                        
                        // Get available metrics
                        const availableMetrics = [...new Set(data.map(row => row.Metric))];
                        setUploadedMetrics(availableMetrics);
                        if (availableMetrics.length > 0) {
                          const prefix = quarterly ? '[Q] ' : '[M] ';
                          setSelectedMetric(prefix + availableMetrics[0]);
                        }
                      }
                    };
                    reader.readAsText(file);
                  }
                }}
                style={{ display: 'none' }}
                id="csv-upload"
              />
              <label htmlFor="csv-upload">
                <Button variant="contained" component="span">
                  📁 Choose CSV File
                </Button>
              </label>
              {uploadedData && (
                <Typography variant="body2" color="success.main">
                  ✅ {uploadedData.length} records loaded
                </Typography>
              )}
            </Box>
            <Typography variant="body2" color="text.secondary">
              Download templates above: Quarterly (Q1-Q4 columns) or Monthly (Jan-Dec columns). Fill with your data and upload.
            </Typography>
          </CardContent>
        </Card>
      )}
      
      {/* Controls */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={3}>
          <FormControl fullWidth>
            <InputLabel>Base Bank</InputLabel>
            <Select
              value={selectedBank}
              label="Base Bank"
              onChange={(e) => setSelectedBank(e.target.value)}
            >
              {availableBanks.map((bank) => (
                <MenuItem key={bank} value={bank}>{bank}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={12} md={3}>
          <FormControl fullWidth>
            <InputLabel>Peer Banks (Max 3)</InputLabel>
            <Select
              multiple
              value={selectedPeers}
              label="Peer Banks (Max 3)"
              onChange={(e) => setSelectedPeers(e.target.value.slice(0, 3))}
            >
              {availablePeers.map((bank) => (
                <MenuItem key={bank} value={bank}>{bank}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
            Select up to 3 banks for comparison
          </Typography>
        </Grid>
        <Grid item xs={12} md={2}>
          <FormControl fullWidth>
            <InputLabel>Analysis Type</InputLabel>
            <Select
              value={analysisType}
              label="Analysis Type"
              onChange={(e) => {
                setAnalysisType(e.target.value);
                setSelectedMetric(''); // Reset metric when type changes
              }}
            >
              <MenuItem value="Quarterly Metrics">Quarterly</MenuItem>
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={12} md={2}>
          <FormControl fullWidth>
            <InputLabel>Metric</InputLabel>
            <Select
              value={selectedMetric}
              label="Metric"
              onChange={(e) => {
                setSelectedMetric(e.target.value);
                setAnalysis('');
                setChartData([]);
                setError('');
              }}
            >
              {availableMetrics.map((metric) => (
                <MenuItem key={metric} value={metric}>{metric.replace('[Q] ', '').replace('[M] ', '')}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={12} md={1}>
          <Button 
            variant="contained" 
            fullWidth 
            sx={{ height: 56 }}
            disabled={!selectedBank || selectedPeers.length === 0 || !selectedMetric || loading}
            onClick={handleAnalysis}
          >
            {loading ? <CircularProgress size={24} /> : 'Analyze'}
          </Button>
        </Grid>
        <Grid item xs={12} md={1}>
          <Button 
            variant="outlined" 
            fullWidth 
            sx={{ height: 56 }}
            onClick={() => {
              setSelectedBank('');
              setSelectedPeers([]);
              setSelectedMetric('');
              setAnalysis('');
              setChartData([]);
              setError('');
              setUploadedData(null);
              setUploadedBanks([]);
              setUploadedMetrics([]);
            }}
          >
            Reset
          </Button>
        </Grid>
      </Grid>

      {/* AI Analysis */}
      {analysis && (
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              🤖 AI Analysis - {selectedMetric.replace('[Q] ', '').replace('[M] ', '')}
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <Box sx={{ 
              '& h1, & h2, & h3': { mt: 2, mb: 1, fontWeight: 600 },
              '& h2': { fontSize: '1.5rem', color: '#A020F0' },
              '& h3': { fontSize: '1.25rem', color: '#8B1A9B' },
              '& p': { mb: 1.5, lineHeight: 1.7 },
              '& ul, & ol': { pl: 3, mb: 1.5 },
              '& li': { mb: 0.5 },
              '& table': { width: '100%', borderCollapse: 'collapse', mb: 2 },
              '& th, & td': { border: '1px solid #ddd', padding: '8px 12px', textAlign: 'left' },
              '& th': { backgroundColor: '#f5f5f5', fontWeight: 600 },
              '& strong': { fontWeight: 600, color: '#A020F0' },
              '& code': { backgroundColor: '#f5f5f5', padding: '2px 6px', borderRadius: '4px', fontSize: '0.9em' }
            }}>
              <ReactMarkdown>{analysis}</ReactMarkdown>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Chart */}
      {analysis && (
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              {selectedMetric.replace('[Q] ', '').replace('[M] ', '')} Trends
            </Typography>
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={500}>
                <LineChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis 
                    dataKey="quarter" 
                    tick={{ fontSize: 12 }}
                    axisLine={{ stroke: '#ccc' }}
                  />
                  <YAxis 
                    tick={{ fontSize: 12 }}
                    axisLine={{ stroke: '#ccc' }}
                    domain={['dataMin - 0.5', 'dataMax + 0.5']}
                  />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#fff', 
                      border: '1px solid #ccc',
                      borderRadius: '8px',
                      boxShadow: '0 4px 8px rgba(0,0,0,0.1)'
                    }}
                  />
                  <Legend wrapperStyle={{ paddingTop: '20px' }} />
                  {Object.keys(chartData[0] || {}).filter(key => key !== 'quarter').map((dataKey, index) => (
                    <Line 
                      key={dataKey}
                      type="monotone" 
                      dataKey={dataKey}
                      name={dataKey}
                      stroke={['#A020F0', '#FF6B35', '#00B4D8', '#90E0EF'][index % 4]} 
                      strokeWidth={4}
                      strokeDasharray={index === 0 ? '0' : index === 1 ? '5,5' : index === 2 ? '10,5' : '15,5,5,5'}
                      dot={{ fill: ['#A020F0', '#FF6B35', '#00B4D8', '#90E0EF'][index % 4], strokeWidth: 2, r: 6 }}
                      activeDot={{ r: 8, stroke: ['#A020F0', '#FF6B35', '#00B4D8', '#90E0EF'][index % 4], strokeWidth: 2 }}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <Typography>Chart data processing...</Typography>
            )}
          </CardContent>
        </Card>
      )}

      {/* Raw Data Table - Show after analysis */}
      {analysis && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Input Data - {selectedMetric.replace('[Q] ', '').replace('[M] ', '')}
            </Typography>
            <TableContainer component={Paper} elevation={0}>
              <Table size="small">
                <TableHead>
                  <TableRow sx={{ backgroundColor: '#A020F0' }}>
                    <TableCell sx={{ color: 'white', fontWeight: 600 }}>Bank</TableCell>
                    <TableCell sx={{ color: 'white', fontWeight: 600 }}>Quarter</TableCell>
                    <TableCell sx={{ color: 'white', fontWeight: 600 }}>Metric</TableCell>
                    <TableCell sx={{ color: 'white', fontWeight: 600 }}>Value</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {chartData.length > 0 ? (
                    chartData.map((quarter, qIndex) => 
                      Object.keys(quarter).filter(key => key !== 'quarter').map((bank, bIndex) => (
                        <TableRow key={`${qIndex}-${bIndex}`} sx={{ backgroundColor: bIndex % 2 === 0 ? '#f8f9fa' : 'white' }}>
                          <TableCell sx={{ fontWeight: 600 }}>{bank}</TableCell>
                          <TableCell>{quarter.quarter}</TableCell>
                          <TableCell>{selectedMetric.replace('[Q] ', '').replace('[M] ', '')}</TableCell>
                          <TableCell>{quarter[bank]}%</TableCell>
                        </TableRow>
                      ))
                    ).flat()
                  ) : (
                    <TableRow><TableCell colSpan={4}>Run analysis to see data</TableCell></TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}
    </Box>
  );
}

export default PeerAnalytics;