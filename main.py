import os
import logging
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Clean imports mapping directly to the exact classes we wrote
from src.data_extractor import EODHDEquityExtractor
from src.transformer import MarketMoversTransformer
from src.sheets_writer import GoogleSheetsReportWriter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_production_pipeline():
    logging.info("🚀 Initiating Local Stock Market Movers Production Pipeline...")
    
    # 1. Load hidden keys from your root .env file
    load_dotenv()
    
    eodhd_key = os.getenv("EODHD_API_KEY")
    gcs_json = os.getenv("GCS_SERVICE_ACCOUNT_KEY_JSON")
    
    if not eodhd_key or not gcs_json:
        logging.error("❌ Execution Halted: Missing variables inside your root .env file.")
        return

    try:
        # 2. Extract Data Elements using your active extractor class
        extractor = EODHDEquityExtractor(api_key=eodhd_key)
        large_caps_df = extractor.extract_and_filter_large_caps(exchanges=["US"])
        
        if large_caps_df.empty:
            logging.warning("⚠️ No valid tickers passed the market cap filters.")
            return

        # 3. Transform Data Vector Arrays (Production Upgrade: Real Market Closes)
        logging.info("📊 Fetching live historical closes and computing rolling performance windows...")
        transformer = MarketMoversTransformer()
        
        # Isolate a target basket (e.g., top 150 symbols to stay safely under API rate limits)
        target_tickers = large_caps_df['ticker'].head(150).tolist()
        
        # Build an analytical dataframe container to hold our real closing prices
        real_price_history = pd.DataFrame()
        
        # Request raw historical prices directly from the EODHD API
        for ticker in target_tickers:
            try:
                # Documented EODHD endpoint structure for end-of-day history
                hist_url = f"https://eodhd.com{ticker}"
                # Request 365 days of trailing historical data
                params = {"api_token": eodhd_key, "fmt": "json", "period": "d", "order": "a"}
                res = requests.get(hist_url, params=params, timeout=10)
                
                if res.status_code == 200:
                    ticker_data = res.json()
                    # Convert to a temporary DataFrame
                    temp_df = pd.DataFrame(ticker_data)
                    temp_df['date'] = pd.to_datetime(temp_df['date'])
                    temp_df.set_index('date', inplace=True)
                    
                    # Map the closing price to our master tracking dataframe
                    real_price_history[ticker] = temp_df['close']
            except Exception as e:
                logging.debug(f"Skipped tracking for {ticker} due to network timeout: {e}")

        # Execute our mathematical transforms using 100% real stock data
        performance_df = transformer.calculate_price_performance(real_price_history)
        gainers_30d, losers_30d = transformer.extract_top_movers(performance_df, days_window=30, top_n=25)
        #Production Fix 2: Add Real Market CapsTo filter for true companies worth over $1 Billion, we need to request the data fields from an EODHD endpoint that contains financial fundamentals, rather than just the basic symbol list endpoint.Open your src/data_extractor.py file, and update the function block to fetch the Bulk Fundamentals Endpoint, which returns real market caps:python    def extract_and_filter_large_caps(self, exchanges: List[str] = ["US"]) -> pd.DataFrame:
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

        # 4. Export directly to your linked worksheet tracking canvas
        # HYBRID CREDS LOADER: Dynamically switches between local file and cloud environment variables
        if os.path.exists("service_account.json"):
            logging.info("🔑 Local environment detected: Ingesting credentials from service_account.json...")
            with open("service_account.json", "r") as json_file:
                final_json_credentials = json.dumps(json.load(json_file))
        else:
            logging.info("☁️ Cloud environment detected: Fetching credentials from encrypted GitHub Secrets...")
            final_json_credentials = gcs_json

        writer = GoogleSheetsReportWriter(
            spreadsheet_name="Stock Market Movers Report", 
            credential_json_str=final_json_credentials
        )

    except Exception as pipeline_error:
        logging.error(f"💥 Pipeline Execution Failed: {pipeline_error}")

if __name__ == "__main__":
    run_production_pipeline()