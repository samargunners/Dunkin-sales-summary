# Medallia Guest Comments Feature - Implementation Documentation

## 📋 Overview

This document describes the complete implementation of the Medallia Guest Comments feature for the Dunkin Sales Summary Dashboard. This feature allows you to download, process, and analyze customer feedback from Medallia "Daily Guest Comments Summary" emails.

**Implementation Date:** February 4, 2026  
**Status:** Code Complete - Database setup pending

---

## 🗂️ Files Created

### 1. Database Schema
**File:** `db/guest_comments_schema.sql`
- Creates `guest_comments` table with all necessary columns
- Unique constraint: `(restaurant_pc, response_datetime, comment)` to prevent duplicates
- Indexes for performance: report_date, restaurant_pc, response_datetime, osat, ltr
- Supports OSAT (1-5) and LTR (0-10) scoring with CHECK constraints

### 2. Email Download Script
**File:** `scripts/download_medallia_emails.py`
- Downloads Medallia emails from Gmail via IMAP
- Searches for subject: "Daily Guest Comments Summary"
- Saves raw email content to `data/raw_emails/medallia/`
- Filename format: `medallia_YYYY-MM-DD.txt`
- Configurable lookback period (default: 7 days)

### 3. Data Processing Script
**File:** `scripts/process_medallia_data.py`
- Parses downloaded email text files
- Extracts: PC number, address, order channel, datetime, scores, accuracy, comments
- Handles "Other" channel (no transaction datetime)
- Batch inserts into Supabase with duplicate handling
- Returns statistics: inserted count, duplicate count

### 4. Pipeline Runner
**File:** `scripts/run_medallia_pipeline.py`
- One-command solution to run full pipeline
- Downloads emails → Processes → Uploads to database
- Options: `--days N` (lookback period), `--skip-download` flag

### 5. Streamlit Dashboard Page
**File:** `dashboard/pages/9_Guest_Reviews.py`
- Interactive dashboard for viewing and analyzing reviews
- **Metrics:** Total reviews, Avg OSAT, Avg LTR, Accuracy rate, Promoters %
- **Charts:** 
  - OSAT/LTR score distributions (bar charts)
  - Scores over time (dual-axis line chart)
  - Store comparison chart
- **Filters:**
  - Date range selection
  - Store multiselect
  - Min OSAT/LTR sliders
  - Accuracy filter (Yes/No)
  - Order channel filter (In-store/Other)
- **Review Views:**
  - All reviews
  - Positive (OSAT 4-5, LTR 7-10)
  - Negative (OSAT 1-2, LTR 0-5)
  - Order accuracy issues
- **Features:**
  - Color-coded sentiment indicators
  - Review cards with full details
  - CSV export
  - Summary statistics

### 6. Database Setup Script
**File:** `scripts/setup_guest_comments_db.py`
- Python script to create the database table
- Reads and executes `guest_comments_schema.sql`
- Verifies table structure and indexes
- Provides confirmation and next steps

### 7. Connection Test Script
**File:** `scripts/test_supabase_connection.py`
- Diagnoses Supabase connection issues
- Shows configuration (masked password)
- Tests database connection
- Provides troubleshooting tips

### 8. Documentation
**File:** `MEDALLIA_SETUP_GUIDE.md`
- Complete setup and usage guide
- Step-by-step instructions
- Troubleshooting section
- Daily workflow recommendations

---

## 🏗️ Database Schema

```sql
CREATE TABLE guest_comments (
    id SERIAL PRIMARY KEY,
    report_date DATE NOT NULL,
    restaurant_pc VARCHAR(10) NOT NULL,
    restaurant_address TEXT,
    order_channel VARCHAR(20),
    transaction_datetime TIMESTAMP,
    response_datetime TIMESTAMP NOT NULL,
    osat INTEGER CHECK (osat >= 1 AND osat <= 5),
    ltr INTEGER CHECK (ltr >= 0 AND ltr <= 10),
    accuracy VARCHAR(10),
    comment TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT unique_guest_comment UNIQUE (restaurant_pc, response_datetime, comment)
);
```

