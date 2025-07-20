import subprocess, sys, logging, smtplib, ssl, traceback
from email.message import EmailMessage
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import os

# --- PATH SETUP ---
BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=BASE_DIR / '.env')

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
log_file = LOG_DIR / f"pipeline_{datetime.now():%Y%m%d}.log"

# --- LOGGING CONFIG ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ],
)

# --- EMAIL CONFIG ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
EMAIL_FROM = os.getenv("EMAIL_USER")
EMAIL_TO = [os.getenv("EMAIL_USER")]
EMAIL_PWD = os.getenv("EMAIL_PASS")


def send_email(subject, body):
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = EMAIL_FROM, ", ".join(EMAIL_TO), subject
    msg.set_content(body)
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=ctx) as smtp:
        smtp.login(EMAIL_FROM, EMAIL_PWD)
        smtp.send_message(msg)


def run(script_path):
    logging.info(f"📄 Running {script_path.name}...")
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logging.error(result.stderr)
        raise RuntimeError(
            f"{script_path.name} failed:\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    logging.info(f"✅ {script_path.name} finished OK.")
    logging.debug(result.stdout)


def main():
    try:
        scripts = [
            BASE_DIR / "scripts" / "download_from_gmail.py",
            BASE_DIR / "scripts" / "compile_store_reports.py",
            BASE_DIR / "scripts" / "load_to_sqlite.py",
        ]

        for script in scripts:
            run(script)

        send_email(
            "✅ Dunkin ETL pipeline success",
            f"All steps finished without errors on {datetime.now():%Y-%m-%d %H:%M}."
        )
        logging.info("✅ Pipeline completed successfully.")

    except Exception as e:
        err_msg = traceback.format_exc()
        logging.error(err_msg)
        send_email(
            "❌ Dunkin ETL pipeline FAILED",
            f"Error encountered:\n{err_msg}\nLog saved at: {log_file}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
