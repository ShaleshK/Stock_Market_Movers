import os
import json
import gspread
import logging
import pandas as pd
from typing import Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class GoogleSheetsReportWriter:
    """Manages service account authentication and populates side-by-side reports into Google Sheets."""
    
    def __init__(self, spreadsheet_name: str, credential_json_str: Optional[str] = None):
        self.spreadsheet_name = spreadsheet_name
        self.credential_json_str = credential_json_str or os.getenv("GCS_SERVICE_ACCOUNT_KEY_JSON")
        self.client = None
        self.workbook = None
        
        self._authenticate_service_account()

    def _authenticate_service_account(self):
        """Initializes secure server-to-server connection bypassing string wrapping anomalies."""
        logging.info("📝 Synchronizing final data arrays into Google Sheets...")
        local_creds_path = "service_account.json"
        
        try:
            if os.path.exists(local_creds_path):
                logging.info(f"🔑 Local File Detected: Ingesting credentials from {local_creds_path}")
                with open(local_creds_path, "r") as json_file:
                    creds_dict = json.load(json_file)
            else:
                logging.info("☁️ Cloud Context: Parsing credentials string from environment configuration...")
                creds_dict = json.loads(self.credential_json_str)
                if isinstance(creds_dict, str):
                    creds_dict = json.loads(creds_dict)
                    
            self.client = gspread.service_account_from_dict(creds_dict)
            self.workbook = self.client.open(self.spreadsheet_name)
            logging.info(f"📁 Successfully connected to workbook: '{self.spreadsheet_name}'")
        except Exception as e:
            logging.error(f"💥 Critical authentication failure to Google Sheets API: {e}")
            raise

    def export_movers_to_worksheet(self, title: str, grid_payload_df: pd.DataFrame):
        """Writes the side-by-side layout matrix directly onto your active sheet canvas tab."""
        if self.workbook is None:
            raise RuntimeError("Cannot write data: Client is not authenticated.")

        try:
            try:
                worksheet = self.workbook.worksheet(title)
                worksheet.clear()
            except gspread.exceptions.WorksheetNotFound:
                worksheet = self.workbook.add_worksheet(title=title, rows=150, cols=12)
            
            headers = grid_payload_df.columns.tolist()
            rows_data = grid_payload_df.fillna("").values.tolist()
            final_matrix = [headers] + rows_data
            
            worksheet.update("A1", final_matrix)
            logging.info(f"✅ Successfully written data metrics matrix into worksheet: '{title}'")
            worksheet.format("A1:L1", {"textFormat": {"bold": True}})
            
        except Exception as e:
            logging.error(f"❌ Failed writing payload execution arrays to worksheet panel: {e}")
