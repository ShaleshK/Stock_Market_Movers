import logging
import numpy as np
import pandas as pd
from datetime import timedelta
from typing import List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MarketMoversTransformer:
    """Helper vector block handles rolling math configurations for legacy references safely."""
    
    def __init__(self, lookback_days: List[int] = None):
        self.lookback_days = lookback_days or [30, 90, 360]

    def calculate_price_performance(self, price_history_df: pd.DataFrame) -> pd.DataFrame:
        """Commencing rolling time-window vector performance metrics..."""
        if price_history_df.empty:
            logging.error("❌ Vector Transformation Block Failed: DataFrame is empty.")
            return pd.DataFrame()
            
        performance_records = []
        latest_date = price_history_df.index.max()
        
        for ticker in price_history_df.columns:
            latest_price = price_history_df[ticker].iloc[-1]
            if pd.isna(latest_price) or latest_price == 0:
                continue
                
            ticker_metrics = {"ticker": ticker}
            for days in self.lookback_days:
                target_past_date = latest_date - timedelta(days=days)
                first_available_date = price_history_df[ticker].dropna().index.min()
                
                if pd.isna(first_available_date) or target_past_date < first_available_date:
                    ticker_metrics[f"pct_change_{days}d"] = np.nan
                    continue
                    
                try:
                    past_price = price_history_df[ticker].loc[:target_past_date].dropna().iloc[-1]
                    if past_price > 0:
                        pct_change = ((latest_price - past_price) / past_price) * 100
                        ticker_metrics[f"pct_change_{days}d"] = round(pct_change, 2)
                    else:
                        ticker_metrics[f"pct_change_{days}d"] = np.nan
                except Exception:
                    ticker_metrics[f"pct_change_{days}d"] = np.nan
                    
            performance_records.append(ticker_metrics)
        return pd.DataFrame(performance_records)
