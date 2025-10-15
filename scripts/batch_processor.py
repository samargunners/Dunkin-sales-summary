#!/usr/bin/env python3
"""
Batch process Dunkin sales reports for multiple dates.
This script helps process data day by day from a start date to end date.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import time
import re
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))

# Import the compilation functions directly from compile_store_reports
from compile_store_reports import (
    process_one_input, log, norm,
    is_labor, is_order_type, is_daypart, is_subcat, is_tender, is_sales_summary,
    flatten_labor_file, flatten_menu_mix_file, flatten_sales_by_daypart_file,
    flatten_sales_by_subcategory_file, flatten_tender_type_file, flatten_sales_summary_horizontal
)
from load_to_sqlite import load_to_supabase

def parse_date_from_filename(filename):
    """
    Parse date from Dunkin filename format:
    Example: "0 Consolidated Dunkin Sales Summary v2_Sales ... 2025-10-01 to 2025-10-01_20251015T0227.xlsx"
    Returns the date as YYYY-MM-DD string, or None if not found
    """
    # Look for pattern: YYYY-MM-DD to YYYY-MM-DD
    pattern = r'(\d{4}-\d{2}-\d{2}) to (\d{4}-\d{2}-\d{2})'
    match = re.search(pattern, str(filename))
    
    if match:
        start_date = match.group(1)
        end_date = match.group(2)
        # For daily reports, start and end should be the same
        if start_date == end_date:
            return start_date
        else:
            # If different, use the start date
            return start_date
    
    return None

def scan_downloaded_files():
    """
    Scan the raw_emails directory for downloaded files and group them by date
    Returns a dictionary: {date: [list of files for that date]}
    """
    data_dir = Path("data/raw_emails")
    files_by_date = defaultdict(list)
    
    # Look for Excel files in raw_emails directory
    excel_files = list(data_dir.glob("*.xlsx"))
    
    print(f"📁 Found {len(excel_files)} Excel files in /data/raw_emails directory")
    
    for file in excel_files:
        # Skip compiled files
        if "_copy" in file.name:
            continue
            
        date = parse_date_from_filename(file.name)
        if date:
            files_by_date[date].append(file)
            print(f"   📅 {date}: {file.name}")
        else:
            print(f"   ⚠️  Could not parse date from: {file.name}")
    
    return dict(files_by_date)

def validate_files_for_date(files):
    """
    Validate that we have all required report types for a date
    Returns (is_complete, missing_types)
    """
    required_types = [
        "Labor Hours",
        "Sales by Daypart", 
        "Sales by Subcategory",
        "Tender Type",
        "Sales Mix Detail",
        "Menu Mix Metrics"
    ]
    
    found_types = []
    for file in files:
        filename = file.name
        for report_type in required_types:
            if report_type in filename:
                found_types.append(report_type)
                break
    
    missing_types = [t for t in required_types if t not in found_types]
    is_complete = len(missing_types) == 0
    
    return is_complete, missing_types

def generate_date_range(start_date, end_date):
    """Generate list of dates between start and end date"""
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    dates = []
    current = start
    while current <= end:
        dates.append(current.strftime('%Y-%m-%d'))
        current += timedelta(days=1)
    
    return dates

def process_single_date(date_str, files=None):
    """Process data for a single date using the same workflow as compile_store_reports.py"""
    print(f"\n🗓️  Processing date: {date_str}")
    print("=" * 50)
    
    if files:
        # Files already identified for this specific date
        date_files = files
        is_complete, missing_types = validate_files_for_date(date_files)
        
        print(f"📁 Found {len(date_files)} files for {date_str}:")
        for file in date_files:
            print(f"   - {file.name}")
        
        if not is_complete:
            print(f"   ⚠️  Missing report types: {', '.join(missing_types)}")
            proceed = input("   🤔 Continue anyway? (y/n): ").lower()
            if proceed not in ['y', 'yes']:
                return False
    else:
        # Scan for files for this specific date
        files_by_date = scan_downloaded_files()
        if date_str not in files_by_date:
            print(f"   ❌ No files found for {date_str}")
            return False
        
        date_files = files_by_date[date_str]
        is_complete, missing_types = validate_files_for_date(date_files)
        
        print(f"📁 Found {len(date_files)} files for {date_str}:")
        for file in date_files:
            print(f"   - {file.name}")
        
        if not is_complete:
            print(f"   ⚠️  Missing report types: {', '.join(missing_types)}")
            return False
    
    # Step 2: Process each file using compile_store_reports functions
    print(f"\n⚙️  STEP 2: Compiling reports for {date_str}")
    
    successful_files = 0
    failed_files = 0
    
    # Filter to only non-copy files for this date
    files_to_process = [f for f in date_files if not f.name.endswith("_copy.xlsx")]
    
    print(f"   📂 Processing {len(files_to_process)} files...")
    
    for file_path in files_to_process:
        print(f"   🔄 Processing: {file_path.name}")
        try:
            if process_one_input(file_path):
                successful_files += 1
                print(f"      ✅ Success")
            else:
                failed_files += 1
                print(f"      ❌ Failed: No matching transformer")
        except Exception as e:
            failed_files += 1
            print(f"      ❌ Failed: {e}")
    
    print(f"   📊 Compilation Results: ✅ {successful_files} success, ❌ {failed_files} failed")
    
    if successful_files == 0:
        print(f"   ❌ No files successfully compiled for {date_str}")
        return False
    
    # Step 3: Upload compiled files to Supabase
    print(f"\n📤 STEP 3: Uploading compiled files to Supabase for {date_str}")
    
    try:
        # Call the upload function directly
        load_to_supabase()
        print(f"   ✅ Upload successful for {date_str}")
    except Exception as e:
        print(f"   ❌ Upload failed for {date_str}: {e}")
        return False
    
    print(f"\n🎉 Successfully processed {date_str}!")
    return True

def batch_process_dates(start_date, end_date):
    """Process multiple dates in sequence"""
    dates = generate_date_range(start_date, end_date)
    
    print(f"🚀 BATCH PROCESSING: {start_date} to {end_date}")
    print(f"📅 Total dates to process: {len(dates)}")
    print(f"📋 Dates: {', '.join(dates)}")
    
    # Confirm before starting
    response = input(f"\n🤔 Process all {len(dates)} dates? (y/n): ").lower()
    if response not in ['y', 'yes']:
        print("❌ Batch processing cancelled.")
        return
    
    # Process each date
    successful = 0
    failed = 0
    failed_dates = []
    
    for i, date_str in enumerate(dates, 1):
        print(f"\n📈 PROGRESS: {i}/{len(dates)} dates")
        
        if process_single_date(date_str):
            successful += 1
        else:
            failed += 1
            failed_dates.append(date_str)
            
            # Ask if user wants to continue after failure
            if failed_dates:
                continue_process = input(f"\n⚠️  Failed to process {date_str}. Continue with next date? (y/n): ").lower()
                if continue_process not in ['y', 'yes']:
                    break
    
    # Summary
    print(f"\n📊 BATCH PROCESSING SUMMARY:")
    print(f"   ✅ Successful: {successful} dates")
    print(f"   ❌ Failed: {failed} dates")
    if failed_dates:
        print(f"   📋 Failed dates: {', '.join(failed_dates)}")
    print(f"   📁 Total processed: {successful + failed}")

def process_auto_detected_files():
    """Process all auto-detected files from /data directory"""
    files_by_date = scan_downloaded_files()
    
    if not files_by_date:
        print("❌ No files with recognizable dates found in /data directory")
        return
    
    print(f"\n📋 AUTO-DETECTED FILES BY DATE:")
    print("=" * 40)
    
    complete_dates = []
    incomplete_dates = []
    
    for date in sorted(files_by_date.keys()):
        files = files_by_date[date]
        is_complete, missing_types = validate_files_for_date(files)
        
        print(f"\n📅 {date} ({len(files)} files):")
        for file in files:
            print(f"   ✅ {file.name}")
        
        if is_complete:
            print("   ✅ Complete set (all 6 report types)")
            complete_dates.append(date)
        else:
            print(f"   ⚠️  Missing: {', '.join(missing_types)}")
            incomplete_dates.append(date)
    
    print(f"\n📊 SUMMARY:")
    print(f"   ✅ Complete dates: {len(complete_dates)}")
    print(f"   ⚠️  Incomplete dates: {len(incomplete_dates)}")
    
    if complete_dates:
        print(f"\n🎯 Ready to process: {', '.join(complete_dates)}")
        print(f"\n🚀 Starting automatic processing of {len(complete_dates)} complete dates...")
        
        successful = 0
        failed = 0
        failed_dates = []
        
        for i, date in enumerate(complete_dates, 1):
            print(f"\n📅 [{i}/{len(complete_dates)}] Processing {date}...")
            files = files_by_date[date]
            
            if process_single_date(date, files):
                successful += 1
                print(f"   ✅ {date} completed successfully")
            else:
                failed += 1
                failed_dates.append(date)
                print(f"   ❌ {date} failed")
        
        print(f"\n📈 BATCH PROCESSING COMPLETE:")
        print(f"   ✅ Successful: {successful} dates")
        print(f"   ❌ Failed: {failed} dates")
        if failed_dates:
            print(f"   � Failed dates: {', '.join(failed_dates)}")
        print(f"   📁 Total processed: {successful + failed}")
        
        return successful > 0
    
    if incomplete_dates:
        print(f"\n⚠️  Incomplete dates need more files: {', '.join(incomplete_dates)}")

def interactive_mode():
    """Interactive mode for selecting dates and processing"""
    print("🎯 DUNKIN SALES DATA BATCH PROCESSOR")
    print("=" * 50)
    
    while True:
        print("\nOptions:")
        print("1. Auto-detect and process downloaded files")
        print("2. Process single date (manual)")
        print("3. Process date range (manual batch)")
        print("4. Show current database status")
        print("5. Scan downloaded files (preview only)")
        print("6. Exit")
        
        choice = input("\n🔢 Select option (1-6): ").strip()
        
        if choice == "1":
            process_auto_detected_files()
        
        elif choice == "2":
            date_str = input("📅 Enter date (YYYY-MM-DD): ").strip()
            try:
                # Validate date format
                datetime.strptime(date_str, '%Y-%m-%d')
                process_single_date(date_str)
            except ValueError:
                print("❌ Invalid date format. Use YYYY-MM-DD")
        
        elif choice == "3":
            start_date = input("📅 Start date (YYYY-MM-DD): ").strip()
            end_date = input("📅 End date (YYYY-MM-DD): ").strip()
            
            try:
                # Validate dates
                datetime.strptime(start_date, '%Y-%m-%d')
                datetime.strptime(end_date, '%Y-%m-%d')
                batch_process_dates(start_date, end_date)
            except ValueError:
                print("❌ Invalid date format. Use YYYY-MM-DD")
        
        elif choice == "4":
            print("\n📊 Checking database status...")
            os.system("python3 -c \"import sys; sys.path.append('.'); from dashboard.utils import supabase_db; conn = supabase_db.get_supabase_connection(); cur = conn.cursor(); cur.execute('SELECT MAX(date) FROM sales_summary'); print(f'Latest data: {cur.fetchone()[0]}'); conn.close()\"")
        
        elif choice == "5":
            files_by_date = scan_downloaded_files()
            if files_by_date:
                print(f"\n📋 Preview of downloaded files:")
                for date in sorted(files_by_date.keys()):
                    files = files_by_date[date]
                    is_complete, missing = validate_files_for_date(files)
                    status = "✅ Complete" if is_complete else f"⚠️ Missing: {len(missing)} types"
                    print(f"   {date}: {len(files)} files ({status})")
        
        elif choice == "6":
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid option. Please select 1-6.")

def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        # Command line mode
        if len(sys.argv) == 2:
            # Single date
            date_str = sys.argv[1]
            process_single_date(date_str)
        elif len(sys.argv) == 3:
            # Date range
            start_date = sys.argv[1]
            end_date = sys.argv[2]
            batch_process_dates(start_date, end_date)
        else:
            print("Usage:")
            print("  Single date: python3 batch_processor.py 2025-09-13")
            print("  Date range:  python3 batch_processor.py 2025-09-13 2025-10-12")
            print("  Auto-process: python3 batch_processor.py")
    else:
        # Auto-process mode: automatically detect and process all files
        print("🚀 DUNKIN BATCH PROCESSOR - AUTO MODE")
        print("=" * 50)
        process_auto_detected_files()

if __name__ == "__main__":
    main()