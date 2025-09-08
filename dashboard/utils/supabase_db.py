# dashboard/utils/supabase_db.py
# Unified secrets loader for CLI + Streamlit.
# Looks for:
#   1) ~/.streamlit/secrets.toml
#   2) <repo>/.streamlit/secrets.toml
#   3) Environment variables: SUPABASE_HOST, SUPABASE_PORT, SUPABASE_DB, SUPABASE_USER, SUPABASE_PASS

from __future__ import annotations
from pathlib import Path
import os

# psycopg2-binary is simplest for local use
# pip install psycopg2-binary
import psycopg2

# Prefer stdlib tomllib (Py 3.11+); otherwise fallback to 'toml' package
try:
    import tomllib  # Python 3.11+
    def _read_toml(p: Path) -> dict:
        with p.open("rb") as f:
            return tomllib.load(f)
except Exception:
    import toml  # pip install toml
    def _read_toml(p: Path) -> dict:
        return toml.load(p)

def _project_root_from_this_file() -> Path:
    # This file lives at: <repo>/dashboard/utils/supabase_db.py
    # -> repo root is two levels up from here
    return Path(__file__).resolve().parents[2]

def _load_secrets() -> dict:
    home_secrets = Path.home() / ".streamlit" / "secrets.toml"
    proj_secrets = _project_root_from_this_file() / ".streamlit" / "secrets.toml"

    if home_secrets.exists():
        return _read_toml(home_secrets)
    if proj_secrets.exists():
        return _read_toml(proj_secrets)

    # Fallback: env vars
    env = {
        "SUPABASE_HOST": os.getenv("SUPABASE_HOST"),
        "SUPABASE_PORT": os.getenv("SUPABASE_PORT", "5432"),
        "SUPABASE_DB":   os.getenv("SUPABASE_DB"),
        "SUPABASE_USER": os.getenv("SUPABASE_USER"),
        "SUPABASE_PASS": os.getenv("SUPABASE_PASS"),
    }
    if all(env.values()):
        return env

    # Helpful error with the exact paths we checked
    raise FileNotFoundError(
        "No secrets found. Valid paths for a secrets.toml file or secret directories are: "
        f"{home_secrets}, {proj_secrets}. "
        "Alternatively set env vars SUPABASE_HOST, SUPABASE_PORT, SUPABASE_DB, SUPABASE_USER, SUPABASE_PASS."
    )

def _get_db_params() -> dict:
    s = _load_secrets()
    # Secrets might come from TOML or env. Support both structures.
    host = s.get("SUPABASE_HOST") or s.get("host")
    port = s.get("SUPABASE_PORT") or s.get("port") or "5432"
    db   = s.get("SUPABASE_DB") or s.get("dbname") or s.get("database") or "postgres"
    user = s.get("SUPABASE_USER") or s.get("user")   or "postgres"
    pwd  = s.get("SUPABASE_PASS") or s.get("password")

    if not (host and db and user and pwd):
        raise ValueError(
            "Missing Supabase DB parameters. Need host, dbname/database, user, password. "
            "Check your .streamlit/secrets.toml or env vars."
        )
    return dict(host=host, port=port, dbname=db, user=user, password=pwd)

def get_supabase_connection():
    params = _get_db_params()
    # Force SSL for Supabase
    return psycopg2.connect(
        host=params["host"],
        port=params["port"],
        dbname=params["dbname"],
        user=params["user"],
        password=params["password"],
        sslmode="require",
    )
