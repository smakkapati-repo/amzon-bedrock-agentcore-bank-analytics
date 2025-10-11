from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import pandas as pd
import boto3
import json
from rag_system import rag_system
from sec_edgar_live import sec_api
from bank_search import bank_search
from fdic_api import get_real_fdic_data
import PyPDF2
import io
from datetime import datetime, timedelta

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

# S3 client for PDF storage
s3_client = boto3.client('s3')
S3_BUCKET = 'bankiq-uploaded-docs'  # Will be created if doesn't exist

# Cache for FDIC data
fdic_cache = {'data': None, 'timestamp': None, 'ttl_minutes': 30}

# Initialize RAG system on startup
with app.app_context():
    print("Initializing RAG system...")
    try:
        rag_system.initialize()
        print("RAG system initialized successfully")
    except Exception as e:
        print(f"RAG initialization failed: {e}")

def get_banking_data():
    """Get banking data from FDIC API with fallback to mock data"""
    # Check cache first
    if (fdic_cache['data'] is not None and 
        fdic_cache['timestamp'] is not None and 
        datetime.now() - fdic_cache['timestamp'] < timedelta(minutes=fdic_cache['ttl_minutes'])):
        print("Using cached FDIC data")
        return fdic_cache['data']
    
    try:
        print("Fetching fresh FDIC data...")
        data = get_real_fdic_data()
        # Cache the data
        fdic_cache['data'] = data
        fdic_cache['timestamp'] = datetime.now()
        return data
    except Exception as e:
        print(f"FDIC API failed, using mock data: {e}")
        return get_mock_banking_data()

def get_mock_banking_data():
    """Fallback mock banking data"""
    banks = [
        "JPMORGAN CHASE BANK", "BANK OF AMERICA", "WELLS FARGO BANK", 
        "CITIBANK", "U.S. BANK", "PNC BANK", "GOLDMAN SACHS BANK",
        "TRUIST BANK", "CAPITAL ONE", "FIFTH THIRD BANCORP", "REGIONS FINANCIAL CORP"
    ]
    
    quarters = ["2023-Q1", "2023-Q2", "2023-Q3", "2023-Q4", "2024-Q1"]
    metrics = [
        "Return on Assets (ROA)", "Return on Equity (ROE)", 
        "Net Interest Margin (NIM)", "Tier 1 Capital Ratio",
        "Loan-to-Deposit Ratio (LDR)", "CRE Concentration Ratio (%)"
    ]
    
    data = []
    for i, bank in enumerate(banks):
        for quarter in quarters:
            for metric in metrics:
                base_values = {
                    "Return on Assets (ROA)": 1.2,
                    "Return on Equity (ROE)": 15.0,
                    "Net Interest Margin (NIM)": 3.2,
                    "Tier 1 Capital Ratio": 12.5,
                    "Loan-to-Deposit Ratio (LDR)": 75.0,
                    "CRE Concentration Ratio (%)": 25.0
                }
                
                base_value = base_values[metric]
                bank_offset = i * 0.3
                quarter_trend = quarters.index(quarter) * 0.1
                variation = (hash(bank + quarter + metric) % 200) / 100
                value = round(base_value + bank_offset + quarter_trend + variation, 2)
                
                data.append({
                    "Bank": bank,
                    "Quarter": quarter,
                    "Year": quarter[:4],
                    "Metric": metric,
                    "Value": value,
                    "Bank Type": "Base Bank" if "JPMORGAN" in bank else "Peer Bank"
                })
    
    return pd.DataFrame(data)

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/<path:path>')
def serve_static(path):
    try:
        return app.send_static_file(path)
    except:
        # For React Router - serve index.html for any unknown routes
        return app.send_static_file('index.html')

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'service': 'BankIQ+'})

