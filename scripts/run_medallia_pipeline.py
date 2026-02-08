#!/usr/bin/env python3
"""
Complete pipeline script for Medallia Guest Comments
Downloads emails, processes data, and uploads to Supabase
Includes logging, error handling, and email notifications
"""

import subprocess
import sys
import logging
import smtplib
import ssl
import traceback
from email.message import EmailMessage
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
import os

# --- PATH SETUP ---
BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=BASE_DIR / '.env')

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
log_file = LOG_DIR / f"medallia_pipeline_{datetime.now():%Y%m%d}.log"

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
    """Send email notification"""
    if not EMAIL_FROM or not EMAIL_PWD or not EMAIL_TO:
        logging.warning("Email credentials not set; skipping email notification.")
        return
    try:
        msg = EmailMessage()
        msg["From"], msg["To"], msg["Subject"] = EMAIL_FROM, ", ".join(EMAIL_TO), subject
        msg.set_content(body)
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=ctx) as smtp:
            smtp.login(EMAIL_FROM, EMAIL_PWD)
            smtp.send_message(msg)
        logging.info("Email notification sent successfully")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")


def run(script_path, args=None):
    """Run a Python script and capture output"""
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")
    
    logging.info(f"📄 Running {script_path.name}...")
    
    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        logging.error("STDOUT:\n" + result.stdout)
        logging.error("STDERR:\n" + result.stderr)
        raise RuntimeError(
            f"{script_path.name} failed with exit code {result.returncode}"
        )
    
    logging.info(f"✅ {script_path.name} finished OK.")
    if result.stdout.strip():
        logging.info(result.stdout)
    
    return result.stdout


def parse_summary_from_output(output):
    """Extract summary statistics from process output"""
    stats = {
        'files_processed': 0,
        'records_inserted': 0,
        'duplicates_skipped': 0
    }
    
    for line in output.split('\n'):
        if 'Total files processed:' in line:
            stats['files_processed'] = int(line.split(':')[1].strip())
        elif 'Total records inserted:' in line:
            stats['records_inserted'] = int(line.split(':')[1].strip())
        elif 'Total duplicates skipped:' in line:
            stats['duplicates_skipped'] = int(line.split(':')[1].strip())
    
    return stats


def main():
    try:
        import argparse

        parser = argparse.ArgumentParser(description="Run complete Medallia pipeline")
        parser.add_argument(
            "--date",
            type=str,
            default=None,
            help="Specific report date to download (YYYY-MM-DD). Defaults to yesterday."
        )

        args = parser.parse_args()

        # Calculate yesterday's date if not specified
        if args.date:
            report_date = args.date
        else:
            yesterday = datetime.now() - timedelta(days=1)
            report_date = yesterday.strftime("%Y-%m-%d")

        logging.info("="*80)
        logging.info("MEDALLIA GUEST COMMENTS PIPELINE")
        logging.info("="*80)
        logging.info(f"Report date: {report_date}")

        # Step 1: Download emails from Gmail
        logging.info("\n[1/2] Downloading Medallia emails from Gmail...")
        download_script = BASE_DIR / "scripts" / "download_medallia_emails.py"
        run(download_script, [f"--date={report_date}"])
        
        # Step 2: Process and upload to Supabase
        logging.info("\n[2/2] Processing data and uploading to Supabase...")
        process_script = BASE_DIR / "scripts" / "process_medallia_data.py"
        output = run(process_script)
        
        # Extract statistics
        stats = parse_summary_from_output(output)
        
        # Success summary
        summary = f"""
Medallia pipeline completed successfully on {datetime.now():%Y-%m-%d %H:%M}.

Summary:
  - Files processed: {stats['files_processed']}
  - Records inserted: {stats['records_inserted']}
  - Duplicates skipped: {stats['duplicates_skipped']}

Log saved at: {log_file}
"""
        
        logging.info("\n" + "="*80)
        logging.info("✅ PIPELINE COMPLETED SUCCESSFULLY")
        logging.info("="*80)
        logging.info(summary)
        
        send_email(
            "✅ Medallia pipeline success",
            summary
        )
        
        return 0

    except Exception as e:
        err_msg = traceback.format_exc()
        logging.error(err_msg)
        
        error_summary = f"""
Medallia pipeline FAILED on {datetime.now():%Y-%m-%d %H:%M}.

Error encountered:
{err_msg}

Log saved at: {log_file}
"""
        
        send_email(
            "❌ Medallia pipeline FAILED",
            error_summary
        )
        
        return 1


if __name__ == "__main__":
    exit(main())
