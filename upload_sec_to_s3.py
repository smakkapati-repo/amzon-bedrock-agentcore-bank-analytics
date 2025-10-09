#!/usr/bin/env python3
"""
Upload SEC filings to S3 bucket as backup for RAG system
Run this after CloudFormation deployment to populate S3 with raw data
"""

import boto3
import requests
import time
import json
from pathlib import Path

# Major banks and their CIKs
BANKS = {
    'JPMORGAN_CHASE': '19617',
    'BANK_OF_AMERICA': '70858', 
    'WELLS_FARGO': '72971',
    'CITIGROUP': '831001',
    'GOLDMAN_SACHS': '886982',
    'MORGAN_STANLEY': '895421',
    'US_BANCORP': '36104',
    'PNC_FINANCIAL': '713676',
    'CAPITAL_ONE': '927628',
    'TRUIST': '92230'
}

def get_company_filings(cik, year, form_type, limit=2):
    """Get recent filings for a company"""
    url = f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json"
    headers = {'User-Agent': 'BankIQ+ Research (contact@example.com)'}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        filings = []
        recent_filings = data.get('filings', {}).get('recent', {})
        
        forms = recent_filings.get('form', [])
        dates = recent_filings.get('filingDate', [])
        accessions = recent_filings.get('accessionNumber', [])
        
        for form, date, accession in zip(forms, dates, accessions):
            if form == form_type and date.startswith(year):
                filings.append({
                    'form': form,
                    'date': date,
                    'accession': accession,
                    'cik': cik
                })
                if len(filings) >= limit:
                    break
                    
        return filings
        
    except Exception as e:
        print(f"Error fetching {form_type} for CIK {cik} ({year}): {e}")
        return []

def download_filing_content(cik, accession):
    """Download filing content from SEC"""
    # Try multiple URL patterns
    accession_clean = accession.replace('-', '')
    urls = [
        f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}/{accession}.txt",
        f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}/primary-document.html"
    ]
    
    headers = {'User-Agent': 'BankIQ+ Research (contact@example.com)'}
    
    for url in urls:
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.text
        except:
            continue
    
    return None

def upload_to_s3(bucket_name):
    """Upload SEC filings to S3"""
    s3 = boto3.client('s3')
    
    total_uploaded = 0
    total_size = 0
    
    print(f"Uploading SEC filings to S3 bucket: {bucket_name}")
    
    for bank_name, cik in BANKS.items():
        print(f"\nProcessing {bank_name} (CIK: {cik})")
        
        for year in ['2023', '2024', '2025']:
            for form_type in ['10-K', '10-Q']:
                print(f"  Fetching {form_type} filings for {year}...")
                
                filings = get_company_filings(cik, year, form_type, limit=2)
                
                for filing in filings:
                    s3_key = f"{bank_name}/{year}/{form_type}/{filing['accession']}.txt"
                    
                    # Check if already exists
                    try:\n                        s3.head_object(Bucket=bucket_name, Key=s3_key)\n                        print(f\"    Skipping {s3_key} (already exists)\")\n                        continue\n                    except:\n                        pass\n                    \n                    print(f\"    Downloading {filing['accession']}...\")\n                    content = download_filing_content(cik, filing['accession'])\n                    \n                    if content:\n                        # Upload to S3\n                        try:\n                            s3.put_object(\n                                Bucket=bucket_name,\n                                Key=s3_key,\n                                Body=content.encode('utf-8'),\n                                ContentType='text/plain',\n                                Metadata={\n                                    'bank': bank_name,\n                                    'cik': cik,\n                                    'form': form_type,\n                                    'year': year,\n                                    'filing_date': filing['date']\n                                }\n                            )\n                            \n                            size = len(content.encode('utf-8'))\n                            total_uploaded += 1\n                            total_size += size\n                            \n                            print(f\"    ✓ Uploaded {s3_key} ({size:,} bytes)\")\n                            \n                        except Exception as e:\n                            print(f\"    ✗ Failed to upload {s3_key}: {e}\")\n                    else:\n                        print(f\"    ✗ Failed to download {filing['accession']}\")\n                    \n                    # SEC rate limiting\n                    time.sleep(0.1)\n    \n    # Summary\n    size_mb = total_size / (1024 * 1024)\n    print(f\"\\n{'='*60}\")\n    print(f\"UPLOAD COMPLETE\")\n    print(f\"{'='*60}\")\n    print(f\"Files uploaded: {total_uploaded}\")\n    print(f\"Total size: {total_size:,} bytes ({size_mb:.1f} MB)\")\n    print(f\"S3 bucket: {bucket_name}\")\n    print(f\"Monthly cost: ~${(size_mb * 0.023):.2f} (S3 Standard)\")\n\ndef main():\n    import sys\n    \n    if len(sys.argv) != 2:\n        print(\"Usage: python3 upload_sec_to_s3.py <bucket-name>\")\n        print(\"Get bucket name from CloudFormation outputs\")\n        sys.exit(1)\n    \n    bucket_name = sys.argv[1]\n    upload_to_s3(bucket_name)\n\nif __name__ == \"__main__\":\n    main()