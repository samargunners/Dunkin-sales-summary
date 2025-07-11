import imaplib
import email
from email.header import decode_header
import os
import datetime
import re
from bs4 import BeautifulSoup

# Email credentials
IMAP_SERVER = "imap.gmail.com"
EMAIL = "dunkinsamar@gmail.com"
PASSWORD = "huyoqtzoaztqdgzw"

# Directory to save raw email content
SAVE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw_emails")


def clean_filename(text):
    return "".join(c for c in text if c.isalnum() or c in (' ', '.', '_', '-')).rstrip()


def extract_store_info(subject):
    """
    Extracts PC number and store name from subject like:
    'Dunkin Sales Summary - 301290 Paxton'
    """
    match = re.match(r"Dunkin Sales Summary \s*(\d{6})\s+(.*)", subject, re.IGNORECASE)
    if match:
        pc_number, store_name = match.groups()
        return pc_number, store_name.replace(" ", "_")
    return "000000", "unknown_store"


def download_email_bodies():
    os.makedirs(SAVE_DIR, exist_ok=True)

    today = datetime.datetime.now().strftime("%d-%b-%Y")
    date_for_filename = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y%m%d")

    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL, PASSWORD)
    mail.select("inbox")

    result, data = mail.search(None, f'(SENTSINCE {today} SUBJECT "Dunkin Sales Summary")')
    email_ids = data[0].split()

    if not email_ids:
        print("⚠️ No matching emails found.")
        return

    for e_id in email_ids:
        res, msg_data = mail.fetch(e_id, "(RFC822)")
        if res != "OK":
            continue

        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        subject = decode_header(msg["Subject"])[0][0]
        if isinstance(subject, bytes):
            subject = subject.decode()
        subject = clean_filename(subject)

        pc_number, store_name = extract_store_info(subject)

        attachment_saved = False
        for part in msg.walk():
            # Skip multipart containers
            if part.get_content_maintype() == "multipart":
                continue
            # Check if this part has a filename (attachment)
            filename = part.get_filename()
            if filename:
                filename_decoded = decode_header(filename)[0][0]
                if isinstance(filename_decoded, bytes):
                    filename_decoded = filename_decoded.decode()
                # Only save Excel files
                if filename_decoded.lower().endswith((".xlsx", ".xls")):
                    save_filename = f"store_{pc_number}_{store_name}_{date_for_filename}.xlsx"
                    filepath = os.path.join(SAVE_DIR, save_filename)
                    with open(filepath, "wb") as f:
                        f.write(part.get_payload(decode=True))
                    print(f"✅ Saved attachment: {filepath}")
                    attachment_saved = True
                    break

        if not attachment_saved:
            print(f"❌ No Excel attachment found in: {subject}")

    mail.logout()


if __name__ == "__main__":
    download_email_bodies()
