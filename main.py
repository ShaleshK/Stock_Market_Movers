import os
import json
import logging
import requests
import pandas as pd
import gspread
from datetime import datetime
from dotenv import load_dotenv

import sys
sys.dont_write_bytecode = True

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_production_pipeline():
    logging.info("🚀 Initiating Local Stock Market Movers Production Pipeline...")
    load_dotenv()
    
    eodhd_key = os.getenv("EODHD_API_KEY") or "69fa09328a4502.31484839"
    gcs_json = os.getenv("GCS_SERVICE_ACCOUNT_KEY_JSON")
    
    if not eodhd_key:
        logging.error("❌ Execution Halted: Missing API Key.")
        return

    # FIXED: Platform independent file handling check works locally and on GitHub Actions
    local_creds_path = "service_account.json"
    
    try:
        if os.path.exists(local_creds_path):
            logging.info(f"🔑 Local File Found: Ingesting credentials from {local_creds_path}")
            with open(local_creds_path, "r") as json_file:
                creds_dict = json.load(json_file)
        elif gcs_json:
            logging.info("☁️ GitHub Actions Context: Dynamic credential generation triggered...")
            # Clean string parsing strips out any cloud variable escape characters
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
            bulk_url = "https://eodhd.com" + str(ex)
            params = {"api_token": eodhd_key, "fmt": "json"}
            
            try:
                logging.info("Downloading bulk market snapshot data for exchange: " + str(ex) + "...")
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
                            "ticker": str(ticker_code).upper() + "." + str(ex).upper(),
                            "code": ticker_code,
                            "exchange": str(ex).upper(),
                            "close": close_val,
                            "change_p": change_pct
                        })
                    logging.info("✅ Extracted " + str(len(bulk_json)) + " items for " + str(ex))
                else:
                    logging.warning("⚠️ Exchange " + str(ex) + " returned status: " + str(res.status_code))
            except Exception as e:
                logging.error("Skipped network chunk for " + str(ex) + ": " + str(e))
                continue
                
        total_downloaded = len(all_market_records)
        logging.info("📊 Total combined database row count compiled: " + str(total_downloaded))
        
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
            for df_target in [us_gainers, us_losers, intl_gainers, intl_losers]:
                if df_target.empty:
                    continue
                names, caps = [], []
                for _, row in df_target.iterrows():
                    clean_ticker = str(row['ticker']).upper().replace(".", "-")
                    fund_url = "https://eodhd.com" + clean_ticker
                    try:
                        f_res = session.get(fund_url, params={"api_token": eodhd_key, "fmt": "json"}, timeout=10)
                        if f_res.status_code == 200:
                            f_data = f_res.json()
                            names.append(f_data.get("General", {}).get("Name", "Unknown"))
                            caps.append(float(f_data.get("Highlights", {}).get("MarketCapitalization", 0)))
                            continue
                    except:
                        pass
                    names.append("Unknown")
                    caps.append(0)
                
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

            # 6. EXPORT DIRECTLY TO GOOGLE SHEETS
            logging.info("📝 Synchronizing final data arrays into Google Sheets...")
            client = gspread.service_account_from_dict(creds_dict)
            workbook = client.open("Stock Market Movers Report")
            
            worksheet_title = "Report_" + str(datetime.today().strftime('%Y-%m-%d'))
            try:
                ws = workbook.worksheet(worksheet_title)
                ws.clear()
            except:
                ws = workbook.add_worksheet(title=worksheet_title, rows=150, cols=12)
                
            payload = [master_output_grid.columns.tolist()] + master_output_grid.fillna("").values.tolist()
            ws.update("A1", payload)
            
            logging.info("🎉 Run Complete! Your spreadsheet has been fully updated and matches your Colab structure.")

        except Exception as pipeline_error:
            logging.error("💥 Pipeline Execution Failed: " + str(pipeline_error))

if __name__ == "__main__":
    run_production_pipeline()


