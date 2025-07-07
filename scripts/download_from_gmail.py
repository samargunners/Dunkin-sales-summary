import re

# Updated IMAP-based script with store name + date parsing from filename
script_path = "/mnt/data/dunkin_sales_dashboard/scripts/download_from_gmail.py"
script_content = '''import imaplib
import email
from email.header import decode_header
import os
import datetime
import re

# Email credentials
IMAP_SERVER = "imap.gmail.com"
EMAIL = "dunkinsamar@gmail.com"
PASSWORD = "huyoqtzoaztqdgzw"

SAVE_DIR = "data/raw_emails"

def clean_filename(text):
    return "".join(c for c in text if c.isalnum() or c in (' ', '.', '_', '-')).rstrip()

def extract_store_name(filename):
    match = re.match(r"(.*?) (.*?) daily sales summary", filename, re.IGNORECASE)
    if match:
        pc, store_name = match.groups()
        return store_name.replace(" ", "_")
    return "unknown_store"

def download_excel_attachments():
    os.makedirs(SAVE_DIR, exist_ok=True)

    today = datetime.datetime.now().strftime("%d-%b-%Y")

    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL, PASSWORD)
    mail.select("inbox")

    result, data = mail.search(None, f'(SENTSINCE {today} SUBJECT "dunkin sales summary")')
    email_ids = data[0].split()
    if not email_ids:
        print("No matching emails found.")
        return

    for e_id in email_ids:
        res, msg_data = mail.fetch(e_id, "(RFC822)")
        if res != "OK":
            continue

        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        for part in msg.walk():
            if part.get_content_maintype() == "multipart":
                continue
            if part.get("Content-Disposition") is None:
                continue
            filename = part.get_filename()
            if filename and filename.endswith(".xlsx"):
                decoded_header = decode_header(filename)[0][0]
                if isinstance(decoded_header, bytes):
                    filename = decoded_header.decode()
                filename = clean_filename(filename)
                store_name = extract_store_name(filename)
                date_str = datetime.datetime.now().strftime("%Y%m%d")
                new_filename = f"store_{store_name}_{date_str}.xlsx"
                filepath = os.path.join(SAVE_DIR, new_filename)
                with open(filepath, "wb") as f:
                    f.write(part.get_payload(decode=True))
                print(f"Downloaded: {new_filename}")

    mail.logout()

if __name__ == "__main__":
    download_excel_attachments()
'''

with open(script_path, "w") as f:
    f.write(script_content)

script_path
