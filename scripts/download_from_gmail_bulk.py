import imaplib
import email
from email.header import decode_header
import os
import datetime
import re
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

IMAP_SERVER = "imap.gmail.com"
EMAIL = os.getenv("EMAIL_USER")
PASSWORD = os.getenv("EMAIL_PASS")

# Directory to save raw email content
SAVE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw_emails")

# Define the date range (inclusive)
START_DATE = "2025-12-20"  # YYYY-MM-DD
END_DATE = "2025-12-31"    # YYYY-MM-DD

def clean_filename(text):
    if isinstance(text, bytes):
        text = text.decode('utf-8', errors='replace')
    text = text.replace('—', '-').replace('–', '-').replace('"', '').replace('"', '')
    cleaned = "".join(c for c in text if c.isalnum() or c in (' ', '.', '_', '-')).rstrip()
    return cleaned if cleaned else "attachment"

def download_email_bodies_bulk():
    os.makedirs(SAVE_DIR, exist_ok=True)
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL, PASSWORD)
    mail.select("inbox")

    # Convert dates to IMAP format
    start_dt = datetime.datetime.strptime(START_DATE, "%Y-%m-%d")
    end_dt = datetime.datetime.strptime(END_DATE, "%Y-%m-%d")
    imap_start = start_dt.strftime('%d-%b-%Y')
    imap_end = (end_dt + datetime.timedelta(days=1)).strftime('%d-%b-%Y')

    # Search for emails in date range
    result, data = mail.search(None, f'(SUBJECT "Consolidated Dunkin Sales Summary v2" SINCE {imap_start} BEFORE {imap_end})')
    email_ids = data[0].split()

    if not email_ids:
        print("No matching emails found.")
        return

    print(f"Found {len(email_ids)} emails in range {START_DATE} to {END_DATE}")
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
        subject = clean_filename(subject)
        # Parse the email's received date and subtract one day for the report date
        email_date_str = msg.get("Date", "unknown_date")
        try:
            # Example: 'Fri, 01 Jan 2026 09:01:03 +0000 (UTC)'
            from email.utils import parsedate_to_datetime
            email_dt = parsedate_to_datetime(email_date_str)
            report_dt = email_dt - datetime.timedelta(days=1)
            report_date_str = report_dt.strftime("%Y%m%d")
        except Exception:
            report_date_str = "unknown_date"
        attachment_count = 0
        for part in msg.walk():
            if part.get_content_maintype() == "multipart":
                continue
            filename = part.get_filename()
            if filename:
                filename_decoded = decode_header(filename)[0][0]
                if isinstance(filename_decoded, bytes):
                    filename_decoded = filename_decoded.decode('utf-8', errors='replace')
                filename_decoded = clean_filename(filename_decoded)
                if filename_decoded.lower().endswith((".xlsx", ".xls")):
                    save_filename = f"{report_date_str}_{filename_decoded}"
                    filepath = os.path.join(SAVE_DIR, save_filename)
                    with open(filepath, "wb") as f:
                        f.write(part.get_payload(decode=True))
                    print(f"[OK] Saved attachment: {filepath}")
                    attachment_count += 1
        if attachment_count == 0:
            print(f"No Excel attachments found in: {subject}")
        else:
            print(f"Total Excel attachments saved: {attachment_count}")
    mail.logout()

if __name__ == "__main__":
    download_email_bodies_bulk()