@app.route('/api/fdic-data')
def get_fdic_data():
    try:
        # Try real FDIC API first
        data_source = "FDIC API"
        try:
            data = get_real_fdic_data()
        except Exception as e:
            print(f"FDIC API failed, using mock data: {e}")
            data = get_mock_banking_data()
            data_source = "Mock Data"
        
        metrics_data = pd.DataFrame([
            {"Metric Name": "[Q] Return on Assets (ROA)", "Metric Description": "Net income as percentage of average assets"},
            {"Metric Name": "[Q] Return on Equity (ROE)", "Metric Description": "Net income as percentage of average equity"},
            {"Metric Name": "[Q] Net Interest Margin (NIM)", "Metric Description": "Difference between interest earned and paid as % of assets"},
            {"Metric Name": "[Q] Tier 1 Capital Ratio", "Metric Description": "Core capital as percentage of risk-weighted assets"},
            {"Metric Name": "[Q] Loan-to-Deposit Ratio (LDR)", "Metric Description": "Total loans as percentage of total deposits"},
            {"Metric Name": "[Q] CRE Concentration Ratio (%)", "Metric Description": "Commercial real estate loans as percentage of total capital"}
        ])
        
        return jsonify({
            'data': data.to_dict('records'),
            'metrics': metrics_data.to_dict('records'),
            'data_source': data_source,
            'total_records': len(data)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analyze-peers', methods=['POST'])
def analyze_peers():
    try:
        data = request.json
        base_bank = data['baseBank']
        peer_banks = data['peerBanks']
        metric = data['metric']
        
        all_banks = [base_bank] + peer_banks
        clean_metric = metric.replace('[Q] ', '').replace('[M] ', '')
        
        if metric.startswith('[M]'):
            # Monthly data
            months = ['2023-01', '2023-02', '2023-03', '2023-04', '2023-05', '2023-06',
                     '2023-07', '2023-08', '2023-09', '2023-10', '2023-11', '2023-12',
                     '2024-01', '2024-02', '2024-03', '2024-04', '2024-05', '2024-06']
            
            monthly_data = []
            for bank in all_banks:
                for month in months:
                    base_values = {
                        'Loan Growth Rate': 2.5,
                        'Deposit Growth': 1.8,
                        'Efficiency Ratio': 62.0,
                        'Charge-off Rate': 0.8
                    }
                    
                    base_value = base_values.get(clean_metric, 2.0)
                    variation = (hash(bank + month + clean_metric) % 100) / 100
                    value = round(base_value + variation, 2)
                    
                    monthly_data.append({
                        'Bank': bank,
                        'Quarter': month,
                        'Metric': clean_metric,
                        'Value': value
                    })
            
            filtered_data = pd.DataFrame(monthly_data)
        else:
            # Quarterly data
            banking_data = get_banking_data()
            filtered_data = banking_data[banking_data['Bank'].isin(all_banks)]
            filtered_data = filtered_data[filtered_data['Metric'] == clean_metric]
        
        # AI Analysis
        try:
            bedrock = boto3.client('bedrock-runtime')
            
            data_summary = "\n".join([
                f"Bank: {row['Bank']}, Quarter: {row['Quarter']}, {metric}: {row['Value']:.2f}%"
                for _, row in filtered_data.iterrows()
            ])
            
            prompt = f"""
Analyze {base_bank} vs {', '.join(peer_banks)} for {metric}.

Data:
{data_summary}

Provide analysis with:
• Performance comparison
• Trends over time
• Key insights
• Recommendations
"""
            
            response = bedrock.converse(
                modelId="anthropic.claude-3-haiku-20240307-v1:0",
                messages=[{"role": "user", "content": [{"text": prompt}]}],
                inferenceConfig={"maxTokens": 1000}
            )
            
            analysis = response['output']['message']['content'][0]['text']
            
        except Exception as e:
            analysis = f"Analysis for {metric}: {base_bank} performance vs peers - {str(e)}"
        
        return jsonify({
            'analysis': analysis,
            'data': filtered_data.to_dict('records')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sec-reports/<bank_name>')
def get_sec_reports(bank_name):
    use_live = request.args.get('live', 'false').lower() == 'true'
    custom_cik = request.args.get('cik')
    
    if use_live:
        print(f"LIVE MODE: Fetching real SEC filings for {bank_name}")
        if custom_cik:
            print(f"Using custom CIK: {custom_cik}")
        live_filings = sec_api.get_recent_filings(bank_name, limit=10, custom_cik=custom_cik)
        
        reports = {'10-K': [], '10-Q': []}
        for filing in live_filings:
            reports[filing['form']].append({
                'form': filing['form'],
                'filing_date': filing['filing_date'],
                'accession': f"LIVE: {filing['accession']}"
            })
        
        print(f"LIVE MODE: Found {len(live_filings)} real filings")
        return jsonify(reports)
    else:
        # Mock data for RAG mode
        reports = {
            '10-K': [
                {'form': '10-K', 'filing_date': '2025-02-28', 'accession': 'RAG: Annual Report 2024'},
                {'form': '10-K', 'filing_date': '2024-02-28', 'accession': 'RAG: Annual Report 2023'}
            ],
            '10-Q': [
                {'form': '10-Q', 'filing_date': '2025-07-15', 'accession': 'RAG: Q2 2025 Report'},
                {'form': '10-Q', 'filing_date': '2025-04-15', 'accession': 'RAG: Q1 2025 Report'},
                {'form': '10-Q', 'filing_date': '2025-01-15', 'accession': 'RAG: Q4 2024 Report'},
                {'form': '10-Q', 'filing_date': '2024-10-15', 'accession': 'RAG: Q3 2024 Report'},
                {'form': '10-Q', 'filing_date': '2024-07-15', 'accession': 'RAG: Q2 2024 Report'}
            ]
        }
        return jsonify(reports)

@app.route('/api/analyze-pdfs', methods=['POST'])
def analyze_pdfs():
    try:
        files = request.files.getlist('files')
        analyzed_docs = []
        
        for file in files:
            if file.filename.endswith('.pdf'):
                file_data = file.read()
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_data))
                text = ''
                # Read first page for bank name extraction
                first_page_text = pdf_reader.pages[0].extract_text().upper() if pdf_reader.pages else ''
                
                # Read ALL pages to get complete content
                for page in pdf_reader.pages:
                    text += page.extract_text() + '\n'
                
                # Extract bank name, form type, year
                bank_name = 'Unknown Bank'
                form_type = '10-K' if '10-K' in text[:2000] else '10-Q' if '10-Q' in text[:2000] else 'Unknown'
                year = '2024'
                
                # Look for bank name in first page first, then broader search
                text_upper = first_page_text + '\n' + text[:5000].upper()
                
                # Enhanced company name extraction
                import re
                
                # First try standard SEC document patterns
                sec_patterns = [
                    r'COMPANY:\s*([A-Z][A-Z\s&,\.\-]+?)(?:\s*\n|\s*FORM)',
                    r'REGISTRANT:\s*([A-Z][A-Z\s&,\.\-]+?)(?:\s*\n|\s*CIK)',
                    r'([A-Z][A-Z\s&,\.\-]+?)\s*\n\s*\(EXACT NAME OF REGISTRANT',
                    r'([A-Z][A-Z\s&,\.\-]+?)\s*\n\s*\(NAME OF REGISTRANT',
                    r'COMMISSION FILE NO[^\n]*\n\s*([A-Z][A-Z\s&,\.\-]+?)\s*\n\s*\(EXACT NAME',
                    r'FILE NO[^\n]*\n\s*([A-Z][A-Z\s&,\.\-]+?)\s*\n\s*\(EXACT NAME'
                ]
                
                # Try SEC document patterns first
                for pattern in sec_patterns:
                    matches = re.findall(pattern, text_upper[:3000])
                    if matches:
                        match = matches[0].strip().rstrip(',')
                        if len(match) > 5 and 'UNITED STATES' not in match and 'SECURITIES' not in match:
                            bank_name = match
                            break
                
                # If no SEC pattern match, try generic financial company patterns
                if bank_name == 'Unknown Bank':
                    generic_patterns = [
                        (r'([A-Z][A-Z\s&]+)\s+BANK(?:ING)?(?:\s+(?:CORP|CORPORATION|COMPANY|CO|INC|NA|N\.A\.))?', 'BANK'),
                        (r'([A-Z][A-Z\s&]+)\s+BANCORP(?:ORATION)?', 'BANCORP'),
                        (r'([A-Z][A-Z\s&]+)\s+FINANCIAL(?:\s+(?:CORP|CORPORATION|COMPANY|CO|INC|GROUP))?', 'FINANCIAL'),
                        (r'([A-Z][A-Z\s&]+)\s+BANCSHARES', 'BANCSHARES'),
                        (r'([A-Z][A-Z\s&]+)\s+BANCSYSTEM', 'BANCSYSTEM'),
                        (r'([A-Z][A-Z\s&]+)\s+TRUST(?:\s+(?:CORP|CORPORATION|COMPANY|CO))?', 'TRUST'),
                        (r'([A-Z][A-Z\s&]+)\s+INC\.?', 'INC'),
                        (r'([A-Z][A-Z\s&]+)\s+CORP(?:ORATION)?', 'CORP')
                    ]
                    
                    for pattern, suffix in generic_patterns:
                        matches = re.findall(pattern, text_upper)
                        if matches:
                            match = matches[0].strip()
                            if len(match) > 3 and 'UNITED STATES' not in match and 'FEDERAL' not in match:
                                bank_name = match + ' ' + suffix if suffix not in match else match
                                break
                
                # If still no match, try specific company patterns
                if bank_name == 'Unknown Bank':
                    # Common bank patterns
                    bank_patterns = [
                    (r'WEBSTER\s+FINANCIAL', 'WEBSTER FINANCIAL'),
                    (r'JPMORGAN\s+CHASE', 'JPMORGAN CHASE'),
                    (r'BANK\s+OF\s+AMERICA', 'BANK OF AMERICA'),
                    (r'WELLS\s+FARGO', 'WELLS FARGO'),
                    (r'CITIGROUP', 'CITIGROUP'),
                    (r'GOLDMAN\s+SACHS', 'GOLDMAN SACHS'),
                    (r'U\.?S\.?\s+BANCORP', 'U.S. BANCORP'),
                    (r'PNC\s+FINANCIAL', 'PNC FINANCIAL'),
                    (r'TRUIST\s+FINANCIAL', 'TRUIST FINANCIAL'),
                    (r'CAPITAL\s+ONE', 'CAPITAL ONE'),
                    (r'REGIONS\s+FINANCIAL', 'REGIONS FINANCIAL'),
                    (r'FIFTH\s+THIRD', 'FIFTH THIRD'),
                    (r'HUNTINGTON\s+BANCSHARES', 'HUNTINGTON BANCSHARES'),
                    (r'COMERICA', 'COMERICA'),
                    (r'ZIONS\s+BANCORPORATION', 'ZIONS BANCORPORATION'),
                    (r'FIRST\s+REPUBLIC', 'FIRST REPUBLIC'),
                    (r'SILICON\s+VALLEY\s+BANK', 'SILICON VALLEY BANK'),
                    (r'SIGNATURE\s+BANK', 'SIGNATURE BANK'),
                    (r'FIRST\s+CITIZENS', 'FIRST CITIZENS'),
                    (r'SYNOVUS', 'SYNOVUS'),
                    (r'VALLEY\s+NATIONAL', 'VALLEY NATIONAL'),
                    (r'WESTERN\s+ALLIANCE', 'WESTERN ALLIANCE'),
                    (r'PACWEST', 'PACWEST'),
                    (r'ASSOCIATED\s+BANC', 'ASSOCIATED BANC-CORP'),
                    (r'FIRST\s+HORIZON', 'FIRST HORIZON'),
                    (r'COMMERCE\s+BANCSHARES', 'COMMERCE BANCSHARES'),
                    (r'CULLEN/FROST', 'CULLEN/FROST BANKERS'),
                    (r'POPULAR', 'POPULAR INC'),
                    (r'HANCOCK\s+WHITNEY', 'HANCOCK WHITNEY'),
                    (r'FIRST\s+INTERSTATE', 'FIRST INTERSTATE'),
                    (r'BANK\s+OZK', 'BANK OZK'),
                    (r'TEXAS\s+CAPITAL', 'TEXAS CAPITAL'),
                    (r'PROSPERITY\s+BANCSHARES', 'PROSPERITY BANCSHARES'),
                    (r'EAST\s+WEST\s+BANCORP', 'EAST WEST BANCORP'),
                    (r'CATHAY\s+GENERAL', 'CATHAY GENERAL BANCORP'),
                    (r'FIRST\s+FINANCIAL', 'FIRST FINANCIAL BANCORP'),
                    (r'STERLING\s+BANCORP', 'STERLING BANCORP'),
                    (r'BROOKLINE\s+BANCORP', 'BROOKLINE BANCORP'),
                    (r'LAKELAND\s+FINANCIAL', 'LAKELAND FINANCIAL'),
                    (r'SANDY\s+SPRING', 'SANDY SPRING BANCORP'),
                    (r'UNITED\s+COMMUNITY', 'UNITED COMMUNITY BANKS'),
                    (r'ATLANTIC\s+UNION', 'ATLANTIC UNION BANKSHARES'),
                    (r'FIRST\s+MERCHANTS', 'FIRST MERCHANTS CORP'),
                    (r'GERMAN\s+AMERICAN', 'GERMAN AMERICAN BANCORP'),
                    (r'PARK\s+NATIONAL', 'PARK NATIONAL CORP'),
                    (r'SOUTHERN\s+FIRST', 'SOUTHERN FIRST BANCSHARES'),
                    (r'COMMUNITY\s+BANK\s+SYSTEM', 'COMMUNITY BANK SYSTEM'),
                    (r'FIRST\s+BUSEY', 'FIRST BUSEY CORP'),
                    (r'NORTHFIELD\s+BANCORP', 'NORTHFIELD BANCORP'),
                    (r'ENTERPRISE\s+FINANCIAL', 'ENTERPRISE FINANCIAL'),
                    (r'MERIDIAN\s+BANCORP', 'MERIDIAN BANCORP'),
                    (r'SOUTHERN\s+MISSOURI', 'SOUTHERN MISSOURI BANCORP'),
                    (r'FIRST\s+BANCORP', 'FIRST BANCORP'),
                    (r'AMERIS\s+BANCORP', 'AMERIS BANCORP'),
                    (r'RENASANT', 'RENASANT CORP'),
                    (r'SIMMONS\s+FIRST', 'SIMMONS FIRST NATIONAL'),
                    (r'ORIGIN\s+BANCORP', 'ORIGIN BANCORP'),
                    (r'SOUTHSIDE\s+BANCSHARES', 'SOUTHSIDE BANCSHARES'),
                    (r'CENTRAL\s+PACIFIC', 'CENTRAL PACIFIC FINANCIAL'),
                    (r'BANNER\s+CORP', 'BANNER CORP'),
                    (r'COLUMBIA\s+BANKING', 'COLUMBIA BANKING SYSTEM'),
                    (r'PACIFIC\s+PREMIER', 'PACIFIC PREMIER BANCORP'),
                    (r'HERITAGE\s+FINANCIAL', 'HERITAGE FINANCIAL'),
                    (r'WASHINGTON\s+FEDERAL', 'WASHINGTON FEDERAL'),
                    (r'NORTHWEST\s+BANCSHARES', 'NORTHWEST BANCSHARES'),
                    (r'FIRST\s+COMMONWEALTH', 'FIRST COMMONWEALTH FINANCIAL'),
                    (r'S&T\s+BANCORP', 'S&T BANCORP'),
                    (r'PENNS\s+WOODS', 'PENNS WOODS BANCORP'),
                    (r'CITIZENS\s+FINANCIAL', 'CITIZENS FINANCIAL GROUP'),
                    (r'EASTERN\s+BANKSHARES', 'EASTERN BANKSHARES'),
                    (r'BERKSHIRE\s+HILLS', 'BERKSHIRE HILLS BANCORP'),
                    (r'COMMUNITY\s+BANKERS', 'COMMUNITY BANKERS TRUST'),
                    (r'FIRST\s+DEFIANCE', 'FIRST DEFIANCE FINANCIAL'),
                    (r'PREMIER\s+FINANCIAL', 'PREMIER FINANCIAL BANCORP'),
                    (r'UNITED\s+BANKSHARES', 'UNITED BANKSHARES'),
                    (r'CITY\s+HOLDING', 'CITY HOLDING COMPANY'),
                    (r'WESBANCO', 'WESBANCO INC'),
                    (r'FIRST\s+UNITED', 'FIRST UNITED CORP'),
                    (r'COMMUNITY\s+FINANCIAL', 'COMMUNITY FINANCIAL CORP'),
                    (r'PINNACLE\s+FINANCIAL', 'PINNACLE FINANCIAL PARTNERS'),
                    (r'FIRST\s+TENNESSEE', 'FIRST TENNESSEE NATIONAL'),
                    (r'IBERIABANK', 'IBERIABANK CORP'),
                    (r'CAPITAL\s+CITY\s+BANK', 'CAPITAL CITY BANK GROUP'),
                    (r'SEACOAST\s+BANKING', 'SEACOAST BANKING CORP'),
                    (r'CENTERSTATE\s+BANK', 'CENTERSTATE BANK CORP'),
                    (r'FIRST\s+MIDWEST', 'FIRST MIDWEST BANCORP'),
                    (r'GREAT\s+WESTERN', 'GREAT WESTERN BANCORP'),
                    (r'GLACIER\s+BANCORP', 'GLACIER BANCORP'),
                    (r'MOUNTAIN\s+WEST', 'MOUNTAIN WEST FINANCIAL'),
                    (r'WESTERN\s+SIERRA', 'WESTERN SIERRA BANCORP'),
                    (r'CENTRAL\s+VALLEY', 'CENTRAL VALLEY COMMUNITY BANCORP'),
                    (r'SIERRA\s+BANCORP', 'SIERRA BANCORP'),
                    (r'PREFERRED\s+BANK', 'PREFERRED BANK'),
                    (r'PACIFIC\s+CITY', 'PACIFIC CITY FINANCIAL'),
                    (r'HANMI\s+FINANCIAL', 'HANMI FINANCIAL CORP'),
                    (r'NARA\s+BANCORP', 'NARA BANCORP'),
                    (r'WILSHIRE\s+BANCORP', 'WILSHIRE BANCORP'),
                    (r'ROYAL\s+BUSINESS', 'ROYAL BUSINESS BANK'),
                    (r'FIRST\s+FOUNDATION', 'FIRST FOUNDATION INC'),
                    (r'OPUS\s+BANK', 'OPUS BANK'),
                    (r'SQUARE\s+1\s+FINANCIAL', 'SQUARE 1 FINANCIAL'),
                    (r'BRIDGE\s+CAPITAL', 'BRIDGE CAPITAL HOLDINGS'),
                    (r'CALIFORNIA\s+FIRST', 'CALIFORNIA FIRST NATIONAL BANCORP'),
                    (r'TRISTATE\s+CAPITAL', 'TRISTATE CAPITAL HOLDINGS'),
                    (r'FIRST\s+NATIONAL', 'FIRST NATIONAL CORP'),
                    (r'NATIONAL\s+PENN', 'NATIONAL PENN BANCSHARES'),
                    (r'SUSQUEHANNA', 'SUSQUEHANNA BANCSHARES'),
                    (r'ORRSTOWN\s+FINANCIAL', 'ORRSTOWN FINANCIAL SERVICES'),
                    (r'FARMERS\s+NATIONAL', 'FARMERS NATIONAL BANC CORP'),
                    (r'FIRST\defiance', 'FIRST DEFIANCE FINANCIAL CORP'),
                    (r'PARK\s+STERLING', 'PARK STERLING CORP'),
                    (r'SOUTH\s+STATE', 'SOUTH STATE CORP'),
                    (r'SCBT\s+FINANCIAL', 'SCBT FINANCIAL CORP'),
                    (r'FIRST\s+FINANCIAL\s+NORTHWEST', 'FIRST FINANCIAL NORTHWEST'),
                    (r'HERITAGE\s+COMMERCE', 'HERITAGE COMMERCE CORP'),
                    (r'WESTAMERICA', 'WESTAMERICA BANCORPORATION'),
                    (r'BANK\s+OF\s+MARIN', 'BANK OF MARIN BANCORP'),
                    (r'FIRST\s+NORTHERN', 'FIRST NORTHERN COMMUNITY BANCORP'),
                    (r'REDWOOD\s+TRUST', 'REDWOOD TRUST INC'),
                    (r'PROVIDENT\s+FINANCIAL', 'PROVIDENT FINANCIAL SERVICES'),
                    (r'LAKELAND\s+BANCORP', 'LAKELAND BANCORP'),
                    (r'OCEAN\s+FIRST', 'OCEANFIRST FINANCIAL CORP'),
                    (r'INVESTORS\s+BANCORP', 'INVESTORS BANCORP'),
                    (r'VALLEY\s+NATIONAL', 'VALLEY NATIONAL BANCORP'),
                    (r'PEAPACK.GLADSTONE', 'PEAPACK-GLADSTONE FINANCIAL CORP'),
                    (r'KEARNY\s+FINANCIAL', 'KEARNY FINANCIAL CORP'),
                    (r'NORTHFIELD\s+BANCORP', 'NORTHFIELD BANCORP INC'),
                    (r'FLUSHING\s+FINANCIAL', 'FLUSHING FINANCIAL CORP'),
                    (r'NEW\s+YORK\s+COMMUNITY', 'NEW YORK COMMUNITY BANCORP'),
                    (r'DIME\s+COMMUNITY', 'DIME COMMUNITY BANCSHARES'),
                    (r'ASTORIA\s+FINANCIAL', 'ASTORIA FINANCIAL CORP'),
                    (r'STERLING\s+BANCORP', 'STERLING BANCORP'),
                    (r'SIGNATURE\s+BANK', 'SIGNATURE BANK'),
                    (r'FIRST\s+OF\s+LONG\s+ISLAND', 'FIRST OF LONG ISLAND CORP'),
                    (r'SUFFOLK\s+BANCORP', 'SUFFOLK BANCORP'),
                    (r'HAMPTONS\s+BANCORP', 'HAMPTONS BANCORP'),
                    (r'BRIDGE\s+BANCORP', 'BRIDGE BANCORP'),
                    (r'COMMUNITY\s+WEST', 'COMMUNITY WEST BANCSHARES'),
                    (r'PACIFIC\s+CONTINENTAL', 'PACIFIC CONTINENTAL CORP'),
                    (r'UMPQUA\s+HOLDINGS', 'UMPQUA HOLDINGS CORP'),
                    (r'NORTHWEST\s+BANCORP', 'NORTHWEST BANCORP'),
                    (r'FIRST\s+INTERSTATE', 'FIRST INTERSTATE BANCSYSTEM'),
                    (r'GLACIER\s+BANCORP', 'GLACIER BANCORP INC'),
                    (r'MOUNTAIN\s+WEST', 'MOUNTAIN WEST FINANCIAL CORP'),
                    (r'FIRST\s+SECURITY', 'FIRST SECURITY BANCORP'),
                    (r'CACHE\s+VALLEY', 'CACHE VALLEY BANKING COMPANY'),
                    (r'ALTABANCORP', 'ALTABANCORP'),
                    (r'UTAH\s+COMMUNITY', 'UTAH COMMUNITY BANCORP'),
                    (r'CENTRAL\s+BANCOMPANY', 'CENTRAL BANCOMPANY INC'),
                    (r'GREAT\s+SOUTHERN', 'GREAT SOUTHERN BANCORP'),
                    (r'HAWTHORN\s+BANCSHARES', 'HAWTHORN BANCSHARES'),
                    (r'CENTRAL\s+FEDERAL', 'CENTRAL FEDERAL CORP'),
                    (r'FIRST\s+GUARANTY', 'FIRST GUARANTY BANCSHARES'),
                    (r'BUSINESS\s+FIRST', 'BUSINESS FIRST BANCSHARES'),
                    (r'RED\s+RIVER', 'RED RIVER BANCSHARES'),
                    (r'INVESTAR\s+HOLDING', 'INVESTAR HOLDING CORP'),
                    (r'ORIGIN\s+BANCORP', 'ORIGIN BANCORP INC'),
                    (r'SABINE\s+STATE', 'SABINE STATE BANK & TRUST CO'),
                    (r'AUSTIN\s+BANK', 'AUSTIN BANK TEXAS NA'),
                    (r'SOUTHSIDE\s+BANCSHARES', 'SOUTHSIDE BANCSHARES INC'),
                    (r'TEXAS\s+CAPITAL', 'TEXAS CAPITAL BANCSHARES'),
                    (r'PROSPERITY\s+BANCSHARES', 'PROSPERITY BANCSHARES INC'),
                    (r'INDEPENDENT\s+BANK', 'INDEPENDENT BANK GROUP'),
                    (r'FIRST\s+FINANCIAL', 'FIRST FINANCIAL BANKSHARES'),
                    (r'CULLEN/FROST', 'CULLEN/FROST BANKERS INC'),
                    (r'PLAINS\s+GP', 'PLAINS GP HOLDINGS LP'),
                    (r'HILLTOP\s+HOLDINGS', 'HILLTOP HOLDINGS INC'),
                    (r'VERITEX\s+HOLDINGS', 'VERITEX HOLDINGS INC'),
                    (r'GREEN\s+BANCORP', 'GREEN BANCORP INC'),
                    (r'ALLEGIANCE\s+BANCSHARES', 'ALLEGIANCE BANCSHARES INC'),
                    (r'SPIRIT\s+OF\s+TEXAS', 'SPIRIT OF TEXAS BANCSHARES'),
                    (r'FIRST\s+BANCSHARES', 'FIRST BANCSHARES INC'),
                    (r'RENASANT\s+CORP', 'RENASANT CORP'),
                    (r'BANCORPSOUTH', 'BANCORPSOUTH BANK'),
                    (r'TRUSTMARK', 'TRUSTMARK CORP'),
                    (r'HANCOCK\s+WHITNEY', 'HANCOCK WHITNEY CORP'),
                    (r'HOME\s+BANCORP', 'HOME BANCORP INC'),
                    (r'BUSINESS\s+FIRST', 'BUSINESS FIRST BANCSHARES INC'),
                    (r'IBERIABANK', 'IBERIABANK CORP'),
                    (r'FIRST\s+GUARANTY', 'FIRST GUARANTY BANCSHARES INC'),
                    (r'INVESTAR\s+HOLDING', 'INVESTAR HOLDING CORP'),
                    (r'ORIGIN\s+BANCORP', 'ORIGIN BANCORP INC'),
                    (r'RED\s+RIVER', 'RED RIVER BANCSHARES INC'),
                    (r'SIMMONS\s+FIRST', 'SIMMONS FIRST NATIONAL CORP'),
                    (r'BANK\s+OZK', 'BANK OZK'),
                    (r'ARVEST\s+BANK', 'ARVEST BANK GROUP'),
                    (r'CENTENNIAL\s+BANK', 'CENTENNIAL BANK HOLDINGS'),
                    (r'FIRST\s+SECURITY', 'FIRST SECURITY BANCORP'),
                    (r'SOUTHERN\s+BANCORP', 'SOUTHERN BANCORP INC'),
                    (r'DELTA\s+TRUST', 'DELTA TRUST & BANKING CORP'),
                    (r'FIRST\s+FINANCIAL', 'FIRST FINANCIAL CORP'),
                    (r'GREAT\s+SOUTHERN', 'GREAT SOUTHERN BANCORP INC'),
                    (r'HAWTHORN\s+BANCSHARES', 'HAWTHORN BANCSHARES INC'),
                    (r'CENTRAL\s+BANCOMPANY', 'CENTRAL BANCOMPANY INC'),
                    (r'FIRST\s+MID.ILLINOIS', 'FIRST MID-ILLINOIS BANCSHARES'),
                    (r'QCR\s+HOLDINGS', 'QCR HOLDINGS INC'),
                    (r'GREAT\s+WESTERN', 'GREAT WESTERN BANCORP INC'),
                    (r'FIRST\s+INTERSTATE', 'FIRST INTERSTATE BANCSYSTEM INC'),
                    (r'GLACIER\s+BANCORP', 'GLACIER BANCORP INC'),
                    (r'MOUNTAIN\s+WEST', 'MOUNTAIN WEST FINANCIAL CORP'),
                    (r'FIRST\s+SECURITY', 'FIRST SECURITY BANCORP'),
                    (r'CACHE\s+VALLEY', 'CACHE VALLEY BANKING COMPANY'),
                    (r'ALTABANCORP', 'ALTABANCORP'),
                    (r'UTAH\s+COMMUNITY', 'UTAH COMMUNITY BANCORP'),
                    (r'ZIONS\s+BANCORPORATION', 'ZIONS BANCORPORATION NA'),
                    (r'WESTERN\s+ALLIANCE', 'WESTERN ALLIANCE BANCORPORATION'),
                    (r'PACWEST\s+BANCORP', 'PACWEST BANCORP'),
                    (r'FIRST\s+REPUBLIC', 'FIRST REPUBLIC BANK'),
                    (r'SILICON\s+VALLEY', 'SILICON VALLEY BANK'),
                    (r'SQUARE\s+1', 'SQUARE 1 FINANCIAL INC'),
                    (r'BRIDGE\s+CAPITAL', 'BRIDGE CAPITAL HOLDINGS'),
                    (r'CALIFORNIA\s+FIRST', 'CALIFORNIA FIRST NATIONAL BANCORP'),
                    (r'TRISTATE\s+CAPITAL', 'TRISTATE CAPITAL HOLDINGS INC'),
                    (r'FIRST\s+FOUNDATION', 'FIRST FOUNDATION INC'),
                    (r'OPUS\s+BANK', 'OPUS BANK'),
                    (r'PREFERRED\s+BANK', 'PREFERRED BANK'),
                    (r'PACIFIC\s+CITY', 'PACIFIC CITY FINANCIAL CORP'),
                    (r'HANMI\s+FINANCIAL', 'HANMI FINANCIAL CORP'),
                    (r'NARA\s+BANCORP', 'NARA BANCORP INC'),
                    (r'WILSHIRE\s+BANCORP', 'WILSHIRE BANCORP INC'),
                    (r'ROYAL\s+BUSINESS', 'ROYAL BUSINESS BANK'),
                    (r'EAST\s+WEST', 'EAST WEST BANCORP INC'),
                    (r'CATHAY\s+GENERAL', 'CATHAY GENERAL BANCORP'),
                    (r'FIRST\s+FINANCIAL', 'FIRST FINANCIAL BANCORP OH'),
                    (r'STERLING\s+BANCORP', 'STERLING BANCORP DE'),
                    (r'BROOKLINE\s+BANCORP', 'BROOKLINE BANCORP INC'),
                    (r'LAKELAND\s+FINANCIAL', 'LAKELAND FINANCIAL CORP'),
                    (r'SANDY\s+SPRING', 'SANDY SPRING BANCORP INC'),
                    (r'UNITED\s+COMMUNITY', 'UNITED COMMUNITY BANKS INC'),
                    (r'ATLANTIC\s+UNION', 'ATLANTIC UNION BANKSHARES CORP'),
                    (r'FIRST\s+MERCHANTS', 'FIRST MERCHANTS CORP'),
                    (r'GERMAN\s+AMERICAN', 'GERMAN AMERICAN BANCORP INC'),
                    (r'PARK\s+NATIONAL', 'PARK NATIONAL CORP'),
                    (r'SOUTHERN\s+FIRST', 'SOUTHERN FIRST BANCSHARES INC'),
                    (r'COMMUNITY\s+BANK\s+SYSTEM', 'COMMUNITY BANK SYSTEM INC'),
                    (r'FIRST\s+BUSEY', 'FIRST BUSEY CORP'),
                    (r'NORTHFIELD\s+BANCORP', 'NORTHFIELD BANCORP INC MA'),
                    (r'ENTERPRISE\s+FINANCIAL', 'ENTERPRISE FINANCIAL SERVICES CORP'),
                    (r'MERIDIAN\s+BANCORP', 'MERIDIAN BANCORP INC'),
                    (r'SOUTHERN\s+MISSOURI', 'SOUTHERN MISSOURI BANCORP INC'),
                    (r'FIRST\s+BANCORP', 'FIRST BANCORP PR'),
                    (r'AMERIS\s+BANCORP', 'AMERIS BANCORP'),
                    (r'RENASANT\s+CORP', 'RENASANT CORP'),
                    (r'SIMMONS\s+FIRST', 'SIMMONS FIRST NATIONAL CORP'),
                    (r'ORIGIN\s+BANCORP', 'ORIGIN BANCORP INC'),
                    (r'SOUTHSIDE\s+BANCSHARES', 'SOUTHSIDE BANCSHARES INC'),
                    (r'CENTRAL\s+PACIFIC', 'CENTRAL PACIFIC FINANCIAL CORP'),
                    (r'BANNER\s+CORP', 'BANNER CORP'),
                    (r'COLUMBIA\s+BANKING', 'COLUMBIA BANKING SYSTEM INC'),
                    (r'PACIFIC\s+PREMIER', 'PACIFIC PREMIER BANCORP INC'),
                    (r'HERITAGE\s+FINANCIAL', 'HERITAGE FINANCIAL CORP'),
                    (r'WASHINGTON\s+FEDERAL', 'WASHINGTON FEDERAL INC'),
                    (r'NORTHWEST\s+BANCSHARES', 'NORTHWEST BANCSHARES INC'),
                    (r'FIRST\s+COMMONWEALTH', 'FIRST COMMONWEALTH FINANCIAL CORP'),
                    (r'S&T\s+BANCORP', 'S&T BANCORP INC'),
                    (r'PENNS\s+WOODS', 'PENNS WOODS BANCORP INC'),
                    (r'CITIZENS\s+FINANCIAL', 'CITIZENS FINANCIAL GROUP INC'),
                    (r'EASTERN\s+BANKSHARES', 'EASTERN BANKSHARES INC'),
                    (r'BERKSHIRE\s+HILLS', 'BERKSHIRE HILLS BANCORP INC'),
                    (r'COMMUNITY\s+BANKERS', 'COMMUNITY BANKERS TRUST CORP'),
                    (r'FIRST\s+DEFIANCE', 'FIRST DEFIANCE FINANCIAL CORP'),
                    (r'PREMIER\s+FINANCIAL', 'PREMIER FINANCIAL BANCORP INC'),
                    (r'UNITED\s+BANKSHARES', 'UNITED BANKSHARES INC'),
                    (r'CITY\s+HOLDING', 'CITY HOLDING CO'),
                    (r'WESBANCO', 'WESBANCO INC'),
                    (r'FIRST\s+UNITED', 'FIRST UNITED CORP'),
                    (r'COMMUNITY\s+FINANCIAL', 'COMMUNITY FINANCIAL CORP MD'),
                    (r'PINNACLE\s+FINANCIAL', 'PINNACLE FINANCIAL PARTNERS INC'),
                    (r'FIRST\s+TENNESSEE', 'FIRST TENNESSEE NATIONAL CORP'),
                    (r'IBERIABANK', 'IBERIABANK CORP'),
                    (r'CAPITAL\s+CITY\s+BANK', 'CAPITAL CITY BANK GROUP INC'),
                    (r'SEACOAST\s+BANKING', 'SEACOAST BANKING CORP OF FLORIDA'),
                    (r'CENTERSTATE\s+BANK', 'CENTERSTATE BANK CORP'),
                    (r'FIRST\s+MIDWEST', 'FIRST MIDWEST BANCORP INC'),
                    (r'GREAT\s+WESTERN', 'GREAT WESTERN BANCORP INC'),
                    (r'GLACIER\s+BANCORP', 'GLACIER BANCORP INC'),
                    (r'MOUNTAIN\s+WEST', 'MOUNTAIN WEST FINANCIAL CORP'),
                    (r'WESTERN\s+SIERRA', 'WESTERN SIERRA BANCORP'),
                    (r'CENTRAL\s+VALLEY', 'CENTRAL VALLEY COMMUNITY BANCORP'),
                    (r'SIERRA\s+BANCORP', 'SIERRA BANCORP'),
                    (r'PREFERRED\s+BANK', 'PREFERRED BANK'),
                    (r'PACIFIC\s+CITY', 'PACIFIC CITY FINANCIAL CORP'),
                    (r'HANMI\s+FINANCIAL', 'HANMI FINANCIAL CORP'),
                    (r'NARA\s+BANCORP', 'NARA BANCORP INC'),
                    (r'WILSHIRE\s+BANCORP', 'WILSHIRE BANCORP INC'),
                    (r'ROYAL\s+BUSINESS', 'ROYAL BUSINESS BANK'),
                    (r'FIRST\s+FOUNDATION', 'FIRST FOUNDATION INC'),
                    (r'OPUS\s+BANK', 'OPUS BANK'),
                    (r'SQUARE\s+1\s+FINANCIAL', 'SQUARE 1 FINANCIAL INC'),
                    (r'BRIDGE\s+CAPITAL', 'BRIDGE CAPITAL HOLDINGS'),
                    (r'CALIFORNIA\s+FIRST', 'CALIFORNIA FIRST NATIONAL BANCORP'),
                    (r'TRISTATE\s+CAPITAL', 'TRISTATE CAPITAL HOLDINGS INC'),
                    (r'FIRST\s+NATIONAL', 'FIRST NATIONAL CORP'),
                    (r'NATIONAL\s+PENN', 'NATIONAL PENN BANCSHARES INC'),
                    (r'SUSQUEHANNA', 'SUSQUEHANNA BANCSHARES INC'),
                    (r'ORRSTOWN\s+FINANCIAL', 'ORRSTOWN FINANCIAL SERVICES INC'),
                    (r'FARMERS\s+NATIONAL', 'FARMERS NATIONAL BANC CORP'),
                    (r'FIRST\s+DEFIANCE', 'FIRST DEFIANCE FINANCIAL CORP'),
                    (r'PARK\s+STERLING', 'PARK STERLING CORP'),
                    (r'SOUTH\s+STATE', 'SOUTH STATE CORP'),
                    (r'SCBT\s+FINANCIAL', 'SCBT FINANCIAL CORP'),
                    (r'FIRST\s+FINANCIAL\s+NORTHWEST', 'FIRST FINANCIAL NORTHWEST INC'),
                    (r'HERITAGE\s+COMMERCE', 'HERITAGE COMMERCE CORP'),
                    (r'WESTAMERICA', 'WESTAMERICA BANCORPORATION'),
                    (r'BANK\s+OF\s+MARIN', 'BANK OF MARIN BANCORP'),
                    (r'FIRST\s+NORTHERN', 'FIRST NORTHERN COMMUNITY BANCORP'),
                    (r'REDWOOD\s+TRUST', 'REDWOOD TRUST INC'),
                    (r'PROVIDENT\s+FINANCIAL', 'PROVIDENT FINANCIAL SERVICES INC'),
                    (r'LAKELAND\s+BANCORP', 'LAKELAND BANCORP INC'),
                    (r'OCEAN\s+FIRST', 'OCEANFIRST FINANCIAL CORP'),
                    (r'INVESTORS\s+BANCORP', 'INVESTORS BANCORP INC'),
                    (r'VALLEY\s+NATIONAL', 'VALLEY NATIONAL BANCORP'),
                    (r'PEAPACK.GLADSTONE', 'PEAPACK-GLADSTONE FINANCIAL CORP'),
                    (r'KEARNY\s+FINANCIAL', 'KEARNY FINANCIAL CORP'),
                    (r'NORTHFIELD\s+BANCORP', 'NORTHFIELD BANCORP INC'),
                    (r'FLUSHING\s+FINANCIAL', 'FLUSHING FINANCIAL CORP'),
                    (r'NEW\s+YORK\s+COMMUNITY', 'NEW YORK COMMUNITY BANCORP INC'),
                    (r'DIME\s+COMMUNITY', 'DIME COMMUNITY BANCSHARES INC'),
                    (r'ASTORIA\s+FINANCIAL', 'ASTORIA FINANCIAL CORP'),
                    (r'STERLING\s+BANCORP', 'STERLING BANCORP'),
                    (r'SIGNATURE\s+BANK', 'SIGNATURE BANK'),
                    (r'FIRST\s+OF\s+LONG\s+ISLAND', 'FIRST OF LONG ISLAND CORP'),
                    (r'SUFFOLK\s+BANCORP', 'SUFFOLK BANCORP'),
                    (r'HAMPTONS\s+BANCORP', 'HAMPTONS BANCORP'),
                    (r'BRIDGE\s+BANCORP', 'BRIDGE BANCORP INC'),
                    (r'COMMUNITY\s+WEST', 'COMMUNITY WEST BANCSHARES'),
                    (r'PACIFIC\s+CONTINENTAL', 'PACIFIC CONTINENTAL CORP'),
                    (r'UMPQUA\s+HOLDINGS', 'UMPQUA HOLDINGS CORP'),
                    (r'NORTHWEST\s+BANCORP', 'NORTHWEST BANCORP INC'),
                    (r'FIRST\s+INTERSTATE', 'FIRST INTERSTATE BANCSYSTEM INC'),
                    (r'GLACIER\s+BANCORP', 'GLACIER BANCORP INC'),
                    (r'MOUNTAIN\s+WEST', 'MOUNTAIN WEST FINANCIAL CORP'),
                    (r'FIRST\s+SECURITY', 'FIRST SECURITY BANCORP'),
                    (r'CACHE\s+VALLEY', 'CACHE VALLEY BANKING COMPANY'),
                    (r'ALTABANCORP', 'ALTABANCORP'),
                    (r'UTAH\s+COMMUNITY', 'UTAH COMMUNITY BANCORP'),
                    (r'CENTRAL\s+BANCOMPANY', 'CENTRAL BANCOMPANY INC'),
                    (r'GREAT\s+SOUTHERN', 'GREAT SOUTHERN BANCORP INC'),
                    (r'HAWTHORN\s+BANCSHARES', 'HAWTHORN BANCSHARES INC'),
                    (r'CENTRAL\s+FEDERAL', 'CENTRAL FEDERAL CORP'),
                    (r'FIRST\s+GUARANTY', 'FIRST GUARANTY BANCSHARES INC'),
                    (r'BUSINESS\s+FIRST', 'BUSINESS FIRST BANCSHARES INC'),
                    (r'RED\s+RIVER', 'RED RIVER BANCSHARES INC'),
                    (r'INVESTAR\s+HOLDING', 'INVESTAR HOLDING CORP'),
                    (r'ORIGIN\s+BANCORP', 'ORIGIN BANCORP INC'),
                    (r'SABINE\s+STATE', 'SABINE STATE BANK & TRUST CO'),
                    (r'AUSTIN\s+BANK', 'AUSTIN BANK TEXAS NA'),
                    (r'SOUTHSIDE\s+BANCSHARES', 'SOUTHSIDE BANCSHARES INC'),
                    (r'TEXAS\s+CAPITAL', 'TEXAS CAPITAL BANCSHARES INC'),
                    (r'PROSPERITY\s+BANCSHARES', 'PROSPERITY BANCSHARES INC'),
                    (r'INDEPENDENT\s+BANK', 'INDEPENDENT BANK GROUP INC'),
                    (r'FIRST\s+FINANCIAL', 'FIRST FINANCIAL BANKSHARES INC'),
                    (r'CULLEN/FROST', 'CULLEN/FROST BANKERS INC'),
                    (r'PLAINS\s+GP', 'PLAINS GP HOLDINGS LP'),
                    (r'HILLTOP\s+HOLDINGS', 'HILLTOP HOLDINGS INC'),
                    (r'VERITEX\s+HOLDINGS', 'VERITEX HOLDINGS INC'),
                    (r'GREEN\s+BANCORP', 'GREEN BANCORP INC'),
                    (r'ALLEGIANCE\s+BANCSHARES', 'ALLEGIANCE BANCSHARES INC'),
                    (r'SPIRIT\s+OF\s+TEXAS', 'SPIRIT OF TEXAS BANCSHARES INC'),
                    (r'FIRST\s+BANCSHARES', 'FIRST BANCSHARES INC MS'),
                    (r'RENASANT\s+CORP', 'RENASANT CORP'),
                    (r'BANCORPSOUTH', 'BANCORPSOUTH BANK'),
                    (r'TRUSTMARK', 'TRUSTMARK CORP'),
                    (r'HANCOCK\s+WHITNEY', 'HANCOCK WHITNEY CORP'),
                    (r'HOME\s+BANCORP', 'HOME BANCORP INC'),
                    (r'BUSINESS\s+FIRST', 'BUSINESS FIRST BANCSHARES INC'),
                    (r'IBERIABANK', 'IBERIABANK CORP'),
                    (r'FIRST\s+GUARANTY', 'FIRST GUARANTY BANCSHARES INC'),
                    (r'INVESTAR\s+HOLDING', 'INVESTAR HOLDING CORP'),
                    (r'ORIGIN\s+BANCORP', 'ORIGIN BANCORP INC'),
                    (r'RED\s+RIVER', 'RED RIVER BANCSHARES INC'),
                    (r'SIMMONS\s+FIRST', 'SIMMONS FIRST NATIONAL CORP'),
                    (r'BANK\s+OZK', 'BANK OZK'),
                    (r'ARVEST\s+BANK', 'ARVEST BANK GROUP INC'),
                    (r'CENTENNIAL\s+BANK', 'CENTENNIAL BANK HOLDINGS INC'),
                    (r'FIRST\s+SECURITY', 'FIRST SECURITY BANCORP'),
                    (r'SOUTHERN\s+BANCORP', 'SOUTHERN BANCORP INC'),
                    (r'DELTA\s+TRUST', 'DELTA TRUST & BANKING CORP'),
                    (r'FIRST\s+FINANCIAL', 'FIRST FINANCIAL CORP IN'),
                    (r'GREAT\s+SOUTHERN', 'GREAT SOUTHERN BANCORP INC'),
                    (r'HAWTHORN\s+BANCSHARES', 'HAWTHORN BANCSHARES INC'),
                    (r'CENTRAL\s+BANCOMPANY', 'CENTRAL BANCOMPANY INC'),
                    (r'FIRST\s+MID.ILLINOIS', 'FIRST MID-ILLINOIS BANCSHARES INC'),
                    (r'QCR\s+HOLDINGS', 'QCR HOLDINGS INC'),
                    (r'GREAT\s+WESTERN', 'GREAT WESTERN BANCORP INC'),
                    (r'FIRST\s+INTERSTATE', 'FIRST INTERSTATE BANCSYSTEM INC'),
                    (r'GLACIER\s+BANCORP', 'GLACIER BANCORP INC'),
                    (r'MOUNTAIN\s+WEST', 'MOUNTAIN WEST FINANCIAL CORP'),
                    (r'FIRST\s+SECURITY', 'FIRST SECURITY BANCORP'),
                    (r'CACHE\s+VALLEY', 'CACHE VALLEY BANKING COMPANY'),
                    (r'ALTABANCORP', 'ALTABANCORP'),
                    (r'UTAH\s+COMMUNITY', 'UTAH COMMUNITY BANCORP'),
                    (r'ZIONS\s+BANCORPORATION', 'ZIONS BANCORPORATION NA'),
                    (r'WESTERN\s+ALLIANCE', 'WESTERN ALLIANCE BANCORPORATION'),
                    (r'PACWEST\s+BANCORP', 'PACWEST BANCORP'),
                    (r'FIRST\s+REPUBLIC', 'FIRST REPUBLIC BANK'),
                    (r'SILICON\s+VALLEY', 'SILICON VALLEY BANK'),
                    (r'SQUARE\s+1', 'SQUARE 1 FINANCIAL INC'),
                    (r'BRIDGE\s+CAPITAL', 'BRIDGE CAPITAL HOLDINGS'),
                    (r'CALIFORNIA\s+FIRST', 'CALIFORNIA FIRST NATIONAL BANCORP'),
                    (r'TRISTATE\s+CAPITAL', 'TRISTATE CAPITAL HOLDINGS INC'),
                    (r'FIRST\s+FOUNDATION', 'FIRST FOUNDATION INC'),
                    (r'OPUS\s+BANK', 'OPUS BANK'),
                    (r'PREFERRED\s+BANK', 'PREFERRED BANK'),
                    (r'PACIFIC\s+CITY', 'PACIFIC CITY FINANCIAL CORP'),
                    (r'HANMI\s+FINANCIAL', 'HANMI FINANCIAL CORP'),
                    (r'NARA\s+BANCORP', 'NARA BANCORP INC'),
                    (r'WILSHIRE\s+BANCORP', 'WILSHIRE BANCORP INC'),
                    (r'ROYAL\s+BUSINESS', 'ROYAL BUSINESS BANK'),
                    (r'EAST\s+WEST', 'EAST WEST BANCORP INC'),
                    (r'CATHAY\s+GENERAL', 'CATHAY GENERAL BANCORP'),
                    (r'FIRST\s+FINANCIAL', 'FIRST FINANCIAL BANCORP OH'),
                    (r'STERLING\s+BANCORP', 'STERLING BANCORP DE'),
                    (r'BROOKLINE\s+BANCORP', 'BROOKLINE BANCORP INC'),
                    (r'LAKELAND\s+FINANCIAL', 'LAKELAND FINANCIAL CORP'),
                    (r'SANDY\s+SPRING', 'SANDY SPRING BANCORP INC'),
                    (r'UNITED\s+COMMUNITY', 'UNITED COMMUNITY BANKS INC'),
                    (r'ATLANTIC\s+UNION', 'ATLANTIC UNION BANKSHARES CORP'),
                    (r'FIRST\s+MERCHANTS', 'FIRST MERCHANTS CORP'),
                    (r'GERMAN\s+AMERICAN', 'GERMAN AMERICAN BANCORP INC'),
                    (r'PARK\s+NATIONAL', 'PARK NATIONAL CORP'),
                    (r'SOUTHERN\s+FIRST', 'SOUTHERN FIRST BANCSHARES INC'),
                    (r'COMMUNITY\s+BANK\s+SYSTEM', 'COMMUNITY BANK SYSTEM INC'),
                    (r'FIRST\s+BUSEY', 'FIRST BUSEY CORP'),
                    (r'NORTHFIELD\s+BANCORP', 'NORTHFIELD BANCORP INC MA'),
                    (r'ENTERPRISE\s+FINANCIAL', 'ENTERPRISE FINANCIAL SERVICES CORP'),
                    (r'MERIDIAN\s+BANCORP', 'MERIDIAN BANCORP INC'),
                    (r'SOUTHERN\s+MISSOURI', 'SOUTHERN MISSOURI BANCORP INC'),
                    (r'FIRST\s+BANCORP', 'FIRST BANCORP PR'),
                    (r'AMERIS\s+BANCORP', 'AMERIS BANCORP'),
                    (r'RENASANT\s+CORP', 'RENASANT CORP'),
                    (r'SIMMONS\s+FIRST', 'SIMMONS FIRST NATIONAL CORP'),
                    (r'ORIGIN\s+BANCORP', 'ORIGIN BANCORP INC'),
                    (r'SOUTHSIDE\s+BANCSHARES', 'SOUTHSIDE BANCSHARES INC'),
                    (r'CENTRAL\s+PACIFIC', 'CENTRAL PACIFIC FINANCIAL CORP'),
                    (r'BANNER\s+CORP', 'BANNER CORP'),
                    (r'COLUMBIA\s+BANKING', 'COLUMBIA BANKING SYSTEM INC'),
                    (r'PACIFIC\s+PREMIER', 'PACIFIC PREMIER BANCORP INC'),
                    (r'HERITAGE\s+FINANCIAL', 'HERITAGE FINANCIAL CORP'),
                    (r'WASHINGTON\s+FEDERAL', 'WASHINGTON FEDERAL INC'),
                    (r'NORTHWEST\s+BANCSHARES', 'NORTHWEST BANCSHARES INC'),
                    (r'FIRST\s+COMMONWEALTH', 'FIRST COMMONWEALTH FINANCIAL CORP'),
                    (r'S&T\s+BANCORP', 'S&T BANCORP INC'),
                    (r'PENNS\s+WOODS', 'PENNS WOODS BANCORP INC'),
                    (r'CITIZENS\s+FINANCIAL', 'CITIZENS FINANCIAL GROUP INC'),
                    (r'EASTERN\s+BANKSHARES', 'EASTERN BANKSHARES INC'),
                    (r'BERKSHIRE\s+HILLS', 'BERKSHIRE HILLS BANCORP INC'),
                    (r'COMMUNITY\s+BANKERS', 'COMMUNITY BANKERS TRUST CORP'),
                    (r'FIRST\s+DEFIANCE', 'FIRST DEFIANCE FINANCIAL CORP'),
                    (r'PREMIER\s+FINANCIAL', 'PREMIER FINANCIAL BANCORP INC'),
                    (r'UNITED\s+BANKSHARES', 'UNITED BANKSHARES INC'),
                    (r'CITY\s+HOLDING', 'CITY HOLDING CO'),
                    (r'WESBANCO', 'WESBANCO INC'),
                    (r'FIRST\s+UNITED', 'FIRST UNITED CORP'),
                    (r'COMMUNITY\s+FINANCIAL', 'COMMUNITY FINANCIAL CORP MD'),
                    (r'PINNACLE\s+FINANCIAL', 'PINNACLE FINANCIAL PARTNERS INC'),
                    (r'FIRST\s+TENNESSEE', 'FIRST TENNESSEE NATIONAL CORP'),
                    (r'IBERIABANK', 'IBERIABANK CORP'),
                    (r'CAPITAL\s+CITY\s+BANK', 'CAPITAL CITY BANK GROUP INC'),
                    (r'SEACOAST\s+BANKING', 'SEACOAST BANKING CORP OF FLORIDA'),
                    (r'CENTERSTATE\s+BANK', 'CENTERSTATE BANK CORP'),
                    (r'FIRST\s+MIDWEST', 'FIRST MIDWEST BANCORP INC'),
                    (r'GREAT\s+WESTERN', 'GREAT WESTERN BANCORP INC'),
                    (r'GLACIER\s+BANCORP', 'GLACIER BANCORP INC'),
                    (r'MOUNTAIN\s+WEST', 'MOUNTAIN WEST FINANCIAL CORP'),
                    (r'WESTERN\s+SIERRA', 'WESTERN SIERRA BANCORP'),
                    (r'CENTRAL\s+VALLEY', 'CENTRAL VALLEY COMMUNITY BANCORP'),
                    (r'SIERRA\s+BANCORP', 'SIERRA BANCORP'),
                    (r'PREFERRED\s+BANK', 'PREFERRED BANK'),
                    (r'PACIFIC\s+CITY', 'PACIFIC CITY FINANCIAL CORP'),
                    (r'HANMI\s+FINANCIAL', 'HANMI FINANCIAL CORP'),
                    (r'NARA\s+BANCORP', 'NARA BANCORP INC'),
                    (r'WILSHIRE\s+BANCORP', 'WILSHIRE BANCORP INC'),
                    (r'ROYAL\s+BUSINESS', 'ROYAL BUSINESS BANK'),
                    (r'FIRST\s+FOUNDATION', 'FIRST FOUNDATION INC'),
                    (r'OPUS\s+BANK', 'OPUS BANK'),
                    (r'SQUARE\s+1\s+FINANCIAL', 'SQUARE 1 FINANCIAL INC'),
                    (r'BRIDGE\s+CAPITAL', 'BRIDGE CAPITAL HOLDINGS'),
                    (r'CALIFORNIA\s+FIRST', 'CALIFORNIA FIRST NATIONAL BANCORP'),
                    (r'TRISTATE\s+CAPITAL', 'TRISTATE CAPITAL HOLDINGS INC'),
                    (r'FIRST\s+NATIONAL', 'FIRST NATIONAL CORP'),
                    (r'NATIONAL\s+PENN', 'NATIONAL PENN BANCSHARES INC'),
                    (r'SUSQUEHANNA', 'SUSQUEHANNA BANCSHARES INC'),
                    (r'ORRSTOWN\s+FINANCIAL', 'ORRSTOWN FINANCIAL SERVICES INC'),
                    (r'FARMERS\s+NATIONAL', 'FARMERS NATIONAL BANC CORP'),
                    (r'FIRST\s+DEFIANCE', 'FIRST DEFIANCE FINANCIAL CORP'),
                    (r'PARK\s+STERLING', 'PARK STERLING CORP'),
                    (r'SOUTH\s+STATE', 'SOUTH STATE CORP'),
                    (r'SCBT\s+FINANCIAL', 'SCBT FINANCIAL CORP'),
                    (r'FIRST\s+FINANCIAL\s+NORTHWEST', 'FIRST FINANCIAL NORTHWEST INC'),
                    (r'HERITAGE\s+COMMERCE', 'HERITAGE COMMERCE CORP'),
                    (r'WESTAMERICA', 'WESTAMERICA BANCORPORATION'),
                    (r'BANK\s+OF\s+MARIN', 'BANK OF MARIN BANCORP'),
                    (r'FIRST\s+NORTHERN', 'FIRST NORTHERN COMMUNITY BANCORP'),
                    (r'REDWOOD\s+TRUST', 'REDWOOD TRUST INC'),
                    (r'PROVIDENT\s+FINANCIAL', 'PROVIDENT FINANCIAL SERVICES INC'),
                    (r'LAKELAND\s+BANCORP', 'LAKELAND BANCORP INC'),
                    (r'OCEAN\s+FIRST', 'OCEANFIRST FINANCIAL CORP'),
                    (r'INVESTORS\s+BANCORP', 'INVESTORS BANCORP INC'),
                    (r'VALLEY\s+NATIONAL', 'VALLEY NATIONAL BANCORP'),
                    (r'PEAPACK.GLADSTONE', 'PEAPACK-GLADSTONE FINANCIAL CORP'),
                    (r'KEARNY\s+FINANCIAL', 'KEARNY FINANCIAL CORP'),
                    (r'NORTHFIELD\s+BANCORP', 'NORTHFIELD BANCORP INC'),
                    (r'FLUSHING\s+FINANCIAL', 'FLUSHING FINANCIAL CORP'),
                    (r'NEW\s+YORK\s+COMMUNITY', 'NEW YORK COMMUNITY BANCORP INC'),
                    (r'DIME\s+COMMUNITY', 'DIME COMMUNITY BANCSHARES INC'),
                    (r'ASTORIA\s+FINANCIAL', 'ASTORIA FINANCIAL CORP'),
                    (r'STERLING\s+BANCORP', 'STERLING BANCORP'),
                    (r'SIGNATURE\s+BANK', 'SIGNATURE BANK'),
                    (r'FIRST\s+OF\s+LONG\s+ISLAND', 'FIRST OF LONG ISLAND CORP'),
                    (r'SUFFOLK\s+BANCORP', 'SUFFOLK BANCORP'),
                    (r'HAMPTONS\s+BANCORP', 'HAMPTONS BANCORP'),
                    (r'BRIDGE\s+BANCORP', 'BRIDGE BANCORP INC'),
                    (r'COMMUNITY\s+WEST', 'COMMUNITY WEST BANCSHARES'),
                    (r'PACIFIC\s+CONTINENTAL', 'PACIFIC CONTINENTAL CORP'),
                    (r'UMPQUA\s+HOLDINGS', 'UMPQUA HOLDINGS CORP'),
                    (r'NORTHWEST\s+BANCORP', 'NORTHWEST BANCORP INC'),
                    (r'FIRST\s+INTERSTATE', 'FIRST INTERSTATE BANCSYSTEM INC'),
                    (r'GLACIER\s+BANCORP', 'GLACIER BANCORP INC'),
                    (r'MOUNTAIN\s+WEST', 'MOUNTAIN WEST FINANCIAL CORP'),
                    (r'FIRST\s+SECURITY', 'FIRST SECURITY BANCORP'),
                    (r'CACHE\s+VALLEY', 'CACHE VALLEY BANKING COMPANY'),
                    (r'ALTABANCORP', 'ALTABANCORP'),
                    (r'UTAH\s+COMMUNITY', 'UTAH COMMUNITY BANCORP'),
                    (r'CENTRAL\s+BANCOMPANY', 'CENTRAL BANCOMPANY INC'),
                    (r'GREAT\s+SOUTHERN', 'GREAT SOUTHERN BANCORP INC'),
                    (r'HAWTHORN\s+BANCSHARES', 'HAWTHORN BANCSHARES INC'),
                    (r'CENTRAL\s+FEDERAL', 'CENTRAL FEDERAL CORP'),
                    (r'FIRST\s+GUARANTY', 'FIRST GUARANTY BANCSHARES INC'),
                    (r'BUSINESS\s+FIRST', 'BUSINESS FIRST BANCSHARES INC'),
                    (r'RED\s+RIVER', 'RED RIVER BANCSHARES INC'),
                    (r'INVESTAR\s+HOLDING', 'INVESTAR HOLDING CORP'),
                    (r'ORIGIN\s+BANCORP', 'ORIGIN BANCORP INC'),
                    (r'SABINE\s+STATE', 'SABINE STATE BANK & TRUST CO'),
                    (r'AUSTIN\s+BANK', 'AUSTIN BANK TEXAS NA'),
                    (r'SOUTHSIDE\s+BANCSHARES', 'SOUTHSIDE BANCSHARES INC'),
                    (r'TEXAS\s+CAPITAL', 'TEXAS CAPITAL BANCSHARES INC'),
                    (r'PROSPERITY\s+BANCSHARES', 'PROSPERITY BANCSHARES INC'),
                    (r'INDEPENDENT\s+BANK', 'INDEPENDENT BANK GROUP INC'),
                    (r'FIRST\s+FINANCIAL', 'FIRST FINANCIAL BANKSHARES INC'),
                    (r'CULLEN/FROST', 'CULLEN/FROST BANKERS INC'),
                    (r'PLAINS\s+GP', 'PLAINS GP HOLDINGS LP'),
                    (r'HILLTOP\s+HOLDINGS', 'HILLTOP HOLDINGS INC'),
                    (r'VERITEX\s+HOLDINGS', 'VERITEX HOLDINGS INC'),
                    (r'GREEN\s+BANCORP', 'GREEN BANCORP INC'),
                    (r'ALLEGIANCE\s+BANCSHARES', 'ALLEGIANCE BANCSHARES INC'),
                    (r'SPIRIT\s+OF\s+TEXAS', 'SPIRIT OF TEXAS BANCSHARES INC')
                ]
                
                    for pattern, name in bank_patterns:
                        if re.search(pattern, text_upper):
                            bank_name = name
                            break
                
                # Extract year
                import re
                years = re.findall(r'20(2[0-5])', text[:2000])
                if years:
                    year = '20' + years[0]
                
                # Generate unique ID and store content in S3
                import uuid
                doc_id = str(uuid.uuid4())
                
                # Create S3 bucket if it doesn't exist
                try:
                    s3_client.head_bucket(Bucket=S3_BUCKET)
                except:
                    try:
                        s3_client.create_bucket(Bucket=S3_BUCKET)
                    except Exception as e:
                        print(f"S3 bucket creation failed: {e}")
                
                # Store PDF content in S3
                try:
                    s3_client.put_object(
                        Bucket=S3_BUCKET,
                        Key=f"pdf-content/{doc_id}.txt",
                        Body=text.encode('utf-8'),
                        ContentType='text/plain'
                    )
                except Exception as e:
                    print(f"S3 upload failed: {e}")
                
                analyzed_docs.append({
                    'filename': file.filename,
                    'bank_name': bank_name,
                    'form_type': form_type,
                    'year': year,
                    'size': len(file_data),
                    'pages': len(pdf_reader.pages),
                    'doc_id': doc_id
                })
        
        return jsonify({'documents': analyzed_docs})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat-local', methods=['POST'])
def chat_local():
    try:
        message = request.form.get('message')
        files = request.files.getlist('files')
        
        # Extract text from PDFs and identify bank/form/year
        documents = []
        for file in files:
            if file.filename.endswith('.pdf'):
                file_data = file.read()
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_data))
                text = ''
                # Read ALL pages to get complete content
                for page in pdf_reader.pages:
                    text += page.extract_text() + '\n'
                
                # Extract bank name, form type, year from content
                bank_name = 'Unknown Bank'
                form_type = '10-K' if '10-K' in text[:2000] else '10-Q' if '10-Q' in text[:2000] else 'Unknown'
                year = '2024'  # Default
                
                # Look for bank name patterns
                text_upper = text[:3000].upper()
                if 'WEBSTER FINANCIAL' in text_upper:
                    bank_name = 'WEBSTER FINANCIAL'
                elif 'JPMORGAN' in text_upper:
                    bank_name = 'JPMORGAN CHASE'
                elif 'BANK OF AMERICA' in text_upper:
                    bank_name = 'BANK OF AMERICA'
                elif 'WELLS FARGO' in text_upper:
                    bank_name = 'WELLS FARGO'
                elif 'CITIGROUP' in text_upper:
                    bank_name = 'CITIGROUP'
                elif 'GOLDMAN SACHS' in text_upper:
                    bank_name = 'GOLDMAN SACHS'
                
                # Look for year patterns
                import re
                years = re.findall(r'20(2[0-5])', text[:1000])
                if years:
                    year = '20' + years[0]
                
                documents.append({
                    'filename': file.filename,
                    'content': text,
                    'bank_name': bank_name,
                    'form_type': form_type,
                    'year': year
                })
        
        bedrock = boto3.client('bedrock-runtime')
        
        # Use more content for better analysis - chunk if too large
        context_parts = []
        for doc in documents:
            content = doc['content']
            # Use first 15000 chars for comprehensive analysis while staying within token limits
            content_chunk = content[:15000] if len(content) > 15000 else content
            context_parts.append(f"From {doc['bank_name']} {doc['form_type']} {doc['year']}:\n{content_chunk}")
        
        context = '\n\n'.join(context_parts)
        
        prompt = f"""You are a financial analyst. Based on these uploaded SEC financial documents:\n\n{context}\n\nProvide a detailed analysis to answer: {message}\n\nUse specific data, numbers, and quotes from the documents above. Focus on concrete financial metrics and performance indicators."""
        
        response = bedrock.converse(
            modelId="anthropic.claude-3-haiku-20240307-v1:0",
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 2000}
        )
        
        return jsonify({
            'response': response['output']['message']['content'][0]['text'],
            'sources': [{'bank': doc['bank_name'], 'filing_type': doc['form_type'], 'year': doc['year']} for doc in documents]
        })
    except Exception as e:
        return jsonify({'response': f"Error: {str(e)}"})

