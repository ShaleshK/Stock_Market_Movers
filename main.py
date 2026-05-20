# main.py
import os
import sys
from src.data_extractor import FetchEODHDData
from src.transformer import ProcessMovers
from src.sheets_writer import ExportToGoogleSheets

def run_market_report_pipeline():
    print("📈 Activating Market Movers Automated Report Pipeline...")
    
    # 1. Pipeline extraction safety gate
    api_key = os.getenv("EODHD_API_KEY")
    if not api_key:
        print("❌ Critical Error: EODHD_API_KEY variable missing.")
        sys.exit(1)
        
    # 2. Sequential pipeline execution
    try:
        raw_equities = FetchEODHDData(api_key=api_key)
        processed_report = ProcessMovers(raw_data=raw_equities)
        ExportToGoogleSheets(report_df=processed_report)
        print("✨ Success! Production sheets updated cleanly.")
    except Exception as e:
        print(f"💥 Pipeline Execution Failed: {e}")

if __name__ == "__main__":
    run_market_report_pipeline()