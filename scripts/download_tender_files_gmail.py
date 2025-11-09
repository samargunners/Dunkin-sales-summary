"""
Download Tender Type files from Gmail for missing dates

This script downloads "Consolidated Dunkin Sales Summary_Tender Type" Excel files
from Gmail for dates starting October 19, 2025 onwards (where we have missing tender data).
"""

import os
import sys
import imaplib
import email
from email.header import decode_header
from datetime import datetime, timedelta
import re

# Email credentials (same as download_from_gmail.py)
IMAP_SERVER = "imap.gmail.com"
EMAIL = "dunkinsamar@gmail.com"
PASSWORD = "huyoqtzoaztqdgzw"

def download_tender_type_files(start_date='2025-10-19'):
    """Download tender type files from Gmail starting from the specified date."""
    
    print("=" * 80)
    print("Gmail Tender Type File Downloader")
    print("=" * 80)
    print()
    
    # Create download directory
    download_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                'data', 'tender_downloads')
    os.makedirs(download_dir, exist_ok=True)
    print(f"📁 Download directory: {download_dir}")
    print()
    
    # Connect to Gmail via IMAP
    print("🔐 Connecting to Gmail...")
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, PASSWORD)
        mail.select("inbox")
        print("✓ Connected successfully")
        print()
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return
    
    # Search for emails with the subject
    subject = "Consolidated Dunkin Sales Summary v2"
    
    # Convert start_date to IMAP date format
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    imap_date = start_dt.strftime('%d-%b-%Y')
    
    print(f"🔍 Searching for emails...")
    print(f"   Subject: {subject}")
    print(f"   After date: {start_date}")
    print()
    
    try:
        # Search for emails with subject since the start date
        status, messages = mail.search(None, f'(SUBJECT "{subject}" SINCE {imap_date})')
        
        if status != "OK":
            print("❌ Search failed")
            return
        
        email_ids = messages[0].split()
        
        if not email_ids:
            print("❌ No emails found matching the criteria")
            return
        
        print(f"✓ Found {len(email_ids)} email(s)")
        print()
        
        downloaded_files = []
        
        for idx, email_id in enumerate(email_ids, 1):
            # Fetch the email
            status, msg_data = mail.fetch(email_id, "(RFC822)")
            
            if status != "OK":
                continue
            
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    # Get email date
                    email_date = msg.get("Date", "Unknown")
                    subject_line = msg.get("Subject", "")
                    
                    print(f"📧 Email {idx}/{len(email_ids)}")
                    print(f"   Subject: {subject_line}")
                    print(f"   Date: {email_date}")
                    
                    # Process attachments
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_disposition = str(part.get("Content-Disposition", ""))
                            
                            if "attachment" in content_disposition:
                                filename = part.get_filename()
                                
                                if filename:
                                    # Decode filename if needed
                                    if isinstance(filename, bytes):
                                        filename = filename.decode('utf-8', errors='replace')
                                    
                                    # Check if it's a tender type file
                                    if filename.startswith('Consolidated Dunkin Sales Summary_Tender Type') and filename.endswith('.xlsx'):
                                        print(f"   📎 Attachment: {filename}")
                                        
                                        # Extract date from filename using regex
                                        date_match = re.search(r'(\d{4}-\d{2}-\d{2}) to (\d{4}-\d{2}-\d{2})', filename)
                                        if date_match:
                                            file_start_date = date_match.group(1)
                                            file_end_date = date_match.group(2)
                                            print(f"   📅 Date range: {file_start_date} to {file_end_date}")
                                        
                                        # Download attachment
                                        filepath = os.path.join(download_dir, filename)
                                        
                                        with open(filepath, 'wb') as f:
                                            f.write(part.get_payload(decode=True))
                                        
                                        print(f"   ✓ Downloaded to: {filepath}")
                                        downloaded_files.append({
                                            'filename': filename,
                                            'filepath': filepath,
                                            'start_date': file_start_date if date_match else 'Unknown',
                                            'end_date': file_end_date if date_match else 'Unknown',
                                            'email_date': email_date
                                        })
            print()
        
        mail.close()
        mail.logout()
        
        # Summary
        print("=" * 80)
        print("DOWNLOAD SUMMARY")
        print("=" * 80)
        print(f"\n✓ Total files downloaded: {len(downloaded_files)}")
        
        if downloaded_files:
            print("\n📋 Downloaded Files:")
            print("-" * 80)
            for i, file_info in enumerate(downloaded_files, 1):
                print(f"\n{i}. {file_info['filename']}")
                print(f"   Date Range: {file_info['start_date']} to {file_info['end_date']}")
                print(f"   Email Date: {file_info['email_date']}")
                print(f"   Location: {file_info['filepath']}")
            
            # List date ranges
            print("\n" + "=" * 80)
            print("DATE COVERAGE")
            print("=" * 80)
            dates = sorted(set([f['start_date'] for f in downloaded_files if f['start_date'] != 'Unknown']))
            if dates:
                print(f"\nDownloaded tender data for dates: {dates[0]} to {dates[-1]}")
                print(f"Total unique dates covered: {len(dates)}")
                print(f"\nDates list:")
                for date in dates:
                    print(f"  - {date}")
            
        print("\n" + "=" * 80)
        print("✓ Download complete!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        mail.close()
        mail.logout()



if __name__ == "__main__":
    # Start from October 17, 2025 (checking for missing dates)
    download_tender_type_files(start_date='2025-10-17')