@app.route('/api/chat', methods=['POST'])
def chat_with_ai():
    try:
        data = request.json
        question = data['question']
        bank_name = data['bankName']
        use_rag = data.get('useRAG', True)
        
        bedrock = boto3.client('bedrock-runtime')
        
        if use_rag:
            # Use RAG system
            relevant_docs = rag_system.search(question, bank_filter=bank_name, k=3)
            
            context = "\n\n".join([
                f"From {doc['metadata']['bank']} {doc['metadata']['filing_type']} {doc['metadata']['year']}:\n{doc['content'][:800]}..."
                for doc in relevant_docs
            ])
            
            prompt = f"""
You are a financial analyst. Answer this question about {bank_name}: {question}

Use the following SEC filing excerpts as context:

{context}

Provide a detailed analysis based on the actual filing data above. Include specific references to the filings when possible.
"""
            
            sources = [{
                'bank': doc['metadata']['bank'],
                'filing_type': doc['metadata']['filing_type'],
                'year': doc['metadata']['year'],
                'score': doc['score']
            } for doc in relevant_docs]
            
        else:
            # Use Live EDGAR API
            custom_cik = data.get('cik')
            print(f"LIVE MODE: Downloading real SEC filings for {bank_name}")
            if custom_cik:
                print(f"Using custom CIK: {custom_cik}")
            live_filings = sec_api.get_recent_filings(bank_name, limit=3, custom_cik=custom_cik)
            print(f"LIVE MODE: Found {len(live_filings)} filings")
            
            context_parts = []
            for filing in live_filings:
                print(f"LIVE MODE: Downloading {filing['form']} {filing['accession']}")
                content = sec_api.get_filing_content(filing['cik'], filing['accession'], max_length=1000)
                if content:
                    context_parts.append(f"From LIVE {filing['form']} filed {filing['filing_date']}:\n{content[:500]}...")
                    print(f"LIVE MODE: Downloaded {len(content)} chars")
            
            context = "\n\n".join(context_parts) if context_parts else "No recent filings available from SEC.gov"
            
            prompt = f"""
You are a financial analyst. Answer this question about {bank_name}: {question}

Use the following LIVE SEC filing excerpts downloaded in real-time from SEC.gov:

{context}

Provide analysis based on this live SEC data downloaded just now. Include specific references to the filings when possible.
"""
            
            sources = [{
                'bank': bank_name,
                'filing_type': f"LIVE {filing['form']}",
                'year': filing['filing_date'][:4],
                'score': 1.0
            } for filing in live_filings]
        
        response = bedrock.converse(
            modelId="anthropic.claude-3-haiku-20240307-v1:0",
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 1000}
        )
        
        return jsonify({
            'response': response['output']['message']['content'][0]['text'],
            'sources': sources
        })
    except Exception as e:
        return jsonify({'response': f"Error: {str(e)}"})

