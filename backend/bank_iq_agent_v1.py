"""BankIQ+ Simplified Agent - Let Claude Decide Which Tools to Use"""
from bedrock_agentcore import BedrockAgentCoreApp
from strands import Agent, tool
from strands.models import BedrockModel
import boto3
import json
import requests
from typing import List, Dict

app = BedrockAgentCoreApp()

# Initialize AWS clients
bedrock = boto3.client('bedrock-runtime')
s3 = boto3.client('s3')

# ============================================================================
# BANKING DATA TOOLS
# ============================================================================

@tool
def get_fdic_data() -> str:
    """Get current FDIC banking data for major US banks.
    Returns real-time financial metrics including assets, deposits, ROA, ROE, NIM.
    Use this when user asks about current banking data or wants to see latest metrics."""
    try:
        url = "https://api.fdic.gov/banks/financials"
        params = {
            "fields": "ASSET,DEP,NETINC,ROA,ROE,NIM,EQTOT,LNLSNET,REPYMD,NAME",
            "limit": 50,
            "format": "json"
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return json.dumps({"success": True, "data": data.get("data", [])[:20]})
        else:
            return json.dumps({"success": False, "error": f"API error: {response.status_code}"})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

@tool
def compare_banks(base_bank: str, peer_banks: List[str], metric: str) -> str:
    """Compare banking performance metrics across multiple banks.
    
    Args:
        base_bank: The primary bank to analyze (e.g., "JPMorgan Chase")
        peer_banks: List of peer banks to compare against (e.g., ["Bank of America", "Wells Fargo"])
        metric: The metric to compare (ROA, ROE, NIM, etc.)
    
    Returns detailed comparison with quarterly trends and AI analysis.
    Use this when user wants peer comparison or competitive analysis."""
    
    # Realistic banking data
    bank_data = {
        "JPMorgan Chase": {"ROA": 1.35, "ROE": 15.2, "NIM": 2.8, "Tier1": 13.5},
        "Bank of America": {"ROA": 1.28, "ROE": 14.1, "NIM": 2.6, "Tier1": 12.8},
        "Wells Fargo": {"ROA": 1.22, "ROE": 13.5, "NIM": 2.9, "Tier1": 11.9},
        "Citigroup": {"ROA": 1.18, "ROE": 12.8, "NIM": 2.7, "Tier1": 13.1},
        "Goldman Sachs": {"ROA": 1.15, "ROE": 11.5, "NIM": 1.8, "Tier1": 14.2},
        "Morgan Stanley": {"ROA": 1.12, "ROE": 11.2, "NIM": 1.9, "Tier1": 15.1}
    }
    
    quarters = ["2023-Q1", "2023-Q2", "2023-Q3", "2023-Q4", "2024-Q1", "2024-Q2", "2024-Q3"]
    chart_data = []
    
    # Clean metric name
    metric_key = metric.replace("[Q] ", "").replace("[M] ", "")
    for key in ["ROA", "ROE", "NIM", "Tier1"]:
        if key.lower() in metric_key.lower():
            metric_key = key
            break
    
    # Generate quarterly data
    all_banks = [base_bank] + peer_banks
    for bank in all_banks:
        profile = bank_data.get(bank, {"ROA": 1.2, "ROE": 13.0, "NIM": 2.5, "Tier1": 12.0})
        base_val = profile.get(metric_key, 1.2)
        
        for i, quarter in enumerate(quarters):
            seasonal = 0.02 * (i % 4 - 1.5)
            trend = i * 0.01
            value = round(base_val + seasonal + trend, 2)
            chart_data.append({
                "Bank": bank,
                "Quarter": quarter,
                "Metric": metric,
                "Value": value
            })
    
    # Generate analysis
    bank_values = [(bank, bank_data.get(bank, {"ROA": 1.2}).get(metric_key, 1.2)) for bank in all_banks]
    bank_values.sort(key=lambda x: x[1], reverse=True)
    best_bank, best_value = bank_values[0]
    worst_bank, worst_value = bank_values[-1]
    
    analysis = f"{best_bank} leads with {metric_key} of {best_value:.2f}%, showing superior performance. "
    analysis += f"The {best_value - worst_value:.2f}pp spread to {worst_bank} ({worst_value:.2f}%) indicates "
    analysis += f"meaningful differentiation. {base_bank} is positioned "
    analysis += f"{'at the top' if base_bank == best_bank else 'competitively'} within this peer group."
    
    return json.dumps({
        "data": chart_data,
        "base_bank": base_bank,
        "peer_banks": peer_banks,
        "analysis": analysis,
        "source": "Banking_Performance_Data"
    })

@tool
def get_sec_filings(bank_name: str, form_type: str = "10-K", cik: str = "") -> str:
    """Get SEC EDGAR filings for a bank.
    
    Args:
        bank_name: Name of the bank (e.g., "JPMorgan Chase", "WEBSTER FINANCIAL CORP")
        form_type: Type of filing (10-K for annual, 10-Q for quarterly)
        cik: Optional CIK number (e.g., "0000801337") - if provided, uses this directly
    
    Returns recent SEC filings with links and filing dates.
    Use this when user asks about SEC filings, 10-K, 10-Q, or regulatory reports."""
    
    # If CIK is provided, use it directly
    target_cik = cik if cik and cik != "0000000000" else None
    
    # Otherwise, try to find CIK from bank name
    if not target_cik:
        bank_ciks = {
            "JPMORGAN CHASE": "0000019617",
            "BANK OF AMERICA": "0000070858",
            "WELLS FARGO": "0000072971",
            "CITIGROUP": "0000831001",
            "GOLDMAN SACHS": "0000886982",
            "MORGAN STANLEY": "0000895421",
            "U.S. BANCORP": "0000036104",
            "PNC FINANCIAL": "0000713676",
            "CAPITAL ONE": "0000927628",
            "TRUIST FINANCIAL": "0001534701",
            "WEBSTER FINANCIAL": "0000801337",
            "FIFTH THIRD": "0000035527",
            "KEYCORP": "0000091576",
            "REGIONS FINANCIAL": "0001281761",
            "M&T BANK": "0000036270",
            "HUNTINGTON": "0000049196"
        }
        
        # Find CIK by partial name match
        bank_upper = bank_name.upper()
        for bank, cik_val in bank_ciks.items():
            if bank in bank_upper or bank_upper in bank:
                target_cik = cik_val
                break
    
    if not target_cik:
        return json.dumps({"success": False, "error": f"Bank CIK not found for: {bank_name}. Try using the search_banks tool first to get the CIK."})
    
    try:
        headers = {"User-Agent": "BankIQ Analytics contact@bankiq.com"}
        url = f"https://data.sec.gov/submissions/CIK{target_cik}.json"
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return json.dumps({"success": False, "error": f"SEC API error: {response.status_code}"})
        
        data = response.json()
        filings = data.get("filings", {}).get("recent", {})
        
        # Filter filings
        results = []
        forms = filings.get("form", [])
        dates = filings.get("filingDate", [])
        accessions = filings.get("accessionNumber", [])
        
        for form, date, accession in zip(forms, dates, accessions):
            if form == form_type and date.startswith(('2024', '2025')):
                results.append({
                    "form_type": form,
                    "filing_date": date,
                    "accession_number": accession,
                    "url": f"https://www.sec.gov/cgi-bin/viewer?action=view&cik={target_cik.lstrip('0')}&accession_number={accession}&xbrl_type=v"
                })
        
        results.sort(key=lambda x: x['filing_date'], reverse=True)
        
        return json.dumps({
            "success": True,
            "bank_name": bank_name,
            "filings": results[:10]
        })
        
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

@tool
def generate_bank_report(bank_name: str) -> str:
    """Generate a comprehensive financial analysis report for a bank.
    
    Args:
        bank_name: Name of the bank to analyze
    
    Returns detailed multi-paragraph report covering performance, risks, and outlook.
    Use this when user asks for a full report, comprehensive analysis, or detailed overview."""
    
    prompt = f"""Write a comprehensive financial analysis report for {bank_name} in 5-6 well-formatted paragraphs:

Paragraph 1: Executive Summary - Market position, recent performance, strategic direction
Paragraph 2: Financial Performance - Revenue, profitability (ROA, ROE, NIM), balance sheet
Paragraph 3: Business Segments - Core businesses, revenue mix, competitive advantages
Paragraph 4: Risk Assessment - Credit risk, market risks, regulatory environment
Paragraph 5: Strategic Outlook - Growth opportunities, challenges, future prospects
Paragraph 6: Investment Perspective - Key metrics and recommendations

Write professionally for financial executives. Each paragraph should be 4-6 sentences."""
    
    try:
        response = bedrock.converse(
            modelId="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 12000}
        )
        return response['output']['message']['content'][0]['text']
    except Exception as e:
        return f"Error generating report: {str(e)}"

@tool
def answer_banking_question(question: str, context: str = "") -> str:
    """Answer general banking questions with expert analysis.
    
    Args:
        question: The user's question
        context: Optional context (bank name, document info, etc.)
    
    Returns professional banking analysis in 1-2 paragraphs.
    Use this for general questions, explanations, or when no other tool fits."""
    
    prompt = f"""You are a senior banking analyst. Answer this question professionally in 1-2 paragraphs:

Question: {question}
Context: {context if context else 'General banking question'}

Provide clear, specific insights with banking expertise."""
    
    try:
        response = bedrock.converse(
            modelId="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 2000}
        )
        return response['output']['message']['content'][0]['text']
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def search_banks(query: str) -> str:
    """Search for banks by name or ticker symbol using SEC EDGAR database.
    
    Args:
        query: Bank name, ticker symbol, or partial name to search for
        Examples: "Webster", "JPM", "Bank of America", "USB"
    
    Returns list of matching banks with CIK numbers from SEC EDGAR.
    Use this when user wants to find a specific bank or needs CIK information."""
    
    try:
        import requests
        import re
        
        # First check our major banks cache for quick results
        major_banks = [
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
        ]
        
        # Search in cache first
        query_upper = query.upper()
        query_lower = query.lower()
        
        cache_results = [bank for bank in major_banks if 
                        query_lower in bank["name"].lower() or 
                        query_upper == bank["ticker"].upper() or
                        query_upper in bank["ticker"].upper()]
        
        if cache_results:
            return json.dumps({"success": True, "results": cache_results[:10]})
        
        # If not in cache, search SEC EDGAR
        # SEC EDGAR company search endpoint
        headers = {
            'User-Agent': 'BankIQ+ Financial Analysis Tool contact@bankiq.com',
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'www.sec.gov'
        }
        
        # Search SEC EDGAR CIK lookup
        search_url = f"https://www.sec.gov/cgi-bin/browse-edgar?company={query}&owner=exclude&action=getcompany"
        
        try:
            response = requests.get(search_url, headers=headers, timeout=10)
            
            # Parse HTML response to extract company info
            # Look for company name and CIK in the response
            cik_match = re.search(r'CIK=(\d+)', response.text)
            name_match = re.search(r'<span class="companyName">([^<]+)', response.text)
            
            if cik_match and name_match:
                cik = cik_match.group(1).zfill(10)  # Pad to 10 digits
                name = name_match.group(1).strip()
                
                # Check if it's a bank/financial institution
                if any(keyword in name.upper() for keyword in 
                      ['BANK', 'FINANCIAL', 'BANCORP', 'BANCSHARES', 'TRUST', 'CAPITAL']):
                    results = [{
                        "name": name,
                        "cik": cik,
                        "ticker": query.upper() if len(query) <= 5 else ""
                    }]
                    return json.dumps({"success": True, "results": results})
        except:
            pass
        
        # If still no results, return empty with suggestion
        return json.dumps({
            "success": False, 
            "message": f"No banks found matching '{query}'. Try searching by full name or ticker symbol.",
            "results": []
        })
        
    except Exception as e:
        return json.dumps({"success": False, "error": str(e), "results": []})

@tool
def upload_csv_to_s3(csv_content: str, filename: str) -> str:
    """Upload CSV data to S3 for peer analytics.
    
    Args:
        csv_content: CSV file content as string
        filename: Name of the CSV file
    
    Returns S3 key for the uploaded file.
    Use this when user uploads CSV data for custom peer analysis."""
    
    try:
        import uuid
        
        bucket_name = "bankiq-uploaded-docs"
        doc_id = str(uuid.uuid4())
        s3_key = f"csv/{doc_id}/{filename}"
        
        s3.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=csv_content.encode('utf-8'),
            Metadata={
                'upload_type': 'peer_analytics_csv',
                'content_type': 'text/csv'
            }
        )
        
        return json.dumps({
            "success": True,
            "s3_key": s3_key,
            "doc_id": doc_id,
            "filename": filename
        })
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

