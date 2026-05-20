import os
import logging
import requests
import pandas as pd
from typing import Optional, List, Dict, Any

# Configure local logging formatting
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class EODHDEquityExtractor:
    """Handles secure connection, ingestion, and validation of equity market arrays from the EODHD API."""
    
    def __init__(self, api_key: Optional[str] = None):
        # Fall back to environment loading if not explicitly passed
        self.api_key = api_key or os.getenv("EODHD_API_KEY")
        self.base_url = "https://eodhd.com"
        
        if not self.api_key:
            logging.error("Initialization Failed: EODHD_API_KEY environment token is missing.")
            raise ValueError("A valid EODHD API Key must be provided or configured in your environment.")

    def fetch_exchange_symbols(self, exchange_code: str) -> List[Dict[str, Any]]:
        """Pulls all active ticker listings for a specific exchange code (e.g., 'US', 'LSE')."""
        endpoint = f"{self.base_url}/exchange-symbol-list/{exchange_code}"
        params = {"api_token": self.api_key, "fmt": "json"}
        
        logging.info(f"🚀 Initializing secure API request for Exchange: [{exchange_code}]...")
        try:
            response = requests.get(endpoint, params=params, timeout=15)
            response.raise_for_status() # Raise error for bad HTTP statuses (4xx, 5xx)
            
            data = response.json()
            logging.info(f"✅ Extracted {len(data)} raw asset records from [{exchange_code}] endpoint.")
            return data
            
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ Failed to fetch symbols from exchange {exchange_code}: {e}")
            return []

    def extract_and_filter_large_caps(self, exchanges: List[str] = ["US"]) -> pd.DataFrame:
        """
        Loops through target exchanges, aggregates ticker strings, 
        and extracts equities with a Market Cap >= $1,000,000,000.
        """
        aggregated_tickers = []
        
        for exchange in exchanges:
            raw_symbols = self.fetch_exchange_symbols(exchange_code=exchange)
            
            for item in raw_symbols:
                # Target Common Stocks and filter by Market Cap floor safely
                if item.get("Type") == "Common Stock":
                    # Convert market capitalization securely to float for matching evaluation
                    try:
                        market_cap = float(item.get("MarketCapitalization", 0))
                    except (ValueError, TypeError):
                        market_cap = 0.0
                        
                    if market_cap >= 1_000_000_000:
                        aggregated_tickers.append({
                            "ticker": f"{item.get('Code')}.{exchange}",
                            "name": item.get("Name"),
                            "exchange": exchange,
                            "market_cap": market_cap
                        })
                        
        df_large_caps = pd.DataFrame(aggregated_tickers)
        logging.info(f"🎯 Aggregation Finished: Generated subset containing {len(df_large_caps)} Large Cap Equities.")
        return df_large_caps

if __name__ == "__main__":
    # Test script verification block
    import dotenv
    dotenv.load_dotenv()
    
    try:
        extractor = EODHDEquityExtractor()
        # Verify a quick subset test sample of US equities
        test_df = extractor.extract_and_filter_large_caps(exchanges=["US"])
        if not test_df.empty:
            print(test_df.head())
    except Exception as error:
        print(f"Extraction execution check failed: {error}")
