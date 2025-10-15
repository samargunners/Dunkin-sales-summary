# 🚀 ENHANCED AUTO-DETECTION WORKFLOW

## ✨ NEW FEATURE: Automatic File Detection and Processing

Your batch processor now automatically detects downloaded files by parsing dates from filenames!

## 📋 Updated Workflow

### Step 1: Download Files (Manual - Once per Day/Session)
- Download all 6 report types for the dates you want to process
- Save them directly to the `/data` directory
- **No need to organize by date** - the script does this automatically!

### Step 2: Run Auto-Processing (Automated)
```bash
cd /path/to/Dunkin-Sales-Summary
python3 scripts/batch_processor.py
```
Select **Option 1: Auto-detect and process downloaded files**

## 🎯 Expected Filename Format
The script looks for this pattern in filenames:
```
*YYYY-MM-DD to YYYY-MM-DD*
```

Examples that work:
- ✅ `0 Consolidated Dunkin Sales Summary v2_Sales by Daypart 2025-10-01 to 2025-10-01_20251015T0227.xlsx`
- ✅ `Consolidated Dunkin Sales Summary v2_Labor Hours 2025-09-13 to 2025-09-13_20251014T1200.xlsx`
- ✅ `Sales Mix Detail 2025-10-12 to 2025-10-12_timestamp.xlsx`

## 🔍 What the Script Does Automatically

1. **Scans `/data` directory** for Excel files
2. **Parses dates** from filenames using regex pattern
3. **Groups files by date** automatically
4. **Validates completeness** - checks for all 6 report types per date
5. **Shows preview** of what will be processed
6. **Processes each complete date** in chronological order

## 📊 Complete Date Requirements

For each date, you need all 6 files:
- ✅ Labor Hours
- ✅ Sales by Daypart  
- ✅ Sales by Subcategory
- ✅ Tender Type
- ✅ Sales Mix Detail
- ✅ Menu Mix Metrics

## 🎯 Recommended Multi-Day Strategy

### Batch Download Strategy:
1. **Download 5-7 days worth** of files at once
2. **Save all to `/data`** directory (don't organize by folders)
3. **Run auto-processor** - it handles everything else!

### Example Session:
```bash
# Download files for Sep 13-19 (7 days × 6 files = 42 files)
# Save all 42 files to /data directory
# Run processor:
python3 scripts/batch_processor.py
# Select option 1
# Script processes all 7 days automatically!
```

## 🛡️ Safety Features

- ✅ **Duplicate prevention** - Won't reprocess existing dates
- ✅ **Validation checks** - Ensures all 6 files per date
- ✅ **Error recovery** - Option to retry failed dates
- ✅ **File cleanup** - Option to delete processed files
- ✅ **Progress tracking** - Shows success/failure counts

## 📈 Menu Options

1. **Auto-detect and process** (🌟 RECOMMENDED)
2. Process single date (manual)
3. Process date range (manual batch)  
4. Show database status
5. Scan files (preview only)
6. Exit

## ⚡ Speed Improvements

**Old workflow per date:**
- Download 6 files → Organize → Run compile → Run upload → Cleanup
- ~10 minutes per date

**New workflow per session:**
- Download 42 files for 7 dates → Run auto-processor once
- ~5-10 minutes for 7 dates!

## 🎉 Benefits

- 🚀 **7x faster** for multi-day processing
- 🤖 **Fully automated** after download
- 🛡️ **Error resistant** with validation
- 📊 **Progress tracking** and reporting
- 🧹 **Smart cleanup** options