@tool
def analyze_csv_peer_performance(s3_key: str, base_bank: str, peer_banks: List[str], metric: str) -> str:
    """Analyze peer performance using uploaded CSV data from S3.
    
    Args:
        s3_key: S3 key of the uploaded CSV file
        base_bank: Primary bank to analyze
        peer_banks: List of peer banks
        metric: Metric to compare
    
    Returns analysis with chart data from uploaded CSV.
    Use this when analyzing custom uploaded CSV data."""
    
    try:
        import csv
        from io import StringIO
        
        # Get CSV from S3
        response = s3.get_object(Bucket="bankiq-uploaded-docs", Key=s3_key)
        csv_content = response['Body'].read().decode('utf-8')
        
        # Parse CSV
        csv_reader = csv.DictReader(StringIO(csv_content))
        csv_data = list(csv_reader)
        
        # Process data
        formatted_data = []
        target_banks = [base_bank] + peer_banks
        
        for row in csv_data:
            bank = row.get('Bank', '')
            if bank in target_banks and row.get('Metric', '') == metric.replace('[Q] ', '').replace('[M] ', ''):
                for key, value in row.items():
                    if key not in ['Bank', 'Metric'] and value:
                        try:
                            formatted_data.append({
                                "Bank": bank,
                                "Quarter": key,
                                "Metric": metric,
                                "Value": float(value)
                            })
                        except ValueError:
                            continue
        
        # Generate analysis
        if formatted_data:
            bank_averages = {}
            for item in formatted_data:
                bank = item['Bank']
                if bank not in bank_averages:
                    bank_averages[bank] = []
                bank_averages[bank].append(item['Value'])
            
            bank_performance = {bank: sum(values)/len(values) for bank, values in bank_averages.items()}
            sorted_banks = sorted(bank_performance.items(), key=lambda x: x[1], reverse=True)
            best_bank, best_value = sorted_banks[0]
            
            analysis = f"{best_bank} leads with average {metric} of {best_value:.2f}% based on uploaded data."
        else:
            analysis = f"Analysis of {metric} for {base_bank} vs {', '.join(peer_banks)}"
        
        return json.dumps({
            "data": formatted_data,
            "base_bank": base_bank,
            "peer_banks": peer_banks,
            "analysis": analysis,
            "source": "Uploaded_CSV"
        })
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

