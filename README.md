# 📈 Automated Global Stock Market Movers Pipeline

An enterprise-grade, serverless data engineering pipeline that automatically ingests daily market snapshots across 13 major international exchanges, filters for large-cap assets, and compiles global top 25 gainers and losers into a stylized side-by-side dashboard layout on Google Sheets.

## ⚙️ Core Architecture & Features
- **Data Aggregator Module (`src/data_extractor.py`)**: Connects securely to central EODHD API gateways to ingest bulk snapshot grids and extract isolated fundamental data points.
- **Unified Handshake Framework (`src/sheets_writer.py`)**: A platform-independent authentication module that utilizes a localized physical service file (`service_account.json`) when executing locally, or falls back to parsed environment string matrices when running in the cloud.
- **Master Production Orchestrator (`main.py`)**: The pipeline's command gateway. It downloads snapshots for all global listings simultaneously, separates domestic vs. foreign equities, splits tables vertically by asset class, and sets side-by-side vertical tables (Gainers on the left, Losers on the right).

## 🚀 Cloud Automation Framework (GitHub Actions)
This project operates as a fully autonomous, serverless cron architecture using **GitHub Actions workflow containers**.
- **The Schedulers**: Configured to initialize a clean Python 3.11 container environment, install explicit project dependencies, inject encrypted GitHub Repository Secrets, and run without using any local computing resources.
- **The Routine Sync**: Fires automatically at **1:00 PM UTC (8:00 AM Central Time) Monday through Friday**, processing over 80,000 global tickers and generating your reports before market open.

## 🛠️ Local Execution Checklist
1. Clone this repository to your environment workspace.
2. Activate your clean virtual environment and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Establish your localized security environment:
   - Create a root `.env` file containing your `EODHD_API_KEY`.
   - Place your Google Cloud account key file named exactly `service_account.json` in the root folder (automatically masked by `.gitignore`).
4. Execute the production orchestrator:
   ```bash
   python -B main.py
   ```

   ```