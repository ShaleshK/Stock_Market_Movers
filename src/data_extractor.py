import logging
import requests
from typing import Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class EODHDEquityExtractor:
    """Handles secure individual validation of equity metrics from the EODHD API."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        if not self.api_key:
            raise ValueError("A valid EODHD API Key must be provided.")

    def fetch_individual_fundamentals(self, ticker: str) -> Dict[str, Any]:
        """Requests individual fundamental company sheets using required dash formatting."""
        clean_ticker = str(ticker).upper().replace(".", "-")
        fund_url = f"https://eodhd.com{clean_ticker}"
        params = {"api_token": self.api_key, "fmt": "json"}
        
        try:
            response = requests.get(fund_url, params=params, timeout=12)
            if response.status_code == 200:
                data = response.json()
                general = data.get("General", {})
                highlights = data.get("Highlights", {})
                
                return {
                    "Name": general.get("Name", "Unknown"),
                    "MarketCap": float(highlights.get("MarketCapitalization", 0))
                }
        except Exception as e:
            logging.debug(f"Could not retrieve details for {ticker}: {e}")
            
        return {"Name": "Unknown", "MarketCap": 0}


