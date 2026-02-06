#!/usr/bin/env python3
"""
Bulk download Medallia Daily Guest Comments emails from Gmail.
Searches for emails with subject containing "Daily Guest Comments Summary"
within a provided date range (inclusive).
"""

import imaplib
import email
from email.header import decode_header
import os
import datetime
import re
from pathlib import Path

from dotenv import load_dotenv

# Load credentials from .env
load_dotenv(Path(__file__).parent.parent / ".env")

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
    match = re.search(r"(\d{4}-\d{2}-\d{2})", subject)
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

            if content_type == "text/plain" and "attachment" not in content_disposition:
                try:
                    body = part.get_payload(decode=True).decode()
                    break
                except Exception:
                    pass
    else:
        try:
            body = msg.get_payload(decode=True).decode()
        except Exception:
            pass

    return body


def download_medallia_emails_bulk(start_date, end_date):
    """
    Download Medallia guest comments emails within a date range.

    Args:
        start_date: YYYY-MM-DD string (inclusive)
        end_date: YYYY-MM-DD string (inclusive)
    """
    SAVE_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Connecting to Gmail as {EMAIL}...")
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL, PASSWORD)
    mail.select("inbox")

    start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    if end_dt < start_dt:
        print("Error: end date must be on or after start date")
        mail.logout()
        return []

    imap_start = start_dt.strftime("%d-%b-%Y")
    imap_end = (end_dt + datetime.timedelta(days=1)).strftime("%d-%b-%Y")

    print(
        "Searching for 'Daily Guest Comments Summary' emails "
        f"from {start_date} to {end_date}..."
    )
    result, data = mail.search(
        None,
        f'(SUBJECT "Daily Guest Comments Summary" SINCE {imap_start} BEFORE {imap_end})'
    )

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

        subject = decode_header(msg["Subject"])[0][0]
        if isinstance(subject, bytes):
            subject = subject.decode()

        email_date = email.utils.parsedate_to_datetime(msg["Date"])
        report_date = extract_report_date(subject)
        body = get_email_text_body(msg)

        if not body.strip():
            print(f"Warning: Empty body for email dated {email_date}")
            continue

        time_stamp = email_date.strftime("%H%M%S")
        filename = f"medallia_{report_date}_{time_stamp}.txt"
        filepath = SAVE_DIR / filename

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"Subject: {subject}\n")
            f.write(f"Date: {email_date}\n")
            f.write(f"Report Date: {report_date}\n")
            f.write(f"{'-' * 80}\n\n")
            f.write(body)

        print(f"[OK] Saved: {filename}")
        downloaded_files.append(filepath)

    mail.logout()
    print(f"\nDownloaded {len(downloaded_files)} email(s) to {SAVE_DIR}")
    return downloaded_files


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Bulk download Medallia guest comments emails from Gmail"
    )
    parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")

    args = parser.parse_args()

    if not EMAIL or not PASSWORD:
        print("Error: EMAIL_USER and EMAIL_PASS must be set in .env file")
        return 1

    downloaded_files = download_medallia_emails_bulk(
        start_date=args.start,
        end_date=args.end
    )

    if downloaded_files:
        print("\nNext steps:")
        print("1. Review downloaded files in:", SAVE_DIR)
        print("2. Run: python scripts/process_medallia_data.py")
        return 0

    print("No files downloaded")
    return 1


if __name__ == "__main__":
    exit(main())
