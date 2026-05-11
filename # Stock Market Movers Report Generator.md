# Stock Market Movers Report Generator

This Google Colab notebook automates the process of identifying top stock market gainers and losers from both US and major international exchanges. It fetches equity data, calculates price changes over various periods (30, 90, and 360 days), identifies top movers, and exports a comprehensive report to a Google Sheet.

## Features

*   **Comprehensive Equity Data**: Fetches US and major foreign equities with a market capitalization of \$1 Billion or greater using the EODHD API.
*   **Fundamental & Historical Metrics**: Retrieves key fundamental metrics (P/S, P/E, PEG, Dividend Yield) and historical price data (52-week high/low, 30/90/360-day price changes).
*   **Top Mover Identification**: Identifies the top 25 gainers and losers for daily (30-day change) and weekly (90-day, 360-day changes) reports, categorized by US and Foreign equities.
*   **Automated Reporting**: Exports formatted reports to a Google Sheet, creating dated worksheets for daily and weekly analyses.
*   **Secure API Key Management**: Utilizes Colab Secrets for securely storing API keys, avoiding hardcoding sensitive information.
*   **Service Account Authentication for Google Sheets**: Employs non-interactive service account authentication for `gspread`, suitable for automated workflows.

## Setup and Configuration

To run this notebook, you will need the following:

### 1. EODHD API Key

1.  **Obtain an API Key**: Get an API key from [EODHD.com](https://eodhd.com/). A free tier key should suffice for initial testing.
2.  **Add to Colab Secrets**: In Google Colab, go to the "🔑" icon on the left sidebar (Secrets Manager).
    *   Click `+ New secret`.
    *   Set `Name` to `EODHD_API_KEY`.
    *   Set `Value` to your actual EODHD API Key.
    *   Ensure `Notebook access` is toggled on.

### 2. Google Cloud Platform (GCP) Service Account for Google Sheets

For automated, non-interactive access to Google Sheets, a GCP Service Account is used.

1.  **Create a GCP Project**: If you don't have one, create a new project in the [Google Cloud Console](https://console.cloud.google.com/).
2.  **Enable Google Sheets API**: Navigate to "APIs & Services" > "Enabled APIs & Services" and ensure "Google Sheets API" and "Google Drive API" are enabled for your project.
3.  **Create a Service Account**: 
    *   Go to "IAM & Admin" > "Service Accounts".
    *   Click `+ CREATE SERVICE ACCOUNT`.
    *   Give it a `Service account name` (e.g., `sheets-writer`).
    *   Grant it the **'Google Sheets Editor'** role (or 'Editor' if you cannot find the Sheets-specific role, but be aware of the broader permissions).
    *   Click `Done`.
4.  **Generate a JSON Key**: 
    *   Find your newly created service account in the list.
    *   Under "Actions" (three dots), select `Manage keys`.
    *   Click `ADD KEY` > `Create new key`.
    *   Select `JSON` as the key type and click `CREATE`.
    *   A JSON file will be downloaded to your computer. **This file contains your private key and must be kept secure!**
5.  **Add to Colab Secrets**: 
    *   Open your downloaded JSON key file in a text editor.
    *   Copy the entire JSON content.
    *   In Colab Secrets Manager:
        *   Click `+ New secret`.
        *   Set `Name` to `GCS_SERVICE_ACCOUNT_KEY_JSON`.
        *   Set `Value` to the **entire JSON content** you copied.
        *   Ensure `Notebook access` is toggled on.

### 3. Share Your Google Sheet with the Service Account

Since the service account operates in its own isolated Google Drive environment, you must explicitly share the target Google Sheet with it.

1.  **Find your Service Account's Email**: Open the downloaded JSON key file and look for the `client_email` field (e.g., `your-service-account-name@your-project-id.iam.gserviceaccount.com`).
2.  **Create the Target Google Sheet**: Go to [Google Sheets](https://sheets.google.com/) and create a new blank spreadsheet. Name it `Stock Market Movers Report` (or the exact name used in the `spreadsheet_name` variable in the notebook).
3.  **Share the Sheet**: Open the `Stock Market Movers Report` spreadsheet. Click the `Share` button.
    *   Paste the `client_email` of your service account into the "Share with people and groups" field.
    *   Grant it **'Editor'** access.
    *   Click `Send`.

## Running the Notebook

1.  **Open in Colab**: Open this `.ipynb` file in Google Colab.
2.  **Install Dependencies**: The notebook includes cells to install necessary libraries like `gspread` and `requests`.
3.  **Execute Cells Sequentially**: Run all cells in the notebook from top to bottom. The notebook is designed to fetch data, process it, and then export the reports to the specified Google Sheet.

## Output

Upon successful execution, a Google Sheet named `Stock Market Movers Report` will be updated (or created if it doesn't exist) with new worksheets:

*   **`YYYY-MM-DD (30D Movers)`**: Contains daily top 25 gainers and losers based on 30-day price changes for both US and Foreign equities.
*   **`Week of YYYY-MM-DD (90D Movers)`**: (Runs only on Fridays) Contains weekly top 25 gainers and losers based on 90-day price changes.
*   **`Week of YYYY-MM-DD (360D Movers)`**: (Runs only on Fridays) Contains weekly top 25 gainers and losers based on 360-day price changes.

Older daily/weekly report sheets will be hidden to keep the spreadsheet organized.