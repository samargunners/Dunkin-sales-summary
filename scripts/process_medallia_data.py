#!/usr/bin/env python3
"""
Process Medallia guest comments emails and upload to Supabase
Parses downloaded email files and inserts into guest_comments table
"""

import re
import sys
from datetime import datetime
from pathlib import Path
import psycopg2
from psycopg2.extras import execute_values
from bs4 import BeautifulSoup

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dashboard.utils.supabase_db import get_supabase_connection


def parse_medallia_email_html(html_text, report_date):
    """
    Parse Medallia HTML email into structured records
    
    Args:
        html_text: HTML email body
        report_date: Date of the report (YYYY-MM-DD string)
    
    Returns:
        List of dictionaries with guest comment data
    """
    soup = BeautifulSoup(html_text, 'html.parser')
    records = []
    
    # Find all data rows (skip header)
    rows = soup.find_all('tr', class_='row-data')
    
    for row in rows:
        try:
            # Get all data cells
            cells = row.find_all('td')
            
            if len(cells) < 8:
                continue
            
            # Extract restaurant info (PC number and address)
            restaurant_text = cells[0].get_text(strip=True)
            match = re.match(r'(\d{6})\s*-\s*(.+)', restaurant_text)
            if not match:
                continue
            pc_number = match.group(1)
            address = match.group(2)
            
            # Order channel (if empty, it's In-store)
            order_channel_text = cells[1].get_text(strip=True)
            order_channel = "Other" if order_channel_text else "In-store"
            
            # Transaction datetime
            transaction_text = cells[2].get_text(strip=True)
            transaction_dt = None
            if transaction_text:
                try:
                    transaction_dt = datetime.strptime(transaction_text, "%m/%d/%y %I:%M %p")
                except ValueError:
                    pass
            
            # Response datetime
            response_text = cells[3].get_text(strip=True)
            if not response_text:
                continue
            response_dt = datetime.strptime(response_text, "%m/%d/%y %I:%M %p")
            
            # OSAT score
            osat_text = cells[4].get_text(strip=True)
            osat = int(osat_text) if osat_text else None
            
            # LTR score
            ltr_text = cells[5].get_text(strip=True)
            ltr = int(ltr_text) if ltr_text else None
            
            # Accuracy
            accuracy = cells[6].get_text(strip=True) or ""
            
            # Find the comment row (next tr with class comments-row)
            comment = ""
            next_row = row.find_next_sibling('tr', class_='comments-row')
            if next_row:
                comment_div = next_row.find('div', class_='comments-verbiage')
                if comment_div:
                    comment = comment_div.get_text(strip=True)
            
            records.append({
                "report_date": report_date,
                "restaurant_pc": pc_number,
                "restaurant_address": address,
                "order_channel": order_channel,
                "transaction_datetime": transaction_dt,
                "response_datetime": response_dt,
                "osat": osat,
                "ltr": ltr,
                "accuracy": accuracy,
                "comment": comment
            })
            
        except Exception as e:
            print(f"  Warning: Failed to parse row: {e}")
            continue
    
    return records


def parse_medallia_email(email_text, report_date):
    """
    Parse Medallia email (HTML or text) into structured records
    Automatically detects format and uses appropriate parser
    
    Args:
        email_text: Raw email body (HTML or text)
        report_date: Date of the report (YYYY-MM-DD string)
    
    Returns:
        List of dictionaries with guest comment data
    """
    # Check if HTML
    if '<table' in email_text or '<div' in email_text:
        return parse_medallia_email_html(email_text, report_date)
    
    # Fallback to plain text parser (legacy format)
    lines = [l.strip() for l in email_text.splitlines() if l.strip()]
    records = []
    i = 0

    restaurant_re = re.compile(r"^(\d{6})\s*-\s*(.+)$")

    while i < len(lines):
        match = restaurant_re.match(lines[i])
        if not match:
            i += 1
            continue

        pc_number = match.group(1)
        address = match.group(2)

        # Check if we have enough lines left for a complete record
        if i + 6 >= len(lines):
            i += 1
            continue

        # Parse order channel and transaction datetime
        order_channel = "In-store"
        transaction_dt = None
        transaction_raw = lines[i + 1]
        
        if transaction_raw.lower() == "other":
            order_channel = "Other"
            transaction_dt = None
            i += 2  # Skip the "Other" line
        else:
            try:
                transaction_dt = datetime.strptime(transaction_raw, "%m/%d/%y %I:%M %p")
                i += 1
            except ValueError:
                # If we can't parse, assume it's "Other"
                order_channel = "Other"
                i += 1

        # Parse remaining fields
        try:
            response_dt = datetime.strptime(lines[i + 1], "%m/%d/%y %I:%M %p")
            osat = int(lines[i + 2])
            ltr = int(lines[i + 3])
            accuracy = lines[i + 4]

            # Skip "Please tell us more about your visit" or "Offered Sample"
            j = i + 5
            while j < len(lines) and ("Please tell us more" in lines[j] or "Offered Sample" in lines[j]):
                j += 1

            # Collect comment lines until "Go to survey"
            comment_lines = []
            while j < len(lines) and "Go to survey" not in lines[j]:
                comment_lines.append(lines[j])
                j += 1

            comment = " ".join(comment_lines).strip()

            records.append({
                "report_date": report_date,
                "restaurant_pc": pc_number,
                "restaurant_address": address,
                "order_channel": order_channel,
                "transaction_datetime": transaction_dt,
                "response_datetime": response_dt,
                "osat": osat,
                "ltr": ltr,
                "accuracy": accuracy,
                "comment": comment
            })

            i = j + 1  # move past "Go to survey"
        except (ValueError, IndexError) as e:
            print(f"Warning: Failed to parse record at line {i}: {e}")
            i += 1
            continue

    return records


