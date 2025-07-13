# streamlit_app/utils/exports.py

import streamlit as st
from pathlib import Path
from datetime import datetime
import pdfkit

EXPORTS_DIR = Path("exports")
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

CONFIG = pdfkit.configuration()

STYLE = """
<style>
    body { font-family: Arial, sans-serif; }
    h1, h2, h3, h4 { color: #d15a2d; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border: 1px solid #ddd; padding: 8px; }
    tr:nth-child(even) { background-color: #f9f9f9; }
    th { background-color: #f2a154; color: white; }
</style>
"""

def export_page_as_pdf():
    """Converts the current Streamlit page to a styled PDF."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = EXPORTS_DIR / f"report_{ts}.pdf"

    # Render the entire current page as HTML
    html = f"""
    <html><head>{STYLE}</head><body>
    <h1>Dunkin Sales Dashboard Export</h1>
    {st.session_state.get('_html_export_content', '')}
    </body></html>
    """

    try:
        pdfkit.from_string(html, str(filename), configuration=CONFIG)
        st.success(f"PDF saved to: {filename}")
    except Exception as e:
        st.error(f"PDF export failed: {e}")
