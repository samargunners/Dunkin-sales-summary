# run_hme_pipeline.py
import subprocess, sys, logging, smtplib, ssl, traceback
from email.message import EmailMessage
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import os

# --- PATH SETUP ---
BASE_DIR = Path(__file__).resolve().parents[0]   # folder containing THIS file
# If you prefer the project root explicitly, use:
# BASE_DIR = Path(r"C:\Projects\Dunkin-sales-summary")

load_dotenv(dotenv_path=BASE_DIR / '.env')

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
log_file = LOG_DIR / f"hme_pipeline_{datetime.now():%Y%m%d}.log"

# --- LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(log_file, encoding="utf-8"),
              logging.StreamHandler(sys.stdout)],
)

# --- EMAIL CONFIG ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
EMAIL_FROM = os.getenv("EMAIL_USER")
EMAIL_TO = [os.getenv("EMAIL_USER")]  # send to yourself; add more if needed
EMAIL_PWD = os.getenv("EMAIL_PASS")

def send_email(subject: str, body: str):
    if not EMAIL_FROM or not EMAIL_PWD or not EMAIL_TO:
        logging.warning("Email credentials not set; skipping email notification.")
        return
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = EMAIL_FROM, ", ".join(EMAIL_TO), subject
    msg.set_content(body)
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=ctx) as smtp:
        smtp.login(EMAIL_FROM, EMAIL_PWD)
        smtp.send_message(msg)

def run(script_path: Path):
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")
    logging.info(f"📄 Running {script_path} ...")
    result = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)
    if result.returncode != 0:
        logging.error("STDOUT:\n" + result.stdout)
        logging.error("STDERR:\n" + result.stderr)
        raise RuntimeError(f"{script_path.name} failed with exit code {result.returncode}")
    logging.info(f"✅ {script_path.name} finished OK.")
    if result.stdout.strip():
        logging.debug(result.stdout)

def main():
    try:
        # Set correct HME paths
        HME_DIR = BASE_DIR
        RAW_DIR = HME_DIR / "raw"
        TRANSFORMED_DIR = HME_DIR / "transformed"

        steps = [
            HME_DIR / "download_hme_gmail.py",
            HME_DIR / "transform_hme.py",
            HME_DIR / "upload_hme_to_supabase.py",
        ]

        for step in steps:
            run(step)

        send_email(
            "✅ HME pipeline success",
            f"All HME steps finished without errors on {datetime.now():%Y-%m-%d %H:%M}.\nLog: {log_file}"
        )
        logging.info("✅ HME pipeline completed successfully.")

    except Exception:
        err_msg = traceback.format_exc()
        logging.error(err_msg)
        send_email(
            "❌ HME pipeline FAILED",
            f"Error encountered:\n{err_msg}\nLog: {log_file}"
        )
        sys.exit(1)

if __name__ == "__main__":
    main()
