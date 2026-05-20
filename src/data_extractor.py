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
        self.base_url = "https://eodhd.com/api"
        
        if not self.api_key:
            logging.error("Initialization Failed: EODHD_API_KEY environment token is missing.")
            raise ValueError("A valid EODHD API Key must be provided or configured in your environment.")

    def fetch_exchange_symbols(self, exchange_code: str) -> List[Dict[str, Any]]:
        """Pulls all active ticker listings for a specific exchange code (e.g., 'US')."""
        # Clean, un-slashed endpoint layout string
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
        Production Version: Uses EODHD Bulk Fundamentals to extract 
        true large-cap equities worth >= $1,000,000,000.
        """
        aggregated_tickers = []
        
        for exchange in exchanges:
            # Documented EODHD endpoint for pulling entire exchange financial traits at once
            endpoint = f"{self.base_url}/bulk-fundamentals/{exchange}"
            params = {"api_token": self.api_key, "fmt": "json"}
            
            try:
                response = requests.get(endpoint, params=params, timeout=30)
                if response.status_code == 200:
                    bulk_data = response.json()
                    
                    for ticker_code, financial_records in bulk_data.items():
                        # Extract deep structural fundamental parameters safely
                        general_info = financial_records.get("General", {})
                        highlights = financial_records.get("Highlights", {})
                        
                        if general_info.get("Type") == "Common Stock":
                            market_cap = float(highlights.get("MarketCapitalization", 0))
                            
                            if market_cap >= 1_000_000_000:
                                aggregated_tickers.append({
                                    "ticker": f"{ticker_code}.{exchange}",
                                    "name": general_info.get("Name"),
                                    "exchange": exchange,
                                    "market_cap": market_cap
                                })
            except Exception as e:
                logging.error(f"Failed to ingest bulk fundamentals for {exchange}: {e}")
                        
        df_large_caps = pd.DataFrame(aggregated_tickers)
        logging.info(f"🎯 Production Filter Complete: Isolated {len(df_large_caps)} true Large-Cap entities.")
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
