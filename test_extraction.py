#!/usr/bin/env python3

import PyPDF2
import re
import sys

def extract_company_name(pdf_path):
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Read first page for company name extraction
            first_page_text = pdf_reader.pages[0].extract_text().upper() if pdf_reader.pages else ''
            
            print(f"First 1000 chars of PDF:")
            print("-" * 50)
            print(first_page_text[:1000])
            print("-" * 50)
            
            # Enhanced company name extraction
            bank_name = 'Unknown Company'
            text_upper = first_page_text
            
            # First try standard SEC document patterns
            sec_patterns = [
                r'COMPANY:\s*([A-Z][A-Z\s&,\.\-]+?)(?:\s*\n|\s*FORM)',
                r'REGISTRANT:\s*([A-Z][A-Z\s&,\.\-]+?)(?:\s*\n|\s*CIK)',
                r'([A-Z][A-Z\s&,\.\-]+?)\s*\n\s*\(EXACT NAME OF REGISTRANT',
                r'([A-Z][A-Z\s&,\.\-]+?)\s*\n\s*\(NAME OF REGISTRANT',
                r'COMMISSION FILE NO[^\n]*\n\s*([A-Z][A-Z\s&,\.\-]+?)\s*\n\s*\(EXACT NAME',
                r'FILE NO[^\n]*\n\s*([A-Z][A-Z\s&,\.\-]+?)\s*\n\s*\(EXACT NAME'
            ]
            
            print(f"Trying SEC document patterns...")
            # Try SEC document patterns first
            for i, pattern in enumerate(sec_patterns):
                matches = re.findall(pattern, text_upper[:3000])
                print(f"Pattern {i+1}: {pattern}")
                print(f"Matches: {matches}")
                if matches:
                    match = matches[0].strip().rstrip(',')
                    if len(match) > 5 and 'UNITED STATES' not in match and 'SECURITIES' not in match:
                        bank_name = match
                        print(f"✅ Found company: {bank_name}")
                        break
            
            # If no SEC pattern match, try generic financial company patterns
            if bank_name == 'Unknown Company':
                print(f"Trying generic financial patterns...")
                generic_patterns = [
                    (r'([A-Z][A-Z\s&]+)\s+BANK(?:ING)?(?:\s+(?:CORP|CORPORATION|COMPANY|CO|INC|NA|N\.A\.))?', 'BANK'),
                    (r'([A-Z][A-Z\s&]+)\s+BANCORP(?:ORATION)?', 'BANCORP'),
                    (r'([A-Z][A-Z\s&]+)\s+FINANCIAL(?:\s+(?:CORP|CORPORATION|COMPANY|CO|INC|GROUP))?', 'FINANCIAL'),
                    (r'([A-Z][A-Z\s&]+)\s+INC\.?', 'INC'),
                    (r'([A-Z][A-Z\s&]+)\s+CORP(?:ORATION)?', 'CORP')
                ]
                
                for pattern, suffix in generic_patterns:
                    matches = re.findall(pattern, text_upper)
                    print(f"Pattern: {pattern}")
                    print(f"Matches: {matches}")
                    if matches:
                        match = matches[0].strip()
                        if len(match) > 3 and 'UNITED STATES' not in match and 'FEDERAL' not in match:
                            bank_name = match + ' ' + suffix if suffix not in match else match
                            print(f"✅ Found company: {bank_name}")
                            break
            
            return bank_name
            
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 test_extraction.py <path_to_pdf>")
        print("Example: python3 test_extraction.py ~/Desktop/10k.pdf")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    company_name = extract_company_name(pdf_path)
    print(f"\n🏢 EXTRACTED COMPANY NAME: {company_name}")