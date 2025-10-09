#!/usr/bin/env python3
"""
Final SEC uploader with complete historical data access
"""

import boto3
import requests
import time
import json

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

def get_all_filings(cik, target_years=['2023', '2024', '2025']):
    """Get all filings including historical data"""
    headers = {'User-Agent': 'BankIQ+ Research (contact@example.com)'}
    
    url = f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json"
    response = requests.get(url, headers=headers, timeout=10)
    
    if response.status_code != 200:
        return []
    
    data = response.json()
    filings_data = data.get('filings', {})
    all_filings = []
    
    # Process recent filings
    recent = filings_data.get('recent', {})
    forms = recent.get('form', [])
    dates = recent.get('filingDate', [])
    accessions = recent.get('accessionNumber', [])
    primary_docs = recent.get('primaryDocument', [])
    
    for i, (form, date, accession) in enumerate(zip(forms, dates, accessions)):
        if form in ['10-K', '10-Q'] and any(date.startswith(year) for year in target_years):
            primary_doc = primary_docs[i] if i < len(primary_docs) else None
            all_filings.append({
                'form': form,
                'date': date,
                'accession': accession,
                'primary_doc': primary_doc
            })
    
    # Process historical files
    historical_files = filings_data.get('files', [])
    
    for file_info in historical_files:
        file_url = f"https://data.sec.gov/submissions/{file_info['name']}"
        
        try:
            hist_response = requests.get(file_url, headers=headers, timeout=10)
            if hist_response.status_code == 200:
                hist_data = hist_response.json()
                
                hist_forms = hist_data.get('form', [])
                hist_dates = hist_data.get('filingDate', [])
                hist_accessions = hist_data.get('accessionNumber', [])
                hist_primary_docs = hist_data.get('primaryDocument', [])
                
                for i, (form, date, accession) in enumerate(zip(hist_forms, hist_dates, hist_accessions)):
                    if form in ['10-K', '10-Q'] and any(date.startswith(year) for year in target_years):
                        primary_doc = hist_primary_docs[i] if i < len(hist_primary_docs) else None
                        all_filings.append({
                            'form': form,
                            'date': date,
                            'accession': accession,
                            'primary_doc': primary_doc
                        })
            
            time.sleep(0.1)
            
        except Exception as e:
            continue
    
    return all_filings

def download_filing_content(cik, accession, primary_doc=None):
    """Download filing content from SEC"""
    accession_clean = accession.replace('-', '')
    
    urls = []
    if primary_doc:
        urls.append(f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}/{primary_doc}")
    
    urls.extend([
        f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}/{accession}.txt",
        f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}/index.html"
    ])
    
    headers = {'User-Agent': 'BankIQ+ Research (contact@example.com)'}
    
    for url in urls:
        try:
            response = requests.get(url, headers=headers, timeout=15)
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
        
        filings = get_all_filings(cik)
        print(f"  Found {len(filings)} filings")
        
        for filing in filings:
            s3_key = f"{bank_name}/{filing['date'][:4]}/{filing['form']}/{filing['accession']}.txt"
            
            # Check if already exists
            try:
                s3.head_object(Bucket=bucket_name, Key=s3_key)
                print(f"    Skipping {s3_key} (exists)")
                continue
            except:
                pass
            
            print(f"    Downloading {filing['accession']}...")
            content = download_filing_content(cik, filing['accession'], filing.get('primary_doc'))
            
            if content:
                try:
                    s3.put_object(
                        Bucket=bucket_name,
                        Key=s3_key,
                        Body=content.encode('utf-8'),
                        ContentType='text/plain',
                        Metadata={
                            'bank': bank_name,
                            'cik': cik,
                            'form': filing['form'],
                            'year': filing['date'][:4],
                            'filing_date': filing['date']
                        }
                    )
                    
                    size = len(content.encode('utf-8'))
                    total_uploaded += 1
                    total_size += size
                    
                    print(f"    ✓ Uploaded {s3_key} ({size/1024/1024:.1f} MB)")
                    
                except Exception as e:
                    print(f"    ✗ Upload failed: {e}")
            else:
                print(f"    ✗ Download failed")
            
            time.sleep(0.1)
        
        time.sleep(0.3)
    
    size_mb = total_size / (1024 * 1024)
    print(f"\n{'='*60}")
    print(f"UPLOAD COMPLETE")
    print(f"{'='*60}")
    print(f"Files uploaded: {total_uploaded}")
    print(f"Total size: {size_mb:.0f} MB ({size_mb/1024:.1f} GB)")
    print(f"S3 bucket: {bucket_name}")
    print(f"Monthly cost: ~${(size_mb/1024 * 23):.2f}")

def main():
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python3 upload_sec_to_s3_final.py <bucket-name>")
        sys.exit(1)
    
    bucket_name = sys.argv[1]
    upload_to_s3(bucket_name)

if __name__ == "__main__":
    main()