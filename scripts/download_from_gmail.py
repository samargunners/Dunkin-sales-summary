import imaplib
import email
from email.header import decode_header
import os
import datetime
import re

# Email credentials
IMAP_SERVER = "imap.gmail.com"
EMAIL = "dunkinsamar@gmail.com"
PASSWORD = "huyoqtzoaztqdgzw"

SAVE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw_emails")


def clean_filename(text):
    return "".join(c for c in text if c.isalnum() or c in (' ', '.', '_', '-')).rstrip()


def extract_store_name(subject):
    match = re.match(r"(\d{6})\s+(.*?)\s+daily sales summary", subject, re.IGNORECASE)
    if match:
        pc, store_name = match.groups()
        return pc, store_name.replace(" ", "_")
    return "000000", "unknown_store"


def download_email_bodies():
    os.makedirs(SAVE_DIR, exist_ok=True)

    today = datetime.datetime.now().strftime("%d-%b-%Y")
    date_str = datetime.datetime.now().strftime("%Y%m%d")

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
        subject = decode_header(msg["Subject"])[0][0]
        if isinstance(subject, bytes):
            subject = subject.decode()
        subject = clean_filename(subject)
        pc_number, store_name = extract_store_name(subject)

        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True).decode(errors="ignore")
                filename = f"store_{pc_number}_{store_name}_{date_str}.txt"
                filepath = os.path.join(SAVE_DIR, filename)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(body)
                print(f"Saved: {filename}")
                break  # only save the first plain text body

    mail.logout()


if __name__ == "__main__":
    download_email_bodies()
