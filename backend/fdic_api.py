import requests
import pandas as pd

def get_real_fdic_data():
    """Fetch real banking data from FDIC API with robust error handling"""
    banks = {
        "JPMORGAN CHASE BANK": 628,
        "BANK OF AMERICA": 3510,
        "WELLS FARGO BANK": 3511,
        "CITIBANK": 7213,
        "U.S. BANK": 6548,
        "PNC BANK": 6384,
        "TRUIST BANK": 10057,
        "CAPITAL ONE": 4297,
        "GOLDMAN SACHS BANK": 33124,
        "FIFTH THIRD BANCORP": 6672,
        "REGIONS FINANCIAL CORP": 12368
    }
    
    quarters = {
        "2023-Q4": "20231231",
        "2024-Q1": "20240331",
        "2024-Q2": "20240630",
        "2024-Q3": "20240930"
    }
    
    data = []
    successful_fetches = 0
    total_attempts = len(banks) * len(quarters)
    
    for bank_name, cert in banks.items():
        for quarter_name, fdic_date in quarters.items():
            try:
                url = f"https://api.fdic.gov/banks/financials?filters=CERT:{cert}%20AND%20REPDTE:{fdic_date}&limit=1"
                response = requests.get(url, timeout=15)
                response.raise_for_status()
                
                result = response.json()
                if result.get('data') and len(result['data']) > 0:
                    bank_data = result['data'][0]['data']
                    
                    metrics_data = [
                        {"Metric": "Return on Assets (ROA)", "Value": safe_float(bank_data.get('ROA'))},
                        {"Metric": "Return on Equity (ROE)", "Value": safe_float(bank_data.get('ROE'))},
                        {"Metric": "Net Interest Margin (NIM)", "Value": calculate_nim_percentage(bank_data)},
                        {"Metric": "Tier 1 Capital Ratio", "Value": safe_float(bank_data.get('RBC1AAJ'))},
                        {"Metric": "Loan-to-Deposit Ratio (LDR)", "Value": calculate_ldr(bank_data)},
                        {"Metric": "CRE Concentration Ratio (%)", "Value": safe_float(bank_data.get('NCRER'))}
                    ]
                    
                    for metric_data in metrics_data:
                        data.append({
                            "Bank": bank_name,
                            "Quarter": quarter_name,
                            "Year": quarter_name[:4],
                            "Metric": metric_data["Metric"],
                            "Value": metric_data["Value"],
                            "Bank Type": "Base Bank" if "JPMORGAN" in bank_name else "Peer Bank"
                        })
                    
                    successful_fetches += 1
                    
            except requests.exceptions.Timeout:
                print(f"Timeout fetching {bank_name} {quarter_name}")
            except requests.exceptions.RequestException as e:
                print(f"Request failed for {bank_name} {quarter_name}: {e}")
            except (KeyError, ValueError, TypeError) as e:
                print(f"Data parsing error for {bank_name} {quarter_name}: {e}")
            except Exception as e:
                print(f"Unexpected error for {bank_name} {quarter_name}: {e}")
    
    # Require at least 30% success rate
    if successful_fetches < (total_attempts * 0.3):
        raise Exception(f"FDIC API returned insufficient data ({successful_fetches}/{total_attempts} successful)")
    
    if not data:
        raise Exception("No FDIC data retrieved")
    
    print(f"FDIC API: {successful_fetches}/{total_attempts} successful fetches")
    return pd.DataFrame(data)

def safe_float(value, default=0.0):
    """Safely convert value to float"""
    try:
        return round(float(value or default), 2)
    except (ValueError, TypeError):
        return default

def calculate_nim_percentage(bank_data):
    """Calculate NIM as percentage from FDIC data"""
    try:
        nim = safe_float(bank_data.get('NIM', 0))
        asset = safe_float(bank_data.get('ASSET', 1))
        return round((nim / asset * 100) if asset > 0 else 0, 2)
    except Exception:
        return 0.0

def calculate_ldr(bank_data):
    """Calculate Loan-to-Deposit Ratio from FDIC data"""
    try:
        loans = safe_float(bank_data.get('LNLSNET', 0))
        deposits = safe_float(bank_data.get('DEP', 1))
        return round((loans / deposits * 100) if deposits > 0 else 0, 2)
    except Exception:
        return 0.0