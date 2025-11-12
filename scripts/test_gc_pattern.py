"""
Test the ILIKE pattern matching for Gift Card Redeem
"""

import os
import sys

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.utils.supabase_db import get_supabase_connection


def test_pattern_matching():
    """Test the ILIKE pattern for GC Redeem."""
    
    try:
        print("Connecting to Supabase...")
        conn = get_supabase_connection()
        cursor = conn.cursor()
        
        # Test if the pattern matches
        print("\n" + "="*80)
        print("TEST: Does 'Gift Card Redeem' match 'GC Redeem' pattern?")
        print("="*80)
        
        cursor.execute("""
            SELECT 
                'Gift Card Redeem' ILIKE 'GC Redeem' as exact_match,
                'Gift Card Redeem' ILIKE '%GC%Redeem%' as pattern_match,
                'Gift Card Redeem' ILIKE '%gift%card%redeem%' as full_pattern_match
        """)
        
        result = cursor.fetchone()
        print(f"Exact match ('GC Redeem'): {result[0]}")
        print(f"Pattern match ('%GC%Redeem%'): {result[1]}")
        print(f"Full pattern match ('%gift%card%redeem%'): {result[2]}")
        
        # Check what the CASE statement returns for actual data
        print("\n" + "="*80)
        print("What does the CASE statement return for Oct 18-31?")
        print("="*80)
        
        cursor.execute("""
            SELECT 
                tender_type,
                CASE
                  WHEN tender_type ILIKE 'GC Redeem' THEN 'gift_card_redeem'
                  WHEN tender_type ILIKE '%uber%eats%' THEN 'uber_eats'
                  WHEN tender_type ILIKE '%door%dash%' THEN 'door_dash'
                  WHEN tender_type ILIKE '%grub%hub%' THEN 'grubhub'
                  WHEN tender_type ILIKE '%visa%' THEN 'visa'
                  WHEN tender_type ILIKE '%american express%' OR tender_type ILIKE '%amex%' THEN 'amex'
                  WHEN tender_type ILIKE '%discover%' THEN 'discover'
                  WHEN tender_type ILIKE '%mastercard%' OR tender_type ILIKE '%master card%' THEN 'mastercard'
                  ELSE NULL
                END AS tcat,
                COUNT(*) as cnt
            FROM tender_type_metrics
            WHERE date BETWEEN '2025-10-18' AND '2025-10-31'
            AND tender_type ILIKE '%gift%'
            GROUP BY tender_type, tcat
            ORDER BY tender_type
        """)
        
        results = cursor.fetchall()
        print("\nTender Type                      -> Categorized As       | Count")
        print("-" * 80)
        for row in results:
            cat = row[1] if row[1] else "NULL (NOT MATCHED!)"
            print(f"{row[0]:32} -> {cat:20} | {row[2]:3}")
        
        # Now test with corrected pattern
        print("\n" + "="*80)
        print("CORRECTED CASE statement (using %gift%card%redeem%):")
        print("="*80)
        
        cursor.execute("""
            SELECT 
                tender_type,
                CASE
                  WHEN tender_type ILIKE '%gift%card%redeem%' THEN 'gift_card_redeem'
                  WHEN tender_type ILIKE '%uber%eats%' THEN 'uber_eats'
                  WHEN tender_type ILIKE '%door%dash%' THEN 'door_dash'
                  WHEN tender_type ILIKE '%grub%hub%' THEN 'grubhub'
                  WHEN tender_type ILIKE '%visa%' THEN 'visa'
                  WHEN tender_type ILIKE '%american express%' OR tender_type ILIKE '%amex%' THEN 'amex'
                  WHEN tender_type ILIKE '%discover%' THEN 'discover'
                  WHEN tender_type ILIKE '%mastercard%' OR tender_type ILIKE '%master card%' THEN 'mastercard'
                  ELSE NULL
                END AS tcat,
                COUNT(*) as cnt
            FROM tender_type_metrics
            WHERE date BETWEEN '2025-10-18' AND '2025-10-31'
            AND tender_type ILIKE '%gift%'
            GROUP BY tender_type, tcat
            ORDER BY tender_type
        """)
        
        results = cursor.fetchall()
        print("\nTender Type                      -> Categorized As       | Count")
        print("-" * 80)
        for row in results:
            cat = row[1] if row[1] else "NULL (NOT MATCHED!)"
            print(f"{row[0]:32} -> {cat:20} | {row[2]:3}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_pattern_matching()
