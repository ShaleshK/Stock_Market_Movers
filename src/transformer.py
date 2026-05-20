import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Tuple

# Configure local logging formatting
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MarketMoversTransformer:
    """Handles 30, 90, and 360-day price array transformation and ranks market movers."""
    
    def __init__(self, lookback_days: list = [30, 90, 360]):
        self.lookback_days = lookback_days
        logging.info("📊 MarketMoversTransformer initialized successfully.")

    def calculate_price_performance(self, price_history_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates historical price modifications over 30, 90, and 360-day windows.
        Expects a DataFrame with ticker columns and chronological date indexes.
        """
        logging.info("⚙️ Commencing rolling time-window vector performance metrics...")
        
        if price_history_df.empty or len(price_history_df) < max(self.lookback_days):
            logging.error("❌ Vector Transformation Block Failed: Insufficient historical data rows.")
            return pd.DataFrame()

        performance_records = []
        
        # Calculate trailing endpoints based on the newest available closing matrix row
        latest_date = price_history_df.index.max()
        
        for ticker in price_history_df.columns:
            latest_price = price_history_df[ticker].iloc[-1]
            
            # Prevent processing dead or completely unpriced entities
            if pd.isna(latest_price) or latest_price == 0:
                continue
                
            ticker_metrics = {"ticker": ticker, "latest_price": latest_price}
            
            for days in self.lookback_days:
                target_past_date = latest_date - timedelta(days=days)
                
                # Locate closest historical data block row matching the trailing index target
                try:
                    # Find the nearest date index entry without crashing on gaps
                    past_idx = price_history_df.index.get_indexer([target_past_date], method='pad')[0]
                    if past_idx != -1:
                        past_price = price_history_df[ticker].iloc[past_idx]
                        if past_price > 0:
                            # Calculate percentage performance metrics directly
                            pct_change = ((latest_price - past_price) / past_price) * 100
                            ticker_metrics[f"pct_change_{days}d"] = round(pct_change, 2)
                        else:
                            ticker_metrics[f"pct_change_{days}d"] = np.nan
                    else:
                        ticker_metrics[f"pct_change_{days}d"] = np.nan
                except Exception as e:
                    logging.debug(f"Skipped {ticker} performance delta calculation for {days}d window: {e}")
                    ticker_metrics[f"pct_change_{days}d"] = np.nan
            
            performance_records.append(ticker_metrics)
            
        return pd.DataFrame(performance_records)

    def extract_top_movers(self, performance_df: pd.DataFrame, days_window: int, top_n: int = 25) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Filters and segments the top N gainers and top N losers for a specific time window.
        """
        target_column = f"pct_change_{days_window}d"
        
        if target_column not in performance_df.columns:
            logging.error(f"❌ Transformation Fail: Feature column [{target_column}] missing from data context.")
            return pd.DataFrame(), pd.DataFrame()
            
        # Drop rows missing calculations for this target window
        clean_df = performance_df.dropna(subset=[target_column]).copy()
        
        # Isolate gainers and losers sorted dynamically
        gainers = clean_df.sort_values(by=target_column, ascending=False).head(top_n)
        losers = clean_df.sort_values(by=target_column, ascending=True).head(top_n)
        
        logging.info(f"🎯 Isolated top {top_n} Gainers and Losers for the trailing {days_window}-day bracket.")
        return gainers, losers

if __name__ == "__main__":
    # Quick module diagnostic mock test
    import numpy as np
    
    dates = pd.date_range(end=datetime.today(), periods=400)
    mock_prices = pd.DataFrame(
        np.random.randn(400, 3).cumsum(axis=0) + 100, 
        columns=['AAPL.US', 'MSFT.US', 'VOD.LSE'],
        index=dates
    )
    
    transformer = MarketMoversTransformer()
    perf_df = transformer.calculate_price_performance(mock_prices)
    
    if not perf_df.empty:
        gain, lose = transformer.extract_top_movers(perf_df, days_window=30, top_n=2)
        print("--- Top Test Gainers (30D) ---")
        print(gain[['ticker', 'latest_price', 'pct_change_30d']])