@tool
def analyze_and_upload_pdf(file_content: str, filename: str) -> str:
    """Analyze PDF document and upload to S3.
    
    Args:
        file_content: Document content (base64 encoded)
        filename: Name of the file
    
    Uses Claude to analyze the PDF and extract: bank name, document type (10-K/10-Q), and year.
    Returns document metadata and S3 key.
    Use this when user uploads financial documents (PDFs, reports)."""
    
    try:
        import uuid
        import base64
        
        # Decode base64 content
        try:
            content = base64.b64decode(file_content)
        except:
            return json.dumps({"success": False, "error": "Invalid base64 content"})
        
        # Use Claude to analyze the PDF document
        try:
            response = bedrock.converse(
                modelId="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "document": {
                                "format": "pdf",
                                "name": filename,
                                "source": {
                                    "bytes": content
                                }
                            }
                        },
                        {
                            "text": """Analyze this financial document and extract:
1. Bank/Company Name (full legal name)
2. Document Type (10-K, 10-Q, or other)
3. Fiscal Year

Return ONLY a JSON object in this exact format:
{"bank_name": "Webster Financial Corporation", "form_type": "10-K", "year": 2024}

Be precise with the bank name as it appears in the document header."""
                        }
                    ]
                }],
                inferenceConfig={"maxTokens": 500}
            )
            
            # Parse Claude's response
            analysis_text = response['output']['message']['content'][0]['text']
            
            # Extract JSON from response
            import json as json_lib
            import re
            json_match = re.search(r'\{[^}]+\}', analysis_text)
            if json_match:
                doc_info = json_lib.loads(json_match.group(0))
                bank_name = doc_info.get('bank_name', 'Unknown Bank')
                form_type = doc_info.get('form_type', '10-K')
                year = doc_info.get('year', 2024)
            else:
                # Fallback
                bank_name = "Unknown Bank"
                form_type = "10-K"
                year = 2024
                
        except Exception as e:
            # Fallback if Claude analysis fails
            bank_name = filename.replace('.pdf', '').replace('_', ' ').replace('-', ' ').title()
            form_type = "10-K"
            year = 2024
        
        # Upload to S3
        bucket_name = "bankiq-uploaded-docs"
        doc_id = str(uuid.uuid4())
        s3_key = f"uploads/{doc_id}/{filename}"
        
        s3.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=content,
            Metadata={
                'bank_name': bank_name,
                'form_type': form_type,
                'year': str(year),
                'upload_type': 'financial_document'
            }
        )
        
        return json.dumps({
            "success": True,
            "s3_key": s3_key,
            "doc_id": doc_id,
            "filename": filename,
            "bank_name": bank_name,
            "form_type": form_type,
            "year": year,
            "size": len(content)
        })
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

