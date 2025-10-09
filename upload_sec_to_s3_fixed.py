#!/usr/bin/env python3
"""
Fixed SEC uploader with proper URL patterns and error handling
"""

import boto3
import requests
import time
import json

# Test with fewer banks first
BANKS = {
    'JPMORGAN_CHASE': '19617',
    'BANK_OF_AMERICA': '70858', 
    'WELLS_FARGO': '72971'
}

def get_company_filings(cik, year, form_type, limit=1):
    """Get recent filings for a company"""
    url = f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json"
    headers = {'User-Agent': 'BankIQ+ Research (contact@example.com)'}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        filings = []
        recent_filings = data.get('filings', {}).get('recent', {})
        
        forms = recent_filings.get('form', [])
        dates = recent_filings.get('filingDate', [])
        accessions = recent_filings.get('accessionNumber', [])
        primary_docs = recent_filings.get('primaryDocument', [])
        
        for i, (form, date, accession) in enumerate(zip(forms, dates, accessions)):
            if form == form_type and date.startswith(year):
                primary_doc = primary_docs[i] if i < len(primary_docs) else None
                filings.append({
                    'form': form,
                    'date': date,
                    'accession': accession,
                    'primary_doc': primary_doc,
                    'cik': cik
                })
                if len(filings) >= limit:
                    break
                    
        return filings
        
    except Exception as e:
        print(f"Error fetching {form_type} for CIK {cik} ({year}): {e}")
        return []

def download_filing_content(cik, accession, primary_doc=None):
    """Download filing content from SEC"""
    accession_clean = accession.replace('-', '')
    
    # Try primary document first (most reliable)
    urls = []
    if primary_doc:
        urls.append(f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}/{primary_doc}")
    
    # Fallback URLs
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
        except Exception as e:
            continue
    
    return None

def test_download():
    """Test download functionality"""
    print("Testing SEC download functionality...")
    
    total_downloaded = 0
    total_size = 0
    start_time = time.time()
    
    for bank_name, cik in BANKS.items():
        print(f"\nTesting {bank_name} (CIK: {cik})")
        
        for year in ['2024', '2025']:
            for form_type in ['10-K', '10-Q']:
                print(f"  Fetching {form_type} for {year}...")
                
                filings = get_company_filings(cik, year, form_type, limit=1)
                
                for filing in filings:
                    print(f"    Downloading {filing['accession']} ({filing.get('primary_doc', 'N/A')})...")
                    
                    download_start = time.time()
                    content = download_filing_content(cik, filing['accession'], filing.get('primary_doc'))
                    download_time = time.time() - download_start
                    
                    if content:
                        size_mb = len(content.encode('utf-8')) / (1024 * 1024)
                        total_downloaded += 1
                        total_size += len(content.encode('utf-8'))
                        
                        print(f"    ✓ Downloaded: {size_mb:.1f} MB in {download_time:.2f}s")
                    else:
                        print(f"    ✗ Failed to download")
                
                time.sleep(0.2)  # Rate limiting
    
    total_time = time.time() - start_time
    
    print(f"\n{'='*50}")
    print(f"TEST RESULTS")
    print(f"{'='*50}")
    print(f"Files downloaded: {total_downloaded}")
    print(f"Total size: {total_size / (1024*1024):.1f} MB")
    print(f"Total time: {total_time:.1f}s")
    
    if total_downloaded > 0:
        avg_size = (total_size / (1024*1024)) / total_downloaded
        avg_time = total_time / total_downloaded
        
        print(f"Average file size: {avg_size:.1f} MB")
        print(f"Average download time: {avg_time:.1f}s per file")
        
        # Estimate full dataset (10 banks, 3 years, ~4 filings per year)
        estimated_files = 10 * 3 * 4
        estimated_size_mb = estimated_files * avg_size
        estimated_time_min = (estimated_files * avg_time) / 60
        
        print(f"\nFULL DATASET ESTIMATES:")
        print(f"Total files: ~{estimated_files}")
        print(f"Total size: ~{estimated_size_mb:.0f} MB ({estimated_size_mb/1024:.1f} GB)")
        print(f"Download time: ~{estimated_time_min:.0f} minutes")
        
        if estimated_time_min < 30:
            print("✅ FEASIBLE: Download time acceptable")
        else:
            print("⚠️  SLOW: Consider reducing scope or parallel downloads")
    else:
        print("❌ NO DOWNLOADS: Check SEC API access")

if __name__ == "__main__":
    test_download()