def insert_records(conn, records):
    """
    Insert records into guest_comments table
    Uses ON CONFLICT to handle duplicates
    
    Args:
        conn: Database connection
        records: List of record dictionaries
    
    Returns:
        Tuple of (inserted_count, duplicate_count)
    """
    if not records:
        return 0, 0
    
    cursor = conn.cursor()
    
    # Prepare data for batch insert
    insert_query = """
        INSERT INTO guest_comments (
            report_date, restaurant_pc, restaurant_address, order_channel,
            transaction_datetime, response_datetime, osat, ltr, accuracy, comment
        ) VALUES %s
        ON CONFLICT (restaurant_pc, response_datetime, comment) 
        DO NOTHING
        RETURNING id
    """
    
    values = [
        (
            r["report_date"],
            r["restaurant_pc"],
            r["restaurant_address"],
            r["order_channel"],
            r["transaction_datetime"],
            r["response_datetime"],
            r["osat"],
            r["ltr"],
            r["accuracy"],
            r["comment"]
        )
        for r in records
    ]
    
    # Use execute_values for efficient batch insert
    result = execute_values(
        cursor,
        insert_query,
        values,
        template=None,
        fetch=True
    )
    
    inserted_count = len(result) if result else 0
    duplicate_count = len(records) - inserted_count
    
    conn.commit()
    cursor.close()
    
    return inserted_count, duplicate_count


def process_medallia_file(filepath, conn):
    """
    Process a single Medallia email file
    
    Args:
        filepath: Path to email text file
        conn: Database connection
    
    Returns:
        Tuple of (inserted_count, duplicate_count)
    """
    print(f"\nProcessing: {filepath.name}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract report date from filename or content
    filename_match = re.search(r'medallia_(\d{4}-\d{2}-\d{2})', filepath.name)
    if filename_match:
        report_date = filename_match.group(1)
    else:
        # Try to extract from file content
        content_match = re.search(r'Report Date: (\d{4}-\d{2}-\d{2})', content)
        if content_match:
            report_date = content_match.group(1)
        else:
            print(f"Warning: Could not extract report date from {filepath.name}")
            return 0, 0
    
    # Parse records
    records = parse_medallia_email(content, report_date)
    print(f"  Parsed {len(records)} record(s)")
    
    if not records:
        print("  No records to insert")
        return 0, 0
    
    # Insert into database
    inserted, duplicates = insert_records(conn, records)
    print(f"  ✓ Inserted: {inserted}, Duplicates skipped: {duplicates}")
    
    return inserted, duplicates


def process_all_medallia_files():
    """
    Process all Medallia email files in the raw_emails/medallia directory
    """
    medallia_dir = Path(__file__).parent.parent / "data" / "raw_emails" / "medallia"
    
    if not medallia_dir.exists():
        print(f"Error: Directory not found: {medallia_dir}")
        print("Run download_medallia_emails.py first")
        return 1
    
    # Get all medallia text files
    files = sorted(medallia_dir.glob("medallia_*.txt"))
    
    if not files:
        print(f"No Medallia email files found in {medallia_dir}")
        return 1
    
    print(f"Found {len(files)} file(s) to process")
    
    # Connect to database
    print("\nConnecting to Supabase...")
    try:
        conn = get_supabase_connection()
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return 1
    
    # Process each file
    total_inserted = 0
    total_duplicates = 0
    
    for filepath in files:
        try:
            inserted, duplicates = process_medallia_file(filepath, conn)
            total_inserted += inserted
            total_duplicates += duplicates
        except Exception as e:
            print(f"  ✗ Error processing {filepath.name}: {e}")
            continue
    
    conn.close()
    
    print("\n" + "="*80)
    print(f"Summary:")
    print(f"  Total files processed: {len(files)}")
    print(f"  Total records inserted: {total_inserted}")
    print(f"  Total duplicates skipped: {total_duplicates}")
    print("="*80)
    
    return 0


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Process Medallia guest comments and upload to Supabase")
    parser.add_argument(
        "--file",
        type=str,
        help="Process a specific file (optional)"
    )
    
    args = parser.parse_args()
    
    if args.file:
        # Process single file
        filepath = Path(args.file)
        if not filepath.exists():
            print(f"Error: File not found: {filepath}")
            return 1
        
        print("Connecting to Supabase...")
        try:
            conn = get_supabase_connection()
        except Exception as e:
            print(f"Error connecting to database: {e}")
            return 1
        
        inserted, duplicates = process_medallia_file(filepath, conn)
        conn.close()
        
        print(f"\nTotal inserted: {inserted}, Duplicates: {duplicates}")
        return 0
    else:
        # Process all files
        return process_all_medallia_files()


if __name__ == "__main__":
    exit(main())
