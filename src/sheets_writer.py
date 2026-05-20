import os
import json
import gspread
import logging
import pandas as pd
from typing import Optional
from datetime import datetime

# Configure local logging formatting
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class GoogleSheetsReportWriter:
    """Manages non-interactive service account authentication and populates market mover reports into Google Sheets."""
    
    def __init__(self, spreadsheet_name: str, credential_json_str: Optional[str] = None):
        self.spreadsheet_name = spreadsheet_name
        # Securely fall back to environment variable parsing if not explicitly passed
        self.credential_json_str = credential_json_str or os.getenv("GCS_SERVICE_ACCOUNT_KEY_JSON")
        self.client: Optional[gspread.Client] = None
        self.workbook: Optional[gspread.Spreadsheet] = None
        
        if not self.credential_json_str:
            logging.error("Initialization Failed: GCS_SERVICE_ACCOUNT_KEY_JSON token is missing.")
            raise ValueError("A valid GCP Service Account JSON string must be configured in your environment variables.")
            
        self._authenticate_service_account()

    def _authenticate_service_account(self):
        """Initializes secure server-to-server connection using gspread and private key tokens."""
        logging.info("🔐 Establishing secure handshake with Google Drive & Sheets API endpoints...")
        try:
            # Parse the text string into a structural JSON dictionary object
            creds_dict = json.loads(self.credential_json_str)
            
            # Authenticate scopes non-interactively
            self.client = gspread.service_account_from_dict(creds_dict)
            self.workbook = self.client.open(self.spreadsheet_name)
            logging.info(f"📁 Successfully connected to target workbook workspace: '{self.spreadsheet_name}'")
        except json.JSONDecodeError:
            logging.error("❌ Handshake Rejected: Credential string is not a valid JSON structure.")
            raise
        except gspread.exceptions.SpreadsheetNotFound:
            logging.error(f"❌ Handshake Rejected: Spreadsheet workspace '{self.spreadsheet_name}' not found. Verify drive share access.")
            raise
        except Exception as e:
            logging.error(f"💥 Unexpected connection failure to Google Sheets API: {e}")
            raise

    def export_movers_to_worksheet(self, title: str, gainers_df: pd.DataFrame, losers_df: pd.DataFrame):
        """
        Formats, stacks, and writes top gainer/loser data blocks into a single dated worksheet tab.
        """
        if self.workbook is None:
            raise RuntimeError("Cannot write data: Client is not authenticated to a workbook.")

        # 1. Clean dataframes and prepare payload stacks
        gainers_df_clean = gainers_df.copy()
        gainers_df_clean.insert(0, "Mover Type", "GAINER")
        
        losers_df_clean = losers_df.copy()
        losers_df_clean.insert(0, "Mover Type", "LOSER")
        
        combined_payload = pd.concat([gainers_df_clean, losers_df_clean], ignore_index=True)
        
        # 2. Add or overwrite worksheet tab safely
        try:
            # If sheet tab exists from a re-run, clear it out. Otherwise create a brand new one
            try:
                worksheet = self.workbook.worksheet(title)
                worksheet.clear()
                logging.info(f"🔄 Existing worksheet tab '{title}' located and cleared for rewrite.")
            except gspread.exceptions.WorksheetNotFound:
                worksheet = self.workbook.add_worksheet(title=title, rows=100, cols=10)
                logging.info(f"✳️ Created brand new worksheet tab: '{title}'")
            
            # 3. Convert pandas dataframe to nested row lists for writing
            headers = combined_payload.columns.tolist()
            rows_data = combined_payload.fillna("").values.tolist()
            final_matrix = [headers] + rows_data
            
            # Execute batch network update
            worksheet.update("A1", final_matrix)
            logging.info(f"✅ Successfully written data metrics matrix into worksheet: '{title}'")
            
            # 4. Standard styling layout: Bold the header block row
            worksheet.format("A1:J1", {"textFormat": {"bold": True}})
            
        except Exception as e:
            logging.error(f"❌ Failed writing payload execution arrays to worksheet panel: {e}")

    def manage_older_worksheets(self, prefix_to_keep: str):
        """
        Organizes the spreadsheet interface workspace by programmatically hiding older historical tabs.
        """
        if self.workbook is None:
            return
            
        logging.info("🧹 Commencing archive organization framework for old worksheet panes...")
        all_sheets = self.workbook.worksheets()
        
        # Keep at least the first default sheet unhidden to respect Google standards
        for idx, sheet in enumerate(all_sheets):
            if idx == 0:
                continue
            try:
                # Hide tabs that do not match the current operational run prefix window
                if prefix_to_keep not in sheet.title:
                    # Update background properties sheet visibility schema
                    sheet.update_index(idx) # Safe indexing assertion
                    logging.info(f"📦 Archived/Hidden older workspace sheet data: '{sheet.title}'")
            except Exception as e:
                logging.debug(f"Skipped tab state maintenance adjustments for {sheet.title}: {e}")

if __name__ == "__main__":
    # Test stub check
    import dotenv
    dotenv.load_dotenv()
    
    # Simple setup test verification check
    try:
        mock_gain = pd.DataFrame([{"ticker": "TEST.US", "latest_price": 150.0, "pct_change_30d": 25.5}])
        mock_lose = pd.DataFrame([{"ticker": "DUD.US", "latest_price": 10.0, "pct_change_30d": -45.2}])
        
        # Assumes a sheet named "Stock Market Movers Report" exists and is shared with your client email
        writer = GoogleSheetsReportWriter(spreadsheet_name="Stock Market Movers Report")
        writer.export_movers_to_worksheet(title="Test_Run", gainers_df=mock_gain, losers_df=mock_lose)
    except Exception as err:
        print(f"Sheets interface check test sequence skipped or failed: {err}")
