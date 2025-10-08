from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import pandas as pd
import boto3
import json
from rag_system import rag_system
from sec_edgar_live import sec_api
from bank_search import bank_search
import PyPDF2
import io

app = Flask(__name__)
CORS(app)

# Initialize RAG system on startup
with app.app_context():
    print("Initializing RAG system...")
    try:
        rag_system.initialize()
        print("RAG system initialized successfully")
    except Exception as e:
        print(f"RAG initialization failed: {e}")

def get_banking_data():
    """Generate banking data"""
    banks = [
        "JPMORGAN CHASE BANK", "BANK OF AMERICA", "WELLS FARGO BANK", 
        "CITIBANK", "U.S. BANK", "PNC BANK", "GOLDMAN SACHS BANK",
        "TRUIST BANK", "CAPITAL ONE", "TD BANK"
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

@app.route('/api/fdic-data')
def get_fdic_data():
    try:
        data = get_banking_data()
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
            'metrics': metrics_data.to_dict('records')
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
                for page in pdf_reader.pages[:3]:  # Only first 3 pages for speed
                    text += page.extract_text()
                
                # Extract bank name, form type, year
                bank_name = 'Unknown Bank'
                form_type = '10-K' if '10-K' in text[:2000] else '10-Q' if '10-Q' in text[:2000] else 'Unknown'
                year = '2024'
                
                text_upper = text[:3000].upper()
                
                # Look for bank name patterns
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
                
                # Extract year
                import re
                years = re.findall(r'20(2[0-5])', text[:2000])
                if years:
                    year = '20' + years[0]
                
                analyzed_docs.append({
                    'filename': file.filename,
                    'bank_name': bank_name,
                    'form_type': form_type,
                    'year': year,
                    'size': len(file_data)
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
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
                text = ''
                for page in pdf_reader.pages:
                    text += page.extract_text()
                
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
        context = '\n\n'.join([f"From {doc['bank_name']} {doc['form_type']} {doc['year']}:\n{doc['content'][:1000]}..." for doc in documents])
        
        prompt = f"""Based on these uploaded financial documents:\n\n{context}\n\nAnswer: {message}"""
        
        response = bedrock.converse(
            modelId="anthropic.claude-3-haiku-20240307-v1:0",
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 1000}
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
                yield f"data: {json.dumps({'status': 'Searching SEC filings...', 'progress': 10})}\n\n"
                
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
                
                yield f"data: {json.dumps({'status': 'Generating comprehensive report...', 'progress': 70})}\n\n"
                
                # Build comprehensive context
                context = "\n\n".join([
                    f"From {doc['metadata']['filing_type']} {doc['metadata']['year']}:\n{doc['content'][:1200]}"
                    for doc in all_docs[:10]
                ])
                
                bedrock = boto3.client('bedrock-runtime')
                
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
                
                yield f"data: {json.dumps({'status': 'Report complete!', 'progress': 100, 'complete': True, 'report': full_report, 'sources_used': len(all_docs)})}\n\n"
                
            except Exception as e:
                yield f"data: {json.dumps({'error': f'Error: {str(e)}'})}\n\n"
        
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

if __name__ == '__main__':
    app.run(debug=True, port=8001)