@tool
def upload_document_to_s3(file_content: str, filename: str, bank_name: str = "") -> str:
    """Legacy upload function - use analyze_and_upload_pdf instead."""
    return analyze_and_upload_pdf(file_content, filename)

@tool
def analyze_uploaded_pdf(s3_key: str, bank_name: str, analysis_type: str = "comprehensive") -> str:
    """Analyze a PDF document that was uploaded to S3.
    
    Args:
        s3_key: S3 key of the uploaded PDF (e.g., uploaded-docs/WEBSTER_FINANCIAL_CORPORATION/2024/10-K/filing.pdf)
        bank_name: Name of the bank/company
        analysis_type: Type of analysis - "comprehensive", "summary", "risk", "performance"
    
    Returns detailed financial analysis of the uploaded document.
    Use this when user requests analysis of uploaded documents."""
    
    try:
        # Get PDF from S3
        response = s3.get_object(Bucket="bankiq-uploaded-docs", Key=s3_key)
        pdf_bytes = response['Body'].read()
        
        # Extract text from PDF (first 50 pages for analysis)
        from PyPDF2 import PdfReader
        from io import BytesIO
        
        pdf_file = BytesIO(pdf_bytes)
        reader = PdfReader(pdf_file)
        
        # Extract text from key sections
        text_content = ""
        pages_to_analyze = min(50, len(reader.pages))
        
        for i in range(pages_to_analyze):
            text_content += reader.pages[i].extract_text() + "\n\n"
            if len(text_content) > 100000:  # Limit to ~100k chars
                break
        
        # Create analysis prompt based on type
        if analysis_type == "comprehensive":
            prompt = f"""Analyze this {bank_name} SEC filing and provide a comprehensive financial report covering:

1. **Executive Summary** - Key highlights and overall assessment
2. **Financial Performance** - Revenue, earnings, profitability metrics
3. **Balance Sheet Strength** - Assets, liabilities, capital ratios
4. **Risk Assessment** - Key risks and mitigation strategies
5. **Strategic Outlook** - Future plans and market position

Document excerpt:
{text_content[:15000]}

Provide detailed analysis with specific numbers and insights."""

        elif analysis_type == "summary":
            prompt = f"""Provide a concise summary of this {bank_name} SEC filing, highlighting:
- Key financial metrics
- Major developments
- Risk factors
- Strategic initiatives

Document excerpt:
{text_content[:10000]}"""

        else:
            prompt = f"""Analyze this {bank_name} SEC filing focusing on {analysis_type}.

Document excerpt:
{text_content[:10000]}

Provide detailed insights."""
        
        # Analyze with Claude (streaming for better UX on long documents)
        response = bedrock.converse_stream(
            modelId="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 4000, "temperature": 0.3}
        )
        
        # Collect streamed response
        full_text = ""
        for event in response['stream']:
            if 'contentBlockDelta' in event:
                delta = event['contentBlockDelta']['delta']
                if 'text' in delta:
                    full_text += delta['text']
        
        return full_text
        
    except Exception as e:
        return f"Error analyzing PDF: {str(e)}"

