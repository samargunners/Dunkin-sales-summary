# scripts/run_pipeline.py
import subprocess, sys, logging, smtplib, ssl, traceback
from email.message import EmailMessage
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
LOG_DIR  = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
log_file = LOG_DIR / f"pipeline_{datetime.now():%Y%m%d}.log"

# ------------- LOGGING -------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ],
)

# ------------- EMAIL CONFIG -------------
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT   = 465
EMAIL_FROM  = "dunkinsamar@gmail.com"
EMAIL_TO    = ["dunkinsamar@gmail.com"]          # add others if needed
EMAIL_PWD   = "huyoqtzoaztqdgzw"                 # app-specific password (keep in .env!)

def send_email(subject, body):
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = EMAIL_FROM, ", ".join(EMAIL_TO), subject
    msg.set_content(body)
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=ctx) as smtp:
        smtp.login(EMAIL_FROM, EMAIL_PWD)
        smtp.send_message(msg)

# ------------- HELPER -------------
def run(script_path):
    logging.info(f"Running {script_path.name} …")
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=script_path.parent,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"{script_path.name} failed:\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    logging.info(f"{script_path.name} finished OK.")
    logging.debug(result.stdout)

# ------------- MAIN -------------
def main():
    try:
        scripts = [
            BASE_DIR / "scripts" / "download_from_gmail.py",
            BASE_DIR / "scripts" / "compile_report.py",
            BASE_DIR / "scripts" / "load_to_sqlite.py",
        ]
        for s in scripts:
            run(s)

        send_email("✅ Dunkin ETL pipeline success",
                   f"All steps finished without errors on {datetime.now():%Y-%m-%d %H:%M}.")
        logging.info("Pipeline completed successfully.")

    except Exception as e:
        err_msg = traceback.format_exc()
        logging.error(err_msg)
        send_email("❌ Dunkin ETL pipeline FAILED", f(\"\"\"Error encountered:\n{err_msg}\nLog saved at: {log_file}\"\"\"))
        sys.exit(1)

if __name__ == "__main__":
    init_main()