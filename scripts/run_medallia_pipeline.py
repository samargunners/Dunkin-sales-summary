#!/usr/bin/env python3
"""
Complete pipeline script for Medallia Guest Comments
Downloads emails, processes data, and uploads to Supabase
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Run complete Medallia pipeline")
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to look back for emails (default: 7)"
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip email download, only process existing files"
    )
    
    args = parser.parse_args()
    
    print("="*80)
    print("MEDALLIA GUEST COMMENTS PIPELINE")
    print("="*80)
    
    # Step 1: Download emails
    if not args.skip_download:
        print("\n[1/2] Downloading Medallia emails from Gmail...")
        from scripts.download_medallia_emails import download_medallia_emails
        
        try:
            files = download_medallia_emails(days_back=args.days)
            if not files:
                print("No new emails downloaded")
                return 1
        except Exception as e:
            print(f"Error downloading emails: {e}")
            return 1
    else:
        print("\n[1/2] Skipping email download (--skip-download flag)")
    
    # Step 2: Process and upload
    print("\n[2/2] Processing data and uploading to Supabase...")
    from scripts.process_medallia_data import process_all_medallia_files
    
    try:
        result = process_all_medallia_files()
        if result != 0:
            print("Error processing data")
            return result
    except Exception as e:
        print(f"Error processing data: {e}")
        return 1
    
    print("\n" + "="*80)
    print("✓ PIPELINE COMPLETED SUCCESSFULLY")
    print("="*80)
    print("\nNext steps:")
    print("1. View in Streamlit: streamlit run dashboard/app.py")
    print("2. Navigate to 'Guest Reviews' page")
    
    return 0


if __name__ == "__main__":
    exit(main())
