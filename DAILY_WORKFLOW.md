# 🚀 Daily Data Processing Workflow

## Quick Start Options

### Option 1: Interactive Mode (Recommended for beginners)
```bash
cd /path/to/Dunkin-Sales-Summary
python3 scripts/batch_processor.py
```
Then follow the menu prompts.

### Option 2: Command Line (For specific dates)
```bash
# Process single date
python3 scripts/batch_processor.py 2025-09-13

# Process date range  
python3 scripts/batch_processor.py 2025-09-13 2025-10-12
```

## 📋 Step-by-Step Process for Each Day

### What You Need to Do:
1. **Download Data** (Manual step)
   - Go to your Dunkin data source
   - Download all 6 report types for the target date:
     - Labor Hours
     - Sales by Daypart  
     - Sales by Subcategory
     - Tender Type
     - Sales Mix Detail (Sales Summary)
     - Menu Mix Metrics (Order Type)
   - Save files in `/data` directory

2. **Run Processor** (Automated)
   - Script compiles all reports
   - Script uploads to Supabase  
   - Script checks for duplicates

### What the Script Does Automatically:
✅ Compiles all 6 report types
✅ Formats data to match database schema
✅ Uploads to Supabase with duplicate protection  
✅ Provides progress feedback
✅ Handles errors gracefully

## 🗓️ Suggested Schedule for Missing Dates

### Target: September 13 - October 12 (30 days)

**Week 1 (Sep 13-19)**: Process 7 days
**Week 2 (Sep 20-26)**: Process 7 days  
**Week 3 (Sep 27-Oct 3)**: Process 7 days
**Week 4 (Oct 4-10)**: Process 7 days
**Week 5 (Oct 11-12)**: Process 2 days

### Time Estimate:
- **Per day**: ~5-10 minutes (3 min download + 2-7 min processing)
- **Total**: ~2.5-5 hours spread over several sessions

## 🛡️ Error Handling

The script includes:
- ✅ Duplicate detection and prevention
- ✅ File validation before processing
- ✅ Database connection error handling  
- ✅ Option to retry failed dates
- ✅ Progress tracking and summaries

## 📊 Monitoring Progress

Check your current database status:
```bash
python3 scripts/batch_processor.py
# Select option 3: "Show current database status"
```

## 🔧 Troubleshooting

**If compilation fails:**
- Check that all 6 report files are downloaded
- Verify file names contain the correct date
- Ensure files are in Excel format

**If upload fails:**  
- Check Supabase connection in `.streamlit/secrets.toml`
- Verify internet connection
- Check for any database constraint errors

**If duplicates are detected:**
- Run the cleanup script: `python3 scripts/cleanup_duplicates.py`
- The batch processor will skip dates that already exist