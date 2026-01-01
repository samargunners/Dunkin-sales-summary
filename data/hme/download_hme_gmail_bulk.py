import imaplib
import email
from email.header import decode_header
import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
# Load credentials from .env at project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
load_dotenv(os.path.join(project_root, '.env'))

IMAP_SERVER = "imap.gmail.com"
EMAIL = os.getenv("EMAIL_USER")
PASSWORD = os.getenv("EMAIL_PASS")

SAVE_DIR = r"C:\Projects\Dunkin-sales-summary\data\hme\raw"
START_DATE = "2025-12-20"  # YYYY-MM-DD (day after last date in DB)
END_DATE = datetime.now().strftime("%Y-%m-%d")


def download_hme_reports_bulk():
    os.makedirs(SAVE_DIR, exist_ok=True)
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL, PASSWORD)
    mail.select("inbox")

    # Convert dates to IMAP format
    start_dt = datetime.strptime(START_DATE, "%Y-%m-%d")
    end_dt = datetime.strptime(END_DATE, "%Y-%m-%d")
    imap_start = start_dt.strftime('%d-%b-%Y')
    imap_end = (end_dt + timedelta(days=1)).strftime('%d-%b-%Y')

    # Search for emails from HME in date range
    result, data = mail.search(None, f'(FROM "no-reply@hmeqsr.com" SINCE {imap_start} BEFORE {imap_end})')
    email_ids = data[0].split()

    if not email_ids:
        print("No matching emails found.")
        return

    print(f"Found {len(email_ids)} HME emails in range {START_DATE} to {END_DATE}")
    for email_id in email_ids:
        res, msg_data = mail.fetch(email_id, "(RFC822)")
        if res != "OK":
            print(f"Failed to fetch email ID {email_id}")
            continue
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)
        email_date_str = msg.get("Date", "unknown_date")
        try:
            from email.utils import parsedate_to_datetime
            email_dt = parsedate_to_datetime(email_date_str)
            report_dt = email_dt - timedelta(days=1)
            report_date_str = report_dt.strftime("%Y%m%d")
        except Exception:
            report_date_str = "unknown_date"
        attachment_saved = False
        for part in msg.walk():
            if part.get_content_maintype() == "multipart":
                continue
            filename = part.get_filename()
            if filename:
                decoded_name = decode_header(filename)[0][0]
                if isinstance(decoded_name, bytes):
                    decoded_name = decoded_name.decode()
                if decoded_name.lower().endswith((".xlsx", ".xls")):
                    save_filename = f"hme_report_{report_date_str}.xlsx"
                    filepath = os.path.join(SAVE_DIR, save_filename)
                    with open(filepath, "wb") as f:
                        f.write(part.get_payload(decode=True))
                    print(f"[OK] Saved HME report: {filepath}")
                    attachment_saved = True
        if not attachment_saved:
            print(f"No Excel attachment found in email dated {email_date_str}.")
    mail.logout()

if __name__ == "__main__":
    download_hme_reports_bulk()
