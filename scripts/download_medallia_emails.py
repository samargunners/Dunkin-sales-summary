#!/usr/bin/env python3
"""
Download Medallia Daily Guest Comments emails from Gmail
Searches for emails with subject containing "Daily Guest Comments Summary"
"""

import imaplib
import email
from email.header import decode_header
import os
import datetime
import re
from pathlib import Path

# Load credentials from .env
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

IMAP_SERVER = "imap.gmail.com"
EMAIL = os.getenv("EMAIL_USER")
PASSWORD = os.getenv("EMAIL_PASS")

# Directory to save raw Medallia email content
SAVE_DIR = Path(__file__).parent.parent / "data" / "raw_emails" / "medallia"


def extract_report_date(subject):
    """
    Extract date from subject like:
    'Daily Guest Comments Summary 2026-02-04'
    """
    match = re.search(r'(\d{4}-\d{2}-\d{2})', subject)
    if match:
        return match.group(1)
    return datetime.datetime.now().strftime("%Y-%m-%d")


def get_email_text_body(msg):
    """Extract plain text body from email message"""
    body = ""
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            
            # Get plain text parts
            if content_type == "text/plain" and "attachment" not in content_disposition:
                try:
                    body = part.get_payload(decode=True).decode()
                    break
                except:
                    pass
    else:
        try:
            body = msg.get_payload(decode=True).decode()
        except:
            pass
    
    return body


def download_medallia_emails(days_back=7):
    """
    Download Medallia guest comments emails from the last N days
    
    Args:
        days_back: Number of days to look back for emails (default: 7)
    """
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"Connecting to Gmail as {EMAIL}...")
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL, PASSWORD)
    mail.select("inbox")
    
    # Calculate search date
    since_date = (datetime.datetime.now() - datetime.timedelta(days=days_back)).strftime("%d-%b-%Y")
    
    # Search for Medallia emails
    print(f"Searching for 'Daily Guest Comments Summary' emails since {since_date}...")
    result, data = mail.search(None, f'(SUBJECT "Daily Guest Comments Summary" SINCE {since_date})')
    
    email_ids = data[0].split()
    
    if not email_ids:
        print("No matching emails found.")
        mail.logout()
        return []
    
    print(f"Found {len(email_ids)} email(s)")
    downloaded_files = []
    
    for email_id in email_ids:
        res, msg_data = mail.fetch(email_id, "(RFC822)")
        if res != "OK":
            print(f"Failed to fetch email ID {email_id}")
            continue
        
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)
        
        # Get subject
        subject = decode_header(msg["Subject"])[0][0]
        if isinstance(subject, bytes):
            subject = subject.decode()
        
        # Get email date
        email_date = email.utils.parsedate_to_datetime(msg["Date"])
        
        # Extract report date from subject
        report_date = extract_report_date(subject)
        
        # Get email body
        body = get_email_text_body(msg)
        
        if not body.strip():
            print(f"Warning: Empty body for email dated {email_date}")
            continue
        
        # Save to file
        filename = f"medallia_{report_date}.txt"
        filepath = SAVE_DIR / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"Subject: {subject}\n")
            f.write(f"Date: {email_date}\n")
            f.write(f"Report Date: {report_date}\n")
            f.write(f"{'-' * 80}\n\n")
            f.write(body)
        
        print(f"✓ Saved: {filename}")
        downloaded_files.append(filepath)
    
    mail.logout()
    print(f"\nDownloaded {len(downloaded_files)} email(s) to {SAVE_DIR}")
    return downloaded_files


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Download Medallia guest comments emails from Gmail")
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to look back (default: 7)"
    )
    
    args = parser.parse_args()
    
    if not EMAIL or not PASSWORD:
        print("Error: EMAIL_USER and EMAIL_PASS must be set in .env file")
        return 1
    
    downloaded_files = download_medallia_emails(days_back=args.days)
    
    if downloaded_files:
        print("\nNext steps:")
        print("1. Review downloaded files in:", SAVE_DIR)
        print("2. Run: python scripts/process_medallia_data.py")
        return 0
    else:
        print("No files downloaded")
        return 1


if __name__ == "__main__":
    exit(main())