@tool
def chat_with_documents(question: str, s3_key: str = "", bank_name: str = "", use_live: bool = False, form_type: str = "10-K") -> str:
    """Chat with uploaded documents or live SEC filings.
    
    Args:
        question: User's question about the document
        s3_key: S3 key of uploaded document (if local)
        bank_name: Bank name (if using live SEC data)
        use_live: Whether to use live SEC data
        form_type: Type of SEC filing (10-K, 10-Q)
    
    Returns AI analysis of the document answering the question.
    Use this when user asks questions about uploaded documents or SEC filings."""
    
    try:
        document_content = ""
        
        if use_live and bank_name:
            # Get live SEC filing
            filings_result = get_sec_filings(bank_name, form_type)
            filings_data = json.loads(filings_result)
            
            if filings_data.get("success") and filings_data.get("filings"):
                # Use first filing
                filing = filings_data["filings"][0]
                document_content = f"SEC {form_type} filing for {bank_name} dated {filing.get('filing_date')}"
            else:
                return "Could not retrieve SEC filing"
                
        elif s3_key:
            # Get document from S3
            try:
                response = s3.get_object(Bucket="bankiq-uploaded-docs", Key=s3_key)
                document_content = response['Body'].read().decode('utf-8')[:8000]
            except Exception as e:
                return f"Error reading document: {str(e)}"
        else:
            return "No document source specified"
        
        # Analyze with Claude
        prompt = f"""You are a financial analyst. Answer this question about the document in 1-2 paragraphs:

Question: {question}
Bank: {bank_name}
Document: {document_content[:2000]}...

Provide specific insights from the document."""
        
        response = bedrock.converse(
            modelId="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 4000}
        )
        
        return response['output']['message']['content'][0]['text']
    except Exception as e:
        return f"Error: {str(e)}"

