#!/usr/bin/env python3
"""
Test the Lambda code locally to ensure it works with built-in libraries only
"""

import urllib.request
import urllib.error
import json
import time
import ssl

def test_lambda_logic():
    """Test the core Lambda logic"""
    
    # Test SEC API call
    cik = '19617'  # JPMorgan
    headers = {'User-Agent': 'BankIQ+ Research (contact@example.com)'}
    url = f'https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json'
    
    print("Testing SEC API call with urllib...")
    
    try:
        req = urllib.request.Request(url, headers=headers)
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=10, context=ctx) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        print("✅ SEC API call successful")
        
        # Test parsing
        recent = data.get('filings', {}).get('recent', {})
        forms = recent.get('form', [])
        dates = recent.get('filingDate', [])
        accessions = recent.get('accessionNumber', [])
        primary_docs = recent.get('primaryDocument', [])
        
        print(f"✅ Found {len(forms)} filings")
        
        # Test finding 10-K/10-Q
        found = False
        for i, (form, date, accession) in enumerate(zip(forms[:10], dates[:10], accessions[:10])):
            if form in ['10-K', '10-Q'] and date >= '2024-01-01':
                primary_doc = primary_docs[i] if i < len(primary_docs) else None
                print(f"✅ Found {form} from {date} with primary doc: {primary_doc}")
                
                # Test filing download
                accession_clean = accession.replace('-', '')
                filing_url = f'https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}/{primary_doc}' if primary_doc else f'https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}/{accession}.txt'
                
                try:
                    filing_req = urllib.request.Request(filing_url, headers=headers)
                    with urllib.request.urlopen(filing_req, timeout=15, context=ctx) as filing_response:
                        content = filing_response.read().decode('utf-8')
                        print(f"✅ Downloaded filing: {len(content)} chars")
                        found = True
                        break
                except Exception as e:
                    print(f"⚠️  Filing download failed: {e}")
                    continue
        
        if not found:
            print("❌ No downloadable filings found")
            return False
            
        print("✅ All Lambda logic tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Lambda test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_lambda_logic()
    if success:
        print("\n🎉 Lambda code is ready for deployment")
    else:
        print("\n💥 Lambda code needs fixes before deployment")