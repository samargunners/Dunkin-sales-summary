# Guest Comments Feature - Setup & Usage Guide

## Overview
This feature allows you to track and analyze customer feedback from Medallia "Daily Guest Comments Summary" emails.

## Components Created

### 1. Database Schema
**File:** `db/guest_comments_schema.sql`
- Creates `medallia_reports` table with all necessary fields
- Includes unique constraint to prevent duplicates: `(pc_number, response_datetime, comment)`
- Indexes for performance on common queries

### 2. Email Download Script
**File:** `scripts/download_medallia_emails.py`
- Downloads Medallia emails from Gmail
- Searches for subject "Daily Guest Comments Summary"
- Saves raw email content to `data/raw_emails/medallia/`

### 3. Data Processing Script
**File:** `scripts/process_medallia_data.py`
- Parses downloaded emails using the provided parsing function
- Extracts: store info, scores (OSAT, LTR), accuracy, comments
- Uploads to Supabase with duplicate handling

### 4. Pipeline Runner
**File:** `scripts/run_medallia_pipeline.py`
- One-command solution to download and process data

### 5. Streamlit Page
**File:** `dashboard/pages/9_Guest_Reviews.py`
- Interactive dashboard for viewing and analyzing reviews
- Filters by date, store, scores, accuracy, channel
- Charts: OSAT/LTR distributions, trends over time, store comparisons
- Individual review cards with sentiment indicators

## Setup Instructions

### Step 1: Create Database Table
Run the SQL schema to create the table:
```bash
# Using psql
psql <your_supabase_connection_string> < db/guest_comments_schema.sql

# Or if you have a connection script
python -c "from dashboard.utils.supabase_db import get_supabase_connection; conn = get_supabase_connection(); cursor = conn.cursor(); cursor.execute(open('db/guest_comments_schema.sql').read()); conn.commit()"
```

### Step 2: Configure Gmail Access
Ensure your `.env` file has:
```
EMAIL_USER=your_email@gmail.com
EMAIL_PASS=your_app_password
```

### Step 3: Download & Process Data

**Option A - Full Pipeline (Recommended):**
```bash
# Download emails from last 7 days and process
python scripts/run_medallia_pipeline.py

# Or specify custom days
python scripts/run_medallia_pipeline.py --days 30
```

**Option B - Step by Step:**
```bash
# 1. Download emails
python scripts/download_medallia_emails.py --days 7

# 2. Process and upload
python scripts/process_medallia_data.py
```

### Step 4: View in Streamlit
```bash
streamlit run dashboard/app.py
```
Navigate to **"9_Guest_Reviews"** page in the sidebar.

## Usage

### Daily Workflow
Add to your daily routine:
```bash
python scripts/run_medallia_pipeline.py
```

### Features Available

**Metrics:**
- Total reviews
- Average OSAT (1-5 scale)
- Average LTR (0-10 scale)  
- Accuracy rate percentage
- Promoters percentage (LTR >= 9)

**Visualizations:**
- OSAT & LTR score distributions
- Scores over time (trend lines)
- Store comparison charts

**Filters:**
- Date range selection
- Store selection
- Minimum OSAT/LTR scores
- Accuracy filter (Yes/No)
- Order channel filter (In-store/Other)

**Review Views:**
- All reviews
- Positive reviews (OSAT 4-5, LTR 7-10)
- Negative reviews (OSAT 1-2, LTR 0-5)
- Order accuracy issues only

**Export:**
- Download filtered reviews as CSV
- View summary statistics

## Data Structure

```
medallia_reports table:
├── id (primary key)
├── report_date (date of Medallia report)
├── pc_number (store number)
├── restaurant_address
├── order_channel (In-store/Other)
├── transaction_datetime
├── response_datetime
├── osat (1-5 score)
├── ltr (0-10 score)
├── accuracy (Yes/No)
├── comment (customer text)
└── created_at (timestamp)
```

## Troubleshooting

**No data showing:**
1. Check if table exists: `SELECT COUNT(*) FROM medallia_reports;`
2. Verify emails downloaded: `ls data/raw_emails/medallia/`
3. Check processing logs for errors

**Duplicates:**
- System automatically skips duplicates based on `(pc_number, response_datetime, comment)`

**Email parsing errors:**
- Check email format matches expected structure
- Review parsing function in `process_medallia_data.py`

## Maintenance

**Bulk reload:**
```bash
# Delete old data
# Then reprocess all files
python scripts/process_medallia_data.py
```

**Process single file:**
```bash
python scripts/process_medallia_data.py --file data/raw_emails/medallia/medallia_2026-02-04.txt
```
