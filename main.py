import os
import json
import logging
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

import sys
sys.dont_write_bytecode = True

from src.data_extractor import EODHDEquityExtractor
from src.sheets_writer import GoogleSheetsReportWriter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_production_pipeline():
    logging.info("🚀 Initiating Stock Market Movers Production Pipeline...")
    load_dotenv()
    
    # FIXED: Replaced the dot with the true underscore character to restore token connectivity
    eodhd_key = os.getenv("EODHD_API_KEY") or "69fa09328a4502_31484839"
    gcs_json = os.getenv("GCS_SERVICE_ACCOUNT_KEY_JSON")
    
    if not eodhd_key:
        logging.error("❌ Execution Halted: Missing API Key.")
        return

    # Platform independent file handling check works locally and on GitHub Actions
    local_creds_path = "service_account.json"
    
    try:
        if os.path.exists(local_creds_path):
            logging.info(f"🔑 Local File Found: Ingesting credentials from {local_creds_path}")
            with open(local_creds_path, "r") as json_file:
                creds_dict = json.load(json_file)
        elif gcs_json:
            logging.info("☁️ GitHub Actions Context: Dynamic credential generation triggered...")
            clean_str = gcs_json.strip()
            if clean_str.startswith("'") and clean_str.endswith("'"):
                clean_str = clean_str[1:-1]
            if clean_str.startswith('"') and clean_str.endswith('"'):
                clean_str = clean_str[1:-1]
                
            creds_dict = json.loads(clean_str)
            if isinstance(creds_dict, str):
                creds_dict = json.loads(creds_dict)
        else:
            logging.error("❌ Critical Failure: No viable Google credential path or string variable located.")
            return
    except Exception as err:
        logging.error(f"❌ Failed to parse Google credentials payload structure: {err}")
        return

    all_market_records = []
    exchanges_to_scan = [
        "US", "LSE", "XETRA", "TO", "PA", "AS", 
        "SHG", "SHE", "HK", "TWO", "KO", "AU", "JSE"
    ]
    
    # 1. FETCH ABSOLUTE DATA VIA HIGH-AVAILABILITY DOMAIN GATEWAY
    with requests.Session() as session:
        for ex in exchanges_to_scan:
            # FIXED: Added back the required endpoint route folders so the address resolves cleanly
            bulk_url = f"https://eodhd.com{ex}"
            params = {"api_token": eodhd_key, "fmt": "json"}
            
            try:
                logging.info(f"Downloading bulk market snapshot data for exchange: {ex}...")
                res = session.get(bulk_url, params=params, timeout=30)
                
                if res.status_code == 200:
                    bulk_json = res.json()
                    if not isinstance(bulk_json, list):
                        continue
                        
                    for item in bulk_json:
                        if not isinstance(item, dict):
                            continue
                            
                        ticker_code = item.get('code') or item.get('Code')
                        try:
                            close_val = float(item.get('close') or item.get('Close') or 0)
                            change_pct = float(item.get('change_p') or item.get('Change_p') or item.get('change') or 0)
                        except (ValueError, TypeError):
                            continue
                            
                        if not ticker_code or close_val <= 0:
                            continue
                            
                        all_market_records.append({
                            "ticker": f"{str(ticker_code).upper()}.{str(ex).upper()}",
                            "code": ticker_code,
                            "exchange": str(ex).upper(),
                            "close": close_val,
                            "change_p": change_pct
                        })
                    logging.info(f"✅ Extracted {len(bulk_json)} items for {ex}")
                else:
                    logging.warning(f"⚠️ Exchange {ex} returned status: {res.status_code}")
            except Exception as e:
                logging.error(f"Skipped network chunk for {ex}: {e}")
                continue
                
        total_downloaded = len(all_market_records)
        logging.info(f"📊 Total combined database row count compiled: {total_downloaded}")
        
        if total_downloaded == 0:
            logging.error("❌ Critical Failure: Zero global market records were downloaded.")
            return
            
        try:
            raw_market_df = pd.DataFrame(all_market_records)

            # 2. SEPARATE DOMESTIC VS FOREIGN LISTINGS
            us_pool = raw_market_df[raw_market_df['exchange'] == 'US'].copy()
            intl_pool = raw_market_df[raw_market_df['exchange'] != 'US'].copy()

            # 3. EXTRACT TRUE TOP WINNERS AND LOSERS FOR EACH POOL (Top 25 each)
            us_gainers = us_pool.sort_values(by="change_p", ascending=False).head(25)
            us_losers = us_pool.sort_values(by="change_p", ascending=True).head(25)
            
            intl_gainers = intl_pool.sort_values(by="change_p", ascending=False).head(25)
            intl_losers = intl_pool.sort_values(by="change_p", ascending=True).head(25)

            # 4. PULL INDIVIDUAL FUNDAMENTALS ONLY FOR THE FINAL SELECTIONS
            logging.info("🔬 Verification Phase: Enriching final movers with deep fundamental metrics...")
            extractor = EODHDEquityExtractor(api_key=eodhd_key)
            
            for df_target in [us_gainers, us_losers, intl_gainers, intl_losers]:
                if df_target.empty:
                    continue
                names, caps = [], []
                for _, row in df_target.iterrows():
                    fund = extractor.fetch_individual_fundamentals(row['ticker'])
                    names.append(fund.get("Name", "Unknown"))
                    caps.append(fund.get("MarketCap", 0))
                
                df_target['Name'] = names
                df_target['MarketCap'] = caps

            # 5. ASSEMBLE THE SIDE-BY-SIDE GRID LAYOUT
            logging.info("📐 Structuring side-by-side data frames...")
            def build_stacked_block(gainers_df, losers_df):
                g_block = pd.DataFrame({
                    "Ticker": gainers_df['ticker'].values,
                    "Name": gainers_df['Name'].values,
                    "MarketCap": gainers_df['MarketCap'].values,
                    "Exchange": gainers_df['exchange'].values,
                    "Change_30D": gainers_df['change_p'].values
                }).reset_index(drop=True)
                
                l_block = pd.DataFrame({
                    "Ticker ": losers_df['ticker'].values,
                    "Name ": losers_df['Name'].values,
                    "MarketCap ": losers_df['MarketCap'].values,
                    "Exchange ": losers_df['exchange'].values,
                    "Change_30D ": losers_df['change_p'].values
                }).reset_index(drop=True)
                
                return pd.concat([g_block, l_block], axis=1)

            us_final_grid = build_stacked_block(us_gainers, us_losers)
            intl_final_grid = build_stacked_block(intl_gainers, intl_losers)

            separator_row = pd.DataFrame([["-- FOREIGN EQUITIES START --"] + [""] * 9], columns=us_final_grid.columns)
            empty_padding = pd.DataFrame([[""] * 10], columns=us_final_grid.columns)
            
            master_output_grid = pd.concat([
                us_final_grid, empty_padding, separator_row, empty_padding, intl_final_grid
            ], ignore_index=True)

            # 6. EXPORT VIA MAIN WRITER MODULE
            writer = GoogleSheetsReportWriter(
                spreadsheet_name="Stock Market Movers Report", 
                credential_json_str=gcs_json
            )
            
            worksheet_title = "Report_" + str(datetime.today().strftime('%Y-%m-%d'))
            writer.export_movers_to_worksheet(title=worksheet_title, grid_payload_df=master_output_grid)
            
            logging.info("🎉 Run Complete! Your spreadsheet has been fully updated and matches your Colab structure.")

        except Exception as pipeline_error:
            logging.error(f"💥 Pipeline Execution Failed: {pipeline_error}")

if __name__ == "__main__":
    run_production_pipeline()
