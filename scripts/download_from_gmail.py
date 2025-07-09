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
    match = re.match(r"Dunkin Sales Summary -\s*(\d{6})\s+(.*)", subject, re.IGNORECASE)
    if match:
        pc_number, store_name = match.groups()
        return pc_number, store_name.replace(" ", "_")
    return "000000", "unknown_store"


def download_email_bodies():
    os.makedirs(SAVE_DIR, exist_ok=True)

    today = datetime.datetime.now().strftime("%d-%b-%Y")
    date_str = datetime.datetime.now().strftime("%Y%m%d")

    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL, PASSWORD)
    mail.select("inbox")

    # Match all subjects containing "Dunkin Sales Summary"
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

        body = None
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            if content_type == "text/plain" and "attachment" not in content_disposition:
                body = part.get_payload(decode=True).decode(errors="ignore")
                break

            elif content_type == "text/html" and "attachment" not in content_disposition:
                html = part.get_payload(decode=True).decode(errors="ignore")
                soup = BeautifulSoup(html, "html.parser")
                body = soup.get_text(separator="\n")
                break

        if body:
            filename = f"store_{pc_number}_{store_name}_{date_str}.txt"
            filepath = os.path.join(SAVE_DIR, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(body)
            print(f"✅ Saved: {filepath}")
        else:
            print(f"❌ No usable content found in: {subject}")

    mail.logout()


if __name__ == "__main__":
    download_email_bodies()
