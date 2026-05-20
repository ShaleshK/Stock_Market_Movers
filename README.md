# 📈 Automated Stock Market Movers Pipeline

An enterprise-grade, object-oriented data engineering pipeline that automatically extracts global financial data arrays, filters for large-cap assets, tracks mathematical price momentum, and deploys dated reporting sheets to Google Workspace.

## ⚙️ Core Architecture & Features
- **Data Engineering Module (`src/data_extractor.py`)**: Connects to the EODHD API to ingest bulk fundamental financial matrices, dynamically filtering out assets with a market capitalization below \$1 Billion.
- **Vector Transformation Module (`src/transformer.py`)**: Computes multi-window chronological price array modifications across trailing 30, 90, and 360-day blocks.
- **Enterprise Report Writer (`src/sheets_writer.py`)**: Authenticates non-interactively via a Google Cloud Platform (GCP) Service Account key string to write, format, and manage worksheet tabs.
- **Master Orchestrator (`main.py`)**: A structured pipeline entry point that handles variable injection safety gates and coordinates execution.

## 🚀 Cloud Automation Framework (GitHub Actions)
This project operates as a fully autonomous, serverless pipeline using **GitHub Actions workflow containers**. 
- **The Engine Schedulers**: Configured with an automated `cron` expression matrix to awaken, install virtual dependencies, ingest credentials from encrypted GitHub Secrets, and run the pipeline completely in the cloud.
- **The Routine Sync**: Fires automatically at **1:00 PM UTC (8:00 AM Central Time) Monday through Friday**, delivering data to stakeholders before market open without requiring local machine compute.

## 🛠️ Local Execution Checklist
1. Clone this repository to your environment.
2. Install modern dependencies inside a Python 3.11 playground:
   ```bash
   pip install -r requirements.txt
   ```
3. Establish your localized security files:
   - Create a root `.env` file containing your `EODHD_API_KEY`.
   - Place your Google keys in an isolated `service_account.json` file (automatically masked by `.gitignore`).
4. Execute the master production script:
   ```bash
   python main.py
   ```