@app.route('/api/generate-report', methods=['POST'])
def generate_full_report():
    try:
        data = request.json
        bank_name = data['bankName']
        mode = data.get('mode', 'rag')
        analyzed_docs = data.get('analyzedDocs', [])
        
        # Override bank name for local uploads
        if mode == 'local' and analyzed_docs:
            bank_name = analyzed_docs[0].get('bank_name', 'Unknown Bank')
        
        def generate():
            try:
                yield f"data: {json.dumps({'status': 'Processing documents...', 'progress': 10})}\n\n"
                
                if mode == 'local':
                    yield f"data: {json.dumps({'status': 'Extracting content from uploaded documents...', 'progress': 30})}\n\n"
                    
                    # Get actual PDF content from S3
                    context_parts = []
                    for doc in analyzed_docs:
                        doc_id = doc.get('doc_id')
                        if doc_id:
                            try:
                                response = s3_client.get_object(Bucket=S3_BUCKET, Key=f"pdf-content/{doc_id}.txt")
                                content = response['Body'].read().decode('utf-8')
                                # Use first 8000 chars to stay within token limits
                                content_chunk = content[:8000] if len(content) > 8000 else content
                                context_parts.append(f"From {doc['bank_name']} {doc['form_type']} {doc['year']}:\n{content_chunk}")
                            except Exception as e:
                                print(f"Failed to retrieve content from S3: {e}")
                                context_parts.append(f"From {doc['bank_name']} {doc['form_type']} {doc['year']}:\nDocument content unavailable.")
                    
                    context = "\n\n".join(context_parts)
                    
                    yield f"data: {json.dumps({'status': 'Generating report from actual document content...', 'progress': 50})}\n\n"
                else:
                    # Search for comprehensive financial data
                    queries = [
                        f"financial performance revenue {bank_name}",
                        f"risk factors credit risk {bank_name}", 
                        f"capital adequacy tier 1 {bank_name}",
                        f"business segments operations {bank_name}",
                        f"regulatory compliance {bank_name}"
                    ]
                    
                    all_docs = []
                    for i, query in enumerate(queries):
                        docs = rag_system.search(query, bank_filter=bank_name, k=2)
                        all_docs.extend(docs)
                        progress = 20 + (i * 10)
                        yield f"data: {json.dumps({'status': f'Processing query {i+1}/5...', 'progress': progress})}\n\n"
                    
                    # Build comprehensive context
                    context = "\n\n".join([
                        f"From {doc['metadata']['filing_type']} {doc['metadata']['year']}:\n{doc['content'][:1200]}"
                        for doc in all_docs[:10]
                    ])
                
                yield f"data: {json.dumps({'status': 'Generating comprehensive report...', 'progress': 70})}\n\n"
                
                bedrock = boto3.client('bedrock-runtime')
                
                if mode == 'local':
                    prompt = f"""
Generate a comprehensive financial analysis report for {bank_name} based on the actual content from uploaded SEC financial documents.

Actual Document Content:
{context}

Create a detailed professional report with these sections:

1. EXECUTIVE SUMMARY
2. FINANCIAL PERFORMANCE ANALYSIS  
3. RISK ASSESSMENT & MANAGEMENT
4. CAPITAL ADEQUACY & LIQUIDITY
5. BUSINESS SEGMENTS & STRATEGY
6. REGULATORY ENVIRONMENT
7. INVESTMENT RECOMMENDATIONS & OUTLOOK

Use specific data, numbers, ratios, and quotes from the actual document content above. Focus on concrete financial metrics and performance indicators found in the documents.
"""
                else:
                    prompt = f"""
Generate a comprehensive, detailed financial analysis report for {bank_name} based on their actual SEC filings.

SEC Filing Data:
{context}

Create an extensive professional report (2-3 pages) with detailed analysis in these sections:

1. EXECUTIVE SUMMARY (300+ words)
2. FINANCIAL PERFORMANCE ANALYSIS (400+ words)
3. RISK ASSESSMENT & MANAGEMENT (350+ words)
4. CAPITAL ADEQUACY & LIQUIDITY (300+ words)
5. BUSINESS SEGMENTS & STRATEGY (300+ words)
6. REGULATORY ENVIRONMENT (250+ words)
7. INVESTMENT RECOMMENDATIONS & OUTLOOK (300+ words)

Provide detailed analysis with specific numbers, percentages, and direct quotes from the SEC filings.
"""
                
                yield f"data: {json.dumps({'status': 'AI analyzing filings...', 'progress': 80})}\n\n"
                
                response = bedrock.converse_stream(
                    modelId="anthropic.claude-3-sonnet-20240229-v1:0",
                    messages=[{"role": "user", "content": [{"text": prompt}]}],
                    inferenceConfig={"maxTokens": 4000}
                )
                
                full_report = ""
                for event in response['stream']:
                    if 'contentBlockDelta' in event:
                        chunk = event['contentBlockDelta']['delta']['text']
                        full_report += chunk
                        yield f"data: {json.dumps({'chunk': chunk, 'progress': 90})}\n\n"
                
                sources_count = len(all_docs) if mode != 'local' else len(analyzed_docs)
                yield f"data: {json.dumps({'status': 'Report complete!', 'progress': 100, 'complete': True, 'report': full_report, 'sources_used': sources_count})}\n\n"
                yield "data: [DONE]\n\n"  # Signal end of stream
                
            except Exception as e:
                yield f"data: {json.dumps({'error': f'Error: {str(e)}'})}\n\n"
                yield "data: [DONE]\n\n"  # Signal end of stream even on error
        
        return Response(generate(), mimetype='text/event-stream')
        
    except Exception as e:
        print(f"Report generation error: {e}")
        return jsonify({'error': f"Error generating report: {str(e)}"}), 500