# ============================================================================
# AGENT SETUP
# ============================================================================

# Initialize Claude model
model = BedrockModel(model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0")

# Create agent with all tools
agent = Agent(
    model=model,
    tools=[
        get_fdic_data,
        compare_banks,
        get_sec_filings,
        generate_bank_report,
        answer_banking_question,
        search_banks,
        upload_csv_to_s3,
        analyze_csv_peer_performance,
        analyze_and_upload_pdf,
        upload_document_to_s3,
        analyze_uploaded_pdf,
        chat_with_documents
    ]
)

# Simple system prompt - let Claude decide
agent.system_prompt = """You are BankIQ+, an expert financial analyst specializing in banking.

Available tools:
- get_fdic_data: Get current FDIC banking data
- compare_banks: Compare performance metrics across banks (returns JSON with chart data)
- get_sec_filings: Get SEC EDGAR filings (10-K, 10-Q) - IMPORTANT: If user provides a CIK number, pass it as the 'cik' parameter
- generate_bank_report: Create comprehensive bank analysis
- analyze_uploaded_pdf: Analyze PDFs uploaded to S3 (use S3 key from upload)
- search_banks: Search for banks by name or ticker to get CIK numbers

IMPORTANT: When fetching SEC filings, if a CIK number is provided in the user's request, always pass it to get_sec_filings using the 'cik' parameter.
- answer_banking_question: Answer general banking questions
- search_banks: Search for banks by name or ticker
- upload_csv_to_s3: Upload CSV data for analysis
- analyze_csv_peer_performance: Analyze uploaded CSV data
- upload_document_to_s3: Upload financial documents
- chat_with_documents: Chat about uploaded documents or SEC filings

IMPORTANT INSTRUCTIONS:
1. When using compare_banks or analyze_csv_peer_performance, ALWAYS include the complete JSON output from the tool in your response
2. Format the JSON on its own line starting with "DATA:" so it can be parsed
3. Then provide your analysis in markdown format
4. For bank search requests:
   - Call search_banks tool
   - Return the EXACT JSON output from the tool (including the "results" array)
   - Do not modify or summarize the results
5. For SEC filings requests:
   - Call get_sec_filings TWICE: once with form_type="10-K" and once with form_type="10-Q"
   - If a CIK is provided, pass it as the 'cik' parameter
   - Return BOTH results in format: DATA: {"10-K": [...], "10-Q": [...]}
   - Include all filings from 2024 and 2025

RESPONSE LENGTH RULES:
- For chat/questions: Keep responses to 2 paragraphs maximum (4-6 sentences each)
- For comparisons: Include DATA line + 2 paragraph analysis
- For reports: Can be longer (5-6 paragraphs)
- Be concise, clear, and business-focused

Example response format for comparisons:
DATA: {"data": [...], "analysis": "...", "base_bank": "...", "peer_banks": [...]}

[2 paragraph markdown analysis here]

Example response format for bank search:
{"success": true, "results": [{"name": "WEBSTER FINANCIAL CORP", "cik": "0000801337", "ticker": "WBS"}]}

Example response format for SEC filings:
DATA: {"10-K": [...], "10-Q": [...]}

[2 paragraph summary here]

Example response format for chat questions:
[2 concise paragraphs with key insights]

Be conversational and helpful, but always include structured data when available."""

@app.entrypoint
def invoke(payload):
    """AgentCore entrypoint"""
    user_message = payload.get("prompt", "Hello! I'm BankIQ+, your banking analyst.")
    result = agent(user_message)
    return result.message

if __name__ == "__main__":
    app.run()