**Indexes:**
- `idx_guest_comments_report_date`
- `idx_guest_comments_restaurant_pc`
- `idx_guest_comments_response_datetime`
- `idx_guest_comments_osat`
- `idx_guest_comments_ltr`

---

## 📦 Dependencies

### Python Packages Required
```txt
psycopg2-binary  # PostgreSQL adapter
python-dotenv    # Environment variable management
streamlit        # Dashboard framework
pandas           # Data manipulation
plotly           # Interactive charts
imaplib          # Email download (built-in)
email            # Email parsing (built-in)
beautifulsoup4   # HTML parsing (may be needed for email)
```

### Environment Variables Required
```bash
# .env file
EMAIL_USER=your_email@gmail.com
EMAIL_PASS=your_gmail_app_password
```

### Supabase Configuration
Location: `.streamlit/secrets.toml` or `~/.streamlit/secrets.toml`

```toml
[supabase]
host = "db.xxxxx.supabase.co"
port = 5432
database = "postgres"
user = "postgres"
password = "your_password"
```

---

## 🚀 Setup Instructions for New PC

### Step 1: Clone Repository
```bash
git clone <your-repo-url>
cd Dunkin-Sales-Summary
```

### Step 2: Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Mac/Linux
# OR
venv\Scripts\activate     # On Windows
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

**Note:** If packages are missing, install them manually:
```bash
pip install psycopg2-binary python-dotenv streamlit pandas plotly beautifulsoup4
```

### Step 4: Configure Environment
1. Create `.env` file in project root:
```bash
EMAIL_USER=your_email@gmail.com
EMAIL_PASS=your_gmail_app_password
```

2. Create `.streamlit/secrets.toml`:
```toml
[supabase]
host = "db.xxxxx.supabase.co"
port = 5432
database = "postgres"
user = "postgres"
password = "your_supabase_password"
```

**Gmail App Password:** https://myaccount.google.com/apppasswords

### Step 5: Test Supabase Connection
```bash
python scripts/test_supabase_connection.py
```

**If Supabase is paused:**
- Go to https://supabase.com/dashboard
- Open your project (it will wake up automatically)
- Wait 10-30 seconds, then retry

### Step 6: Create Database Table
```bash
python scripts/setup_guest_comments_db.py
```

This creates the `guest_comments` table with all necessary indexes.

### Step 7: Download & Process First Data
```bash
python scripts/run_medallia_pipeline.py --days 30
```

This will:
1. Download Medallia emails from last 30 days
2. Parse and upload to database
3. Show summary statistics

### Step 8: Launch Dashboard
```bash
streamlit run dashboard/app.py
```

Navigate to **"9_Guest Reviews"** page in the sidebar.

---

## 💻 Usage

### Daily Workflow

**Option A - Full Pipeline:**
```bash
python scripts/run_medallia_pipeline.py
```

**Option B - Manual Steps:**
```bash
# 1. Download emails
python scripts/download_medallia_emails.py --days 7

# 2. Process and upload
python scripts/process_medallia_data.py
```

### Process Single File
```bash
python scripts/process_medallia_data.py --file data/raw_emails/medallia/medallia_2026-02-04.txt
```

### Skip Download (Process Existing Files Only)
```bash
python scripts/run_medallia_pipeline.py --skip-download
```

---

## 📧 Email Format Expected

The scripts expect emails with subject: **"Daily Guest Comments Summary YYYY-MM-DD"**

**Email Body Format:**
```
343939 - 807 E Main St Mount Joy PA
2/3/26 12:00 PM
2/3/26 6:31 PM
5
10
Yes
Please tell us more about your visit
Customer comment text here...
Go to survey »
```

**Fields Parsed:**
1. Restaurant PC and Address
2. Transaction Date/Time (or "Other")
3. Response Date/Time
4. OSAT Score (1-5)
5. LTR Score (0-10)
6. Accuracy (Yes/No)
7. Comment text

