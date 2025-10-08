# Simple bank search without external API calls

class BankSearchAPI:
    def __init__(self):
        # Major US banks and financial institutions with their CIKs
        self.major_banks = {
            "ALLY FINANCIAL INC": "0001479094",
            "AMERICAN EXPRESS COMPANY": "0000004962",
            "BANK OF NEW YORK MELLON CORP": "0001390777",
            "BB&T CORPORATION": "0000092230",
            "CHARLES SCHWAB CORPORATION": "0000316709",
            "COMERICA INCORPORATED": "0000028412",
            "DISCOVER FINANCIAL SERVICES": "0001393612",
            "FIFTH THIRD BANCORP": "0000035527",
            "FIRST REPUBLIC BANK": "0001132979",
            "GOLDMAN SACHS GROUP INC": "0000886982",
            "HUNTINGTON BANCSHARES INC": "0000049196",
            "JPMORGAN CHASE & CO": "0000019617",
            "KEYCORP": "0000091576",
            "M&T BANK CORP": "0000036405",
            "MORGAN STANLEY": "0000895421",
            "NORTHERN TRUST CORP": "0000073124",
            "PNC FINANCIAL SERVICES GROUP INC": "0000713676",
            "REGIONS FINANCIAL CORP": "0001281761",
            "STATE STREET CORP": "0000093751",
            "SUNTRUST BANKS INC": "0000750556",
            "SYNCHRONY FINANCIAL": "0001601712",
            "TRUIST FINANCIAL CORP": "0001534701",
            "U.S. BANCORP": "0000036104",
            "WELLS FARGO & COMPANY": "0000072971",
            "ZIONS BANCORPORATION": "0000109380",
            "BANK OF AMERICA CORP": "0000070858",
            "CITIGROUP INC": "0000831001",
            "CAPITAL ONE FINANCIAL CORP": "0000927628"
        }
    
    def search_banks(self, query):
        """Search for banks by name in predefined list"""
        try:
            query_lower = query.lower().strip()
            results = []
            
            print(f"Searching for: '{query_lower}'")
            
            for bank_name, cik in self.major_banks.items():
                bank_lower = bank_name.lower()
                
                # Check if query matches bank name
                if query_lower in bank_lower:
                    results.append({
                        'name': bank_name,
                        'cik': cik,
                        'ticker': ''
                    })
                    print(f"Match found: {bank_name}")
            
            print(f"Found {len(results)} matching banks")
            return results[:10]  # Limit to 10 results
            
        except Exception as e:
            print(f"Error searching banks: {e}")
            return []

# Global instance
bank_search = BankSearchAPI()