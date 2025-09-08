# streamlit_app/utils/exports.py

import streamlit as st
from pathlib import Path
from datetime import datetime
from fpdf import FPDF

EXPORTS_DIR = Path("exports")
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

def export_page_as_pdf():
    """Exports the current Streamlit page content to a PDF using fpdf."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = EXPORTS_DIR / f"report_{ts}.pdf"
    content = st.session_state.get('_html_export_content', '')

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, "Dunkin Sales Dashboard Export\n\n" + content)

    try:
        pdf.output(str(filename))
        st.success(f"PDF saved to: {filename}")
    except Exception as e:
        st.error(f"PDF export failed: {e}")