---

## 🎨 Dashboard Features

### Metrics Display
- **Total Reviews:** Count of all reviews in selected period
- **Avg OSAT:** Average Overall Satisfaction (1-5 scale)
- **Avg LTR:** Average Likelihood to Return (0-10 scale)
- **Accuracy Rate:** Percentage of orders with accurate fulfillment
- **Promoters %:** Percentage with LTR ≥ 9

### Interactive Charts
1. **OSAT Distribution:** Bar chart showing count per score (1-5)
2. **LTR Distribution:** Bar chart showing count per score (0-10)
3. **Scores Over Time:** Dual-axis line chart tracking daily averages
4. **Store Comparison:** Bar chart comparing average OSAT by store

### Filters
- **Date Range:** Select start and end dates
- **Stores:** Multiselect from available PC numbers
- **Min OSAT:** Slider (1-5)
- **Min LTR:** Slider (0-10)
- **Accuracy:** Checkboxes for Yes/No
- **Order Channel:** Checkboxes for In-store/Other

### Review Display Modes
- **All Reviews:** Show everything
- **Positive:** OSAT 4-5, LTR 7-10
- **Negative:** OSAT 1-2, LTR 0-5
- **Accuracy Issues:** Orders with Accuracy = No

### Review Cards
Each review shows:
- Store PC and address
- Date and time
- Color-coded OSAT/LTR scores (🟢🟡🔴)
- Accuracy indicator (✅❌)
- Order channel
- Full customer comment

---

## 🔧 Troubleshooting

### Issue: Supabase Connection Failed
**Symptoms:** "could not translate host name" error

**Solutions:**
1. Check internet connection: `ping 8.8.8.8`
2. Wake up Supabase instance (free tier pauses)
3. Verify hostname in secrets.toml
4. Test connection: `python scripts/test_supabase_connection.py`

### Issue: Gmail Authentication Failed
**Symptoms:** "Username and Password not accepted"

**Solutions:**
1. Enable 2FA on Gmail account
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Use App Password (not regular password) in .env
4. Check EMAIL_USER and EMAIL_PASS in .env

### Issue: No Emails Downloaded
**Symptoms:** "No matching emails found"

**Solutions:**
1. Verify emails exist in inbox with correct subject
2. Increase lookback period: `--days 30`
3. Check search criteria in download script
4. Verify email hasn't moved to other folder

### Issue: Parsing Errors
**Symptoms:** "Warning: Failed to parse record at line X"

**Solutions:**
1. Check email format matches expected structure
2. Review raw email file in `data/raw_emails/medallia/`
3. Update parsing regex in `process_medallia_data.py` if format changed

### Issue: Duplicates Not Prevented
**Symptoms:** Duplicate reviews appearing

**Solutions:**
1. Verify unique constraint exists: `\d guest_comments` in psql
2. Check constraint columns match: (restaurant_pc, response_datetime, comment)
3. Re-create table with setup script

### Issue: Streamlit Page Not Showing
**Symptoms:** 9_Guest_Reviews page missing

**Solutions:**
1. Check file exists: `ls dashboard/pages/9_Guest_Reviews.py`
2. Restart Streamlit: Stop and run `streamlit run dashboard/app.py`
3. Check for Python syntax errors in page file

---

## 🔄 Git Sync Instructions

### Initial Commit (First PC)
```bash
git add db/guest_comments_schema.sql
git add scripts/download_medallia_emails.py
git add scripts/process_medallia_data.py
git add scripts/run_medallia_pipeline.py
git add scripts/setup_guest_comments_db.py
git add scripts/test_supabase_connection.py
git add dashboard/pages/9_Guest_Reviews.py
git add MEDALLIA_SETUP_GUIDE.md
git add MEDALLIA_IMPLEMENTATION_DOCS.md

git commit -m "Add Medallia Guest Comments feature

- Database schema with unique constraint
- Email download from Gmail
- Data processing and upload to Supabase
- Streamlit dashboard page with filters and charts
- Pipeline runner for automation
- Setup and test scripts
- Complete documentation"

git push origin main
```

