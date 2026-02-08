# Dunkin Sales Summary - Project Overview

## Purpose
This project automates daily data collection, transformation, and reporting for Dunkin operations. It covers three pipelines:
- Sales reports (daily POS exports)
- HME drive-thru metrics (email-based reports)
- Medallia guest comments (email-based surveys)

The output lands in Supabase for reporting and in a Streamlit dashboard for analysis.

## Quick Start (Ops)
1. Ensure credentials are configured in `.env` and `.streamlit/secrets.toml`.
2. Run the pipelines (manual or scheduled):
   - Sales: `run_dunkin_pipeline.bat`
   - HME: `run_hme_pipeline.bat`
   - Medallia: `run_medallia_pipeline.bat`
3. Review logs in `logs/` for success or errors.

## Repository Layout (High Level)
- `scripts/` - Sales and Medallia pipeline code and utilities
- `data/` - Raw downloads, intermediate files, and HME pipeline assets
- `db/` - Database schema and SQL utilities
- `dashboard/` - Streamlit dashboard application
- `logs/` - Pipeline logs
- `exports/` - Generated outputs (PDFs, exports)

## Pipelines

### 1) Sales Pipeline
Primary goal: compile six daily reports into a normalized structure and upload to Supabase.

Key scripts:
- `scripts/download_from_gmail.py` - fetches sales emails/files
- `scripts/compile_store_reports.py` - transforms and normalizes reports
- `scripts/load_to_sqlite.py` - uploads to Supabase (despite name)
- `scripts/run_pipeline.py` - orchestrates download, compile, load
- `scripts/batch_processor.py` - interactive/batch processing with auto-detect

Run options:
- One-click: `run_dunkin_pipeline.bat`
- CLI: `python scripts/run_pipeline.py`
- Interactive/batch: `python scripts/batch_processor.py`

Input requirements (six report types per date):
- Labor Hours
- Sales by Daypart
- Sales by Subcategory
- Tender Type
- Sales Mix Detail (Sales Summary)
- Menu Mix Metrics (Order Type)

### 2) HME Pipeline
Primary goal: download daily drive-thru performance reports, transform, and upload.

Key scripts:
- `data/hme/download_hme_gmail.py`
- `data/hme/transform_hme.py`
- `data/hme/upload_hme_to_supabase.py`
- `data/hme/run_hme_pipeline.py`

Run options:
- One-click: `run_hme_pipeline.bat`
- CLI: `python data/hme/run_hme_pipeline.py`

### 3) Medallia Pipeline
Primary goal: process daily guest comment emails and upload to `medallia_reports`.

Key scripts:
- `scripts/download_medallia_emails.py`
- `scripts/process_medallia_data.py`
- `scripts/run_medallia_pipeline.py`

Run options:
- One-click: `run_medallia_pipeline.bat`
- CLI: `python scripts/run_medallia_pipeline.py`

Notes:
- HTML and text formats are supported
- Duplicate protection is enforced by a unique constraint

## Dashboard
The Streamlit app lives in `dashboard/`.

Run:
```
streamlit run dashboard/app.py
```

Guest reviews are available under `dashboard/pages/9_Guest_Reviews.py`.

## Database
Key schema files live in `db/`. See `DATABASE_TABLES_REFERENCE.md` for table details.

Tables of interest:
- `hme_report`
- `medallia_reports`
- (Sales tables are created/managed by the sales pipeline)

## Configuration

### Environment Variables (.env)
Required for Gmail access and email notifications:
```
EMAIL_USER=your_email@gmail.com
EMAIL_PASS=your_gmail_app_password
```

### Supabase Secrets (.streamlit/secrets.toml)
```
[supabase]
host = "db.xxxxx.supabase.co"
port = 5432
database = "postgres"
user = "postgres"
password = "your_password"
```

## Dependencies
Python packages are listed in `requirements.txt`.

System packages for PDF rendering (Linux): see `packages.txt`.

## Logs and Outputs
- Sales: `logs/pipeline_YYYYMMDD.log`
- HME: `logs/hme_pipeline_YYYYMMDD.log`
- Medallia: `logs/medallia_pipeline_YYYYMMDD.log`

PDF and export artifacts are typically written under `exports/`.

## Daily Operations (Summary)
1. Download sales reports (six files per date) and place in `data/` or `data/raw_emails`.
2. Run sales pipeline via `run_dunkin_pipeline.bat` or `scripts/batch_processor.py`.
3. Run HME pipeline via `run_hme_pipeline.bat`.
4. Run Medallia pipeline via `run_medallia_pipeline.bat`.
5. Review logs for errors; check Supabase for new data.

For more detail:
- `DAILY_WORKFLOW.md`
- `ENHANCED_WORKFLOW.md`
- `DAILY_CHECKLIST.txt`

## Scheduling (Windows Task Scheduler)
Follow `TASK_SCHEDULER_SETUP_GUIDE.md` to run pipelines automatically.

Recommended daily schedule:
- 9:00 AM Sales
- 9:05 AM HME
- 9:10 AM Medallia

## Troubleshooting
- No new data in Supabase:
  - Check pipeline logs in `logs/`
  - Verify Supabase credentials in `.streamlit/secrets.toml`
- Gmail download fails:
  - Verify `.env` values and Gmail app password
- Duplicate data:
  - Pipelines use unique constraints; duplicates are skipped

## Additional Documentation
- `MEDALLIA_SETUP_GUIDE.md`
- `MEDALLIA_IMPLEMENTATION_DOCS.md`
- `MEDALLIA_PIPELINE_ENHANCEMENT.md`
- `DATABASE_TABLES_REFERENCE.md`
- `TASK_SCHEDULER_SETUP_GUIDE.md`
