import imaplib
import email
from email.header import decode_header
import os
from dotenv import load_dotenv


# Email credentials from .env
IMAP_SERVER = "imap.gmail.com"
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../.env'))
EMAIL = os.getenv("EMAIL_USER")
PASSWORD = os.getenv("EMAIL_PASS")

# Directory to save the attachment
SAVE_DIR = r"C:\Projects\Dunkin-sales-summary\data\hme\raw"
SAVE_FILENAME = "hme_report.xlsx"


def download_hme_report():
    os.makedirs(SAVE_DIR, exist_ok=True)

    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL, PASSWORD)
    mail.select("inbox")

    # Search emails from no-reply@hmeqsr.com
    result, data = mail.search(None, '(FROM "no-reply@hmeqsr.com")')
    email_ids = data[0].split()

    if not email_ids:
        print("No matching emails found.")
        return

    # Process the latest email
    latest_email_id = email_ids[-1]
    res, msg_data = mail.fetch(latest_email_id, "(RFC822)")
    if res != "OK":
        print("Failed to fetch the email.")
        return

    raw_email = msg_data[0][1]
    msg = email.message_from_bytes(raw_email)

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
                filepath = os.path.join(SAVE_DIR, SAVE_FILENAME)
                with open(filepath, "wb") as f:
                    f.write(part.get_payload(decode=True))
                print(f"[OK] Saved HME report: {filepath}")
                attachment_saved = True
                break

    if not attachment_saved:
        print("No Excel attachment found in the latest email.")

    mail.logout()


if __name__ == "__main__":
    download_hme_report()