### On New PC
```bash
git pull origin main

# Then follow "Setup Instructions for New PC" above
```

### Exclude from Git
Add to `.gitignore`:
```
.env
.streamlit/secrets.toml
data/raw_emails/medallia/
venv/
__pycache__/
*.pyc
```

---

## 📊 Data Flow Diagram

```
Gmail Inbox
    ↓ (download_medallia_emails.py)
data/raw_emails/medallia/
    ↓ (process_medallia_data.py)
Parsing & Validation
    ↓ (psycopg2)
Supabase - guest_comments table
    ↓ (SQL queries)
Streamlit Dashboard (9_Guest_Reviews.py)
    ↓
User Analytics & Export
```

---

## 🎯 Future Enhancements (Optional)

### Potential Improvements
1. **Email Notifications:** Alert on negative reviews (OSAT ≤ 2)
2. **Sentiment Analysis:** Use NLP to categorize comment sentiment
3. **Word Cloud:** Visualize common words in comments
4. **Trend Alerts:** Notify when scores drop below threshold
5. **Automated Reporting:** Daily/weekly summary emails
6. **Manager Dashboard:** Store-specific view for managers
7. **Response Tracking:** Track follow-up actions on negative reviews
8. **Integration:** Connect with POS or operational systems

---

## 📝 Code Maintenance Notes

### Key Functions

**Email Parser:** `scripts/process_medallia_data.py::parse_medallia_email()`
- Uses regex to match restaurant PC: `r"^(\d{6})\s*-\s*(.+)$"`
- Handles "Other" channel gracefully
- Collects comment lines until "Go to survey"

**Database Insert:** `scripts/process_medallia_data.py::insert_records()`
- Uses `execute_values()` for batch insert efficiency
- `ON CONFLICT DO NOTHING` prevents duplicates
- Returns inserted and duplicate counts

**Streamlit Filters:** `dashboard/pages/9_Guest_Reviews.py`
- Dynamic SQL with parameterized queries (prevents SQL injection)
- Uses `checkbox_multiselect` utility for store selection
- Plotly for interactive charts

### Important Variables
- `IMAP_SERVER`: Gmail IMAP endpoint
- `SAVE_DIR`: Where raw emails are stored
- Default lookback: 7 days
- Review display limit: 50 per page

### Testing Checklist
- [ ] Connection to Supabase works
- [ ] Email downloads successfully
- [ ] Parser handles all email formats
- [ ] Duplicates are prevented
- [ ] Dashboard loads without errors
- [ ] Filters work correctly
- [ ] Charts display properly
- [ ] CSV export works

---

## 🆘 Support & Contact

### Resources
- Supabase Dashboard: https://supabase.com/dashboard
- Gmail App Passwords: https://myaccount.google.com/apppasswords
- Streamlit Docs: https://docs.streamlit.io
- psycopg2 Docs: https://www.psycopg.org/docs/

### File Locations
- Scripts: `scripts/`
- Database schemas: `db/`
- Dashboard pages: `dashboard/pages/`
- Raw data: `data/raw_emails/medallia/`
- Configuration: `.env`, `.streamlit/secrets.toml`

---

## ✅ Implementation Checklist

### Completed ✓
- [x] Database schema created
- [x] Email download script implemented
- [x] Data processing script implemented
- [x] Pipeline runner script created
- [x] Streamlit dashboard page created
- [x] Setup script created
- [x] Connection test script created
- [x] Documentation written

### Pending (Per PC)
- [ ] Virtual environment setup
- [ ] Dependencies installed
- [ ] .env file configured
- [ ] Supabase secrets configured
- [ ] Database table created
- [ ] Initial data downloaded
- [ ] Dashboard tested

---

**Document Version:** 1.0  
**Last Updated:** February 4, 2026  
**Author:** GitHub Copilot  
**Project:** Dunkin Sales Summary Dashboard - Medallia Guest Comments Feature
