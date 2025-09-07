import psycopg2
import toml
from pathlib import Path

# ...existing code...

def get_supabase_connection():
    """Establishes a connection to the Supabase (PostgreSQL) database using credentials from supabase.toml."""
    config_path = Path(__file__).resolve().parent.parent / "dashboard" / "supabase.toml"
    config = toml.load(config_path)
    creds = config["supabase"]
    conn = psycopg2.connect(
        host=creds["host"],
        port=creds["port"],
        dbname=creds["database"],
        user=creds["user"],
        password=creds["password"]
    )
    return conn