@app.route('/api/analyze-local-data', methods=['POST'])
def analyze_local_data():
    try:
        data = request.json
        local_data = data['data']
        base_bank = data['baseBank']
        peer_banks = data['peerBanks']
        metric = data['metric']
        
        # Create data summary for AI
        data_summary = "\n".join([
            f"Bank: {row['Bank']}, Quarter: {row['Quarter']}, {metric}: {row['Value']:.2f}%"
            for row in local_data
        ])
        
        bedrock = boto3.client('bedrock-runtime')
        
        prompt = f"""
Analyze {base_bank} vs {', '.join(peer_banks)} for {metric} based on uploaded data.

Data:
{data_summary}

Provide analysis with:
• Performance comparison between base bank and peers
• Trends over time periods
• Key insights and observations
• Recommendations for improvement

Focus on actionable insights from this specific dataset.
"""
        
        response = bedrock.converse(
            modelId="anthropic.claude-3-haiku-20240307-v1:0",
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 1000}
        )
        
        return jsonify({
            'analysis': response['output']['message']['content'][0]['text']
        })
    except Exception as e:
        return jsonify({'analysis': f"Analysis based on uploaded data for {metric} - {str(e)}"})

@app.route('/api/search-banks', methods=['POST'])
def search_banks():
    try:
        data = request.json
        query = data['query']
        
        print(f"Searching for banks: {query}")
        results = bank_search.search_banks(query)
        print(f"Found {len(results)} banks")
        
        return jsonify(results)
    except Exception as e:
        print(f"Bank search error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/store-csv-data', methods=['POST'])
def store_csv_data():
    try:
        data = request.json
        csv_data = data['data']
        filename = data['filename']
        
        # Generate unique ID for CSV data
        import uuid
        csv_id = str(uuid.uuid4())
        
        # Store CSV data in S3
        try:
            s3_client.put_object(
                Bucket=S3_BUCKET,
                Key=f"csv-data/{csv_id}.json",
                Body=json.dumps(csv_data).encode('utf-8'),
                ContentType='application/json',
                Metadata={'filename': filename}
            )
            return jsonify({'csv_id': csv_id, 'status': 'stored'})
        except Exception as e:
            print(f"CSV S3 storage failed: {e}")
            return jsonify({'error': 'Storage failed'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8001)