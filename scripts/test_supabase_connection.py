#!/usr/bin/env python3
"""
Test Supabase connection and show configuration
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from dashboard.utils.supabase_db import _load_secrets, _get_db_params
    
    print("="*80)
    print("SUPABASE CONNECTION TEST")
    print("="*80)
    
    # Try to load secrets
    print("\n1. Loading configuration...")
    try:
        secrets = _load_secrets()
        print("   ✓ Secrets loaded")
        
        # Show supabase config (without password)
        if isinstance(secrets, dict) and "supabase" in secrets:
            config = secrets["supabase"]
            print("\n   Configuration found:")
            for key, value in config.items():
                if "pass" in key.lower() or "password" in key.lower():
                    print(f"     {key}: ****")
                else:
                    print(f"     {key}: {value}")
    except Exception as e:
        print(f"   ✗ Error loading secrets: {e}")
        sys.exit(1)
    
    # Try to get DB params
    print("\n2. Parsing database parameters...")
    try:
        params = _get_db_params()
        print("   ✓ Parameters parsed:")
        print(f"     Host: {params['host']}")
        print(f"     Port: {params['port']}")
        print(f"     Database: {params['dbname']}")
        print(f"     User: {params['user']}")
        print(f"     Password: {'*' * len(params['password'])}")
    except Exception as e:
        print(f"   ✗ Error parsing parameters: {e}")
        sys.exit(1)
    
    # Try to connect
    print("\n3. Testing database connection...")
    try:
        from dashboard.utils.supabase_db import get_supabase_connection
        conn = get_supabase_connection()
        print("   ✓ Connection successful!")
        
        # Test query
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"   PostgreSQL version: {version[:50]}...")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*80)
        print("✓ CONNECTION TEST PASSED")
        print("="*80)
        
    except Exception as e:
        print(f"   ✗ Connection failed: {e}")
        print("\n" + "="*80)
        print("TROUBLESHOOTING TIPS:")
        print("="*80)
        print("1. Check if you're connected to the internet")
        print("2. Verify Supabase host address is correct")
        print("3. Check if Supabase instance is active")
        print("4. Verify firewall isn't blocking port 5432")
        print("5. Try accessing Supabase dashboard in browser")
        sys.exit(1)

except ImportError as e:
    print(f"Import error: {e}")
    print("\nMake sure required packages are installed:")
    print("  pip install psycopg2-binary python-dotenv")
    sys.exit(1)
