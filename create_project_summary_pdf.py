"""
Generate a comprehensive project summary PDF for the Dunkin Sales Summary project
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle, Paragraph, 
                                 Spacer, PageBreak, Image)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from datetime import datetime
import os

def create_project_summary():
    """Create comprehensive project summary PDF"""
    
    # Setup PDF
    pdf_filename = "Dunkin_Sales_Summary_Project_Documentation.pdf"
    doc = SimpleDocTemplate(pdf_filename, pagesize=letter,
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    # Container for PDF elements
    story = []
    
    # Define styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CustomTitle', parent=styles['Heading1'],
                             fontSize=24, textColor=colors.HexColor('#FF6B00'),
                             spaceAfter=30, alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='Heading2Custom', parent=styles['Heading2'],
                             fontSize=16, textColor=colors.HexColor('#FF6B00'),
                             spaceAfter=12, spaceBefore=12))
    styles.add(ParagraphStyle(name='Heading3Custom', parent=styles['Heading3'],
                             fontSize=14, textColor=colors.HexColor('#333333'),
                             spaceAfter=6, spaceBefore=6))
    
    # Title Page
    story.append(Spacer(1, 2*inch))
    title = Paragraph("🍩 Dunkin' Donuts<br/>Sales Summary & Analytics System", styles['CustomTitle'])
    story.append(title)
    story.append(Spacer(1, 0.5*inch))
    
    subtitle = Paragraph("Complete Project Documentation", styles['Heading2'])
    subtitle.alignment = TA_CENTER
    story.append(subtitle)
    story.append(Spacer(1, 0.5*inch))
    
    date_text = Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y')}", styles['Normal'])
    date_text.alignment = TA_CENTER
    story.append(date_text)
    
    story.append(PageBreak())
    
    # ===== PROJECT OVERVIEW =====
    story.append(Paragraph("1. Project Overview", styles['Heading2Custom']))
    story.append(Spacer(1, 12))
    
    overview_text = """
    The Dunkin Sales Summary & Analytics System is a comprehensive data pipeline and 
    analytics dashboard designed to track, analyze, and visualize sales performance 
    across multiple Dunkin' Donuts franchise locations. The system automates data 
    collection, transformation, storage, and visualization to provide actionable insights 
    for business decision-making.
    """
    story.append(Paragraph(overview_text, styles['BodyText']))
    story.append(Spacer(1, 12))
    
    # Key Features
    story.append(Paragraph("Key Features:", styles['Heading3Custom']))
    features = [
        "• Automated data pipeline for processing daily sales reports",
        "• Multi-store performance tracking and comparison",
        "• Interactive web-based dashboard with multiple analytics views",
        "• Real-time data synchronization with Supabase cloud database",
        "• Comprehensive reporting covering sales, labor, tender types, and product mix",
        "• Duplicate detection and data validation",
        "• PDF export capabilities for all reports"
    ]
    for feature in features:
        story.append(Paragraph(feature, styles['Normal']))
    story.append(Spacer(1, 12))
    
    # ===== SYSTEM ARCHITECTURE =====
    story.append(PageBreak())
    story.append(Paragraph("2. System Architecture", styles['Heading2Custom']))
    story.append(Spacer(1, 12))
    
    arch_text = """
    The system follows a three-tier architecture consisting of:
    """
    story.append(Paragraph(arch_text, styles['BodyText']))
    story.append(Spacer(1, 12))
    
    # Architecture components
    components = [
        ["Component", "Technology", "Purpose"],
        ["Data Collection", "Python Scripts", "Download reports from Gmail/Manual"],
        ["Data Processing", "pandas, openpyxl", "Parse & transform Excel files"],
        ["Data Storage", "Supabase (PostgreSQL)", "Cloud database for all metrics"],
        ["Dashboard", "Streamlit", "Interactive web-based analytics"],
        ["Visualization", "Plotly", "Charts and graphs"],
    ]
    
    comp_table = Table(components, colWidths=[2*inch, 2*inch, 2.5*inch])
    comp_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF6B00')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(comp_table)
    story.append(Spacer(1, 24))
    
    # ===== DATABASE SCHEMA =====
    story.append(PageBreak())
    story.append(Paragraph("3. Database Schema & Tables", styles['Heading2Custom']))
    story.append(Spacer(1, 12))
    
    schema_intro = """
    The system uses 6 primary tables in Supabase (PostgreSQL) to store different 
    aspects of store performance. All tables share common identifying columns: 
    store, pc_number, and date.
    """
    story.append(Paragraph(schema_intro, styles['BodyText']))
    story.append(Spacer(1, 12))
    
    # Table 1: Sales Summary
    story.append(Paragraph("3.1 sales_summary", styles['Heading3Custom']))
    story.append(Paragraph("Primary sales metrics and financial performance", styles['Normal']))
    story.append(Spacer(1, 6))
    
    sales_summary_cols = [
        ["Column", "Type", "Description"],
        ["id", "INTEGER", "Primary key"],
        ["store", "TEXT", "Store name/location"],
        ["pc_number", "TEXT", "Profit center number"],
        ["date", "DATE", "Transaction date"],
        ["gross_sales", "REAL", "Total sales before deductions"],
        ["net_sales", "REAL", "Sales after discounts/refunds"],
        ["dd_adjusted_no_markup", "REAL", "DD adjusted sales (no markup)"],
        ["pa_sales_tax", "REAL", "Pennsylvania sales tax"],
        ["dd_discount", "REAL", "Total discounts applied"],
        ["guest_count", "INTEGER", "Number of customers"],
        ["avg_check", "REAL", "Average transaction amount"],
        ["gift_card_sales", "REAL", "Gift card purchases"],
        ["void_amount", "REAL", "Total voided transactions"],
        ["refund", "REAL", "Total refunds issued"],
        ["void_qty", "INTEGER", "Number of void transactions"],
        ["cash_in", "REAL", "Cash received"],
    ]
    
    sales_table = Table(sales_summary_cols, colWidths=[1.8*inch, 1.2*inch, 3.5*inch])
    sales_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#333333')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(sales_table)
    story.append(Spacer(1, 18))
    
    # Table 2: Sales by Daypart
    story.append(Paragraph("3.2 sales_by_daypart", styles['Heading3Custom']))
    story.append(Paragraph("Sales performance by time of day", styles['Normal']))
    story.append(Spacer(1, 6))
    
    daypart_cols = [
        ["Column", "Type", "Description"],
        ["id", "INTEGER", "Primary key"],
        ["store", "TEXT", "Store name/location"],
        ["pc_number", "TEXT", "Profit center number"],
        ["date", "DATE", "Transaction date"],
        ["daypart", "TEXT", "Time period (Morning, Afternoon, Evening)"],
        ["net_sales", "REAL", "Sales for this daypart"],
        ["percent_sales", "REAL", "% of total daily sales"],
        ["check_count", "INTEGER", "Number of transactions"],
        ["avg_check", "REAL", "Average transaction amount"],
    ]
    
    daypart_table = Table(daypart_cols, colWidths=[1.8*inch, 1.2*inch, 3.5*inch])
    daypart_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#333333')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    story.append(daypart_table)
    story.append(Spacer(1, 18))
    
    # Table 3: Tender Type Metrics
    story.append(PageBreak())
    story.append(Paragraph("3.3 tender_type_metrics", styles['Heading3Custom']))
    story.append(Paragraph("Payment method breakdown", styles['Normal']))
    story.append(Spacer(1, 6))
    
    tender_cols = [
        ["Column", "Type", "Description"],
        ["id", "INTEGER", "Primary key"],
        ["store", "TEXT", "Store name/location"],
        ["pc_number", "TEXT", "Profit center number"],
        ["date", "DATE", "Transaction date"],
        ["tender_type", "TEXT", "Payment method (Visa, Cash, etc.)"],
        ["detail_amount", "REAL", "Amount paid via this method"],
    ]
    
    tender_table = Table(tender_cols, colWidths=[1.8*inch, 1.2*inch, 3.5*inch])
    tender_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#333333')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    story.append(tender_table)
    story.append(Spacer(1, 18))
    
    # Table 4: Labor Metrics
    story.append(Paragraph("3.4 labor_metrics", styles['Heading3Custom']))
    story.append(Paragraph("Employee hours and payroll tracking", styles['Normal']))
    story.append(Spacer(1, 6))
    
    labor_cols = [
        ["Column", "Type", "Description"],
        ["id", "INTEGER", "Primary key"],
        ["store", "TEXT", "Store name/location"],
        ["pc_number", "TEXT", "Profit center number"],
        ["date", "DATE", "Transaction date"],
        ["labor_position", "TEXT", "Job role/position"],
        ["reg_hours", "REAL", "Regular hours worked"],
        ["ot_hours", "REAL", "Overtime hours worked"],
        ["total_hours", "REAL", "Total hours (reg + OT)"],
        ["reg_pay", "REAL", "Regular pay amount"],
        ["ot_pay", "REAL", "Overtime pay amount"],
        ["total_pay", "REAL", "Total pay (reg + OT)"],
        ["percent_labor", "REAL", "Labor cost as % of sales"],
    ]
    
    labor_table = Table(labor_cols, colWidths=[1.8*inch, 1.2*inch, 3.5*inch])
    labor_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#333333')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    story.append(labor_table)
    story.append(Spacer(1, 18))
    
    # Table 5: Sales by Order Type
    story.append(Paragraph("3.5 sales_by_order_type", styles['Heading3Custom']))
    story.append(Paragraph("Sales breakdown by service channel", styles['Normal']))
    story.append(Spacer(1, 6))
    
    order_cols = [
        ["Column", "Type", "Description"],
        ["id", "INTEGER", "Primary key"],
        ["store", "TEXT", "Store name/location"],
        ["pc_number", "TEXT", "Profit center number"],
        ["date", "DATE", "Transaction date"],
        ["order_type", "TEXT", "Service type (Dine-in, Drive-thru, etc.)"],
        ["net_sales", "REAL", "Sales for this order type"],
        ["percent_sales", "REAL", "% of total daily sales"],
        ["guests", "INTEGER", "Number of customers"],
        ["percent_guest", "REAL", "% of total daily guests"],
        ["avg_check", "REAL", "Average transaction amount"],
    ]
    
    order_table = Table(order_cols, colWidths=[1.8*inch, 1.2*inch, 3.5*inch])
    order_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#333333')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    story.append(order_table)
    story.append(Spacer(1, 18))
    
    # Table 6: Sales by Subcategory
    story.append(PageBreak())
    story.append(Paragraph("3.6 sales_by_subcategory", styles['Heading3Custom']))
    story.append(Paragraph("Product category performance tracking", styles['Normal']))
    story.append(Spacer(1, 6))
    
    subcat_cols = [
        ["Column", "Type", "Description"],
        ["id", "INTEGER", "Primary key"],
        ["store", "TEXT", "Store name/location"],
        ["pc_number", "TEXT", "Profit center number"],
        ["date", "DATE", "Transaction date"],
        ["subcategory", "TEXT", "Product category (Coffee, Donuts, etc.)"],
        ["qty_sold", "INTEGER", "Quantity of items sold"],
        ["net_sales", "REAL", "Sales for this subcategory"],
        ["percent_sales", "REAL", "% of total daily sales"],
    ]
    
    subcat_table = Table(subcat_cols, colWidths=[1.8*inch, 1.2*inch, 3.5*inch])
    subcat_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#333333')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    story.append(subcat_table)
    story.append(Spacer(1, 24))
    
    # ===== DATA PIPELINE =====
    story.append(PageBreak())
    story.append(Paragraph("4. Data Pipeline Process", styles['Heading2Custom']))
    story.append(Spacer(1, 12))
    
    pipeline_intro = """
    The data pipeline consists of multiple stages that transform raw Excel reports 
    into structured, analyzable data in the cloud database.
    """
    story.append(Paragraph(pipeline_intro, styles['BodyText']))
    story.append(Spacer(1, 12))
    
    # Pipeline stages
    story.append(Paragraph("4.1 Data Collection", styles['Heading3Custom']))
    collection_text = """
    Reports are downloaded from Gmail or manually placed in the /data/raw_emails directory. 
    Six report types are required for each day:
    """
    story.append(Paragraph(collection_text, styles['Normal']))
    story.append(Spacer(1, 6))
    
    reports = [
        "1. Labor Hours Report - Employee schedules and payroll",
        "2. Sales by Daypart - Time-based sales breakdown",
        "3. Sales by Subcategory - Product mix performance",
        "4. Tender Type Report - Payment method details",
        "5. Sales Mix Detail (Sales Summary) - Overall financial metrics",
        "6. Menu Mix Metrics (Order Type) - Service channel breakdown"
    ]
    for report in reports:
        story.append(Paragraph(report, styles['Normal']))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("4.2 Data Processing", styles['Heading3Custom']))
    process_text = """
    The batch_processor.py script orchestrates the entire pipeline:
    • Scans for new report files
    • Validates that all 6 report types are present
    • Parses Excel files using specialized flattening functions
    • Normalizes store names and formats
    • Validates data integrity
    • Checks for duplicates before upload
    """
    story.append(Paragraph(process_text, styles['Normal']))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("4.3 Data Storage", styles['Heading3Custom']))
    storage_text = """
    Processed data is uploaded to Supabase (PostgreSQL) with:
    • Automatic duplicate detection
    • Transaction-based uploads for data integrity
    • Error logging and retry mechanisms
    • Connection pooling for performance
    """
    story.append(Paragraph(storage_text, styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Key Scripts
    story.append(PageBreak())
    story.append(Paragraph("4.4 Key Scripts & Files", styles['Heading3Custom']))
    story.append(Spacer(1, 6))
    
    scripts_data = [
        ["Script", "Purpose"],
        ["batch_processor.py", "Main pipeline orchestrator - processes multiple dates"],
        ["compile_store_reports.py", "Parse and flatten Excel reports"],
        ["load_to_sqlite.py", "Upload data to Supabase database"],
        ["download_from_gmail.py", "Auto-download reports from Gmail"],
        ["cleanup_duplicates.py", "Remove duplicate entries"],
        ["check_supabase_data.py", "Validate data in database"],
    ]
    
    scripts_table = Table(scripts_data, colWidths=[2.5*inch, 4*inch])
    scripts_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF6B00')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(scripts_table)
    story.append(Spacer(1, 24))
    
    # ===== DASHBOARD ANALYTICS =====
    story.append(PageBreak())
    story.append(Paragraph("5. Dashboard & Analytics", styles['Heading2Custom']))
    story.append(Spacer(1, 12))
    
    dashboard_intro = """
    The Streamlit-based dashboard provides 9 comprehensive analytical views, 
    each focusing on specific aspects of business performance.
    """
    story.append(Paragraph(dashboard_intro, styles['BodyText']))
    story.append(Spacer(1, 12))
    
    # Dashboard pages
    pages_data = [
        ["Page", "Primary Table(s)", "Key Metrics"],
        ["Executive Summary", "sales_summary", "Net Sales, Guest Count, Avg Check, Discounts"],
        ["Sales Mix", "sales_by_order_type, sales_by_subcategory", "Order Type %, Product Mix, Guest Distribution"],
        ["Daypart Analysis", "sales_by_daypart", "Morning/Afternoon/Evening Sales, Transaction Patterns"],
        ["Labor Efficiency", "labor_metrics", "Hours Worked, Labor Cost, Labor % by Position"],
        ["Tender Type", "tender_type_metrics", "Payment Method Breakdown, Card vs Cash"],
        ["Store Comparison", "All tables", "Multi-store Performance Comparison"],
        ["Cash Reconciliation", "sales_summary, tender_type_metrics", "Cash In, Expected vs Actual"],
        ["Location Metrics", "sales_summary", "Store-specific KPIs and Trends"],
        ["Payroll Metrics", "labor_metrics", "Detailed Payroll Analysis"],
    ]
    
    pages_table = Table(pages_data, colWidths=[1.8*inch, 2.2*inch, 2.5*inch])
    pages_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF6B00')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(pages_table)
    story.append(Spacer(1, 18))
    
    # Common Features
    story.append(Paragraph("5.1 Common Dashboard Features", styles['Heading3Custom']))
    features_list = [
        "• Multi-store filtering with checkbox selections",
        "• Flexible date range or single-day analysis",
        "• Interactive Plotly charts (bar, pie, line, stacked)",
        "• Real-time data from Supabase",
        "• PDF export for each page",
        "• Responsive layout for different screen sizes",
        "• Color-coded metrics and visualizations"
    ]
    for feature in features_list:
        story.append(Paragraph(feature, styles['Normal']))
    story.append(Spacer(1, 12))
    
    # ===== STORES & LOCATIONS =====
    story.append(PageBreak())
    story.append(Paragraph("6. Stores & Locations", styles['Heading2Custom']))
    story.append(Spacer(1, 12))
    
    stores_text = """
    The system currently tracks 7 Dunkin' Donuts franchise locations across Pennsylvania:
    """
    story.append(Paragraph(stores_text, styles['BodyText']))
    story.append(Spacer(1, 12))
    
    stores_data = [
        ["Store Name", "PC Number", "Location"],
        ["Paxton", "301290", "Paxton, PA"],
        ["Mount Joy", "343939", "Mount Joy, PA"],
        ["Enola", "357993", "Enola, PA"],
        ["Columbia", "358529", "Columbia, PA"],
        ["Lititz", "359042", "Lititz, PA"],
        ["Marietta", "363271", "Marietta, PA"],
        ["E-Town", "364322", "Elizabethtown, PA"],
    ]
    
    stores_table = Table(stores_data, colWidths=[2*inch, 1.5*inch, 3*inch])
    stores_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF6B00')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(stores_table)
    story.append(Spacer(1, 24))
    
    # ===== TECHNICAL DETAILS =====
    story.append(PageBreak())
    story.append(Paragraph("7. Technical Stack", styles['Heading2Custom']))
    story.append(Spacer(1, 12))
    
    tech_data = [
        ["Category", "Technology", "Version/Details"],
        ["Language", "Python", "3.13+"],
        ["Database", "Supabase", "PostgreSQL cloud"],
        ["Dashboard", "Streamlit", "Web framework"],
        ["Data Processing", "pandas", "Data manipulation"],
        ["Excel Parsing", "openpyxl", "Excel file handling"],
        ["Visualization", "Plotly", "Interactive charts"],
        ["PDF Generation", "ReportLab, WeasyPrint", "Report exports"],
        ["Version Control", "Git", "Source control"],
    ]
    
    tech_table = Table(tech_data, colWidths=[1.8*inch, 2.2*inch, 2.5*inch])
    tech_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#333333')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(tech_table)
    story.append(Spacer(1, 24))
    
    # ===== USAGE WORKFLOW =====
    story.append(Paragraph("8. Daily Usage Workflow", styles['Heading2Custom']))
    story.append(Spacer(1, 12))
    
    workflow_text = """
    The typical daily workflow for adding new data:
    """
    story.append(Paragraph(workflow_text, styles['BodyText']))
    story.append(Spacer(1, 12))
    
    workflow_steps = [
        "1. Download reports - Obtain all 6 report types from data source",
        "2. Place in directory - Save files to /data/raw_emails",
        "3. Run batch processor - Execute: python scripts/batch_processor.py",
        "4. Select date - Choose interactive mode or provide date parameter",
        "5. Validation - Script validates all files are present",
        "6. Processing - Automatic parsing and data transformation",
        "7. Upload - Data uploaded to Supabase with duplicate checks",
        "8. Verification - Check dashboard for new data",
        "9. Analysis - Use dashboard pages to analyze performance",
    ]
    for step in workflow_steps:
        story.append(Paragraph(step, styles['Normal']))
        story.append(Spacer(1, 4))
    story.append(Spacer(1, 12))
    
    # ===== DATA QUALITY =====
    story.append(PageBreak())
    story.append(Paragraph("9. Data Quality & Validation", styles['Heading2Custom']))
    story.append(Spacer(1, 12))
    
    quality_text = """
    The system includes multiple layers of data validation to ensure accuracy:
    """
    story.append(Paragraph(quality_text, styles['BodyText']))
    story.append(Spacer(1, 12))
    
    validations = [
        "• File presence validation - Ensures all 6 report types exist",
        "• Date parsing verification - Validates date formats in filenames",
        "• Duplicate detection - Prevents re-uploading existing data",
        "• Schema validation - Ensures columns match expected structure",
        "• Data type checking - Validates numeric and date fields",
        "• Null handling - Manages missing values appropriately",
        "• Store name normalization - Standardizes location names",
        "• Transaction integrity - Uses database transactions for uploads"
    ]
    for validation in validations:
        story.append(Paragraph(validation, styles['Normal']))
    story.append(Spacer(1, 12))
    
    # ===== PROJECT STRUCTURE =====
    story.append(PageBreak())
    story.append(Paragraph("10. Project Directory Structure", styles['Heading2Custom']))
    story.append(Spacer(1, 12))
    
    structure_text = """
    The project follows a well-organized directory structure:
    """
    story.append(Paragraph(structure_text, styles['BodyText']))
    story.append(Spacer(1, 12))
    
    directory_structure = [
        "/dashboard/ - Streamlit web application",
        "  /pages/ - Individual dashboard pages",
        "  /components/ - Reusable UI components",
        "  /utils/ - Database and utility functions",
        "  app.py - Main dashboard entry point",
        "",
        "/scripts/ - Data processing scripts",
        "  batch_processor.py - Main pipeline orchestrator",
        "  compile_store_reports.py - Excel parsing logic",
        "  load_to_sqlite.py - Database upload functions",
        "  check_*.py - Various validation scripts",
        "",
        "/data/ - Data storage",
        "  /raw_emails/ - Downloaded Excel reports",
        "  /compiled/ - Processed CSV files",
        "",
        "/db/ - Database schemas and SQL",
        "  sales_schema.sql - Table definitions",
        "  init_db.py - Database initialization",
        "",
        "/logs/ - Processing logs and error tracking",
        "/exports/ - Generated reports and exports",
    ]
    
    for line in directory_structure:
        if line.strip():
            story.append(Paragraph(line, styles['Code']))
    story.append(Spacer(1, 24))
    
    # ===== FUTURE ENHANCEMENTS =====
    story.append(PageBreak())
    story.append(Paragraph("11. Potential Enhancements", styles['Heading2Custom']))
    story.append(Spacer(1, 12))
    
    enhancements = [
        "• Automated email report fetching with scheduled jobs",
        "• Real-time alerts for anomalies (low sales, high discounts, etc.)",
        "• Predictive analytics using machine learning",
        "• Mobile-responsive dashboard improvements",
        "• Advanced forecasting models for inventory and staffing",
        "• Integration with POS systems for real-time data",
        "• Automated report generation and distribution",
        "• Historical trend analysis with year-over-year comparisons",
        "• Customer segmentation analysis",
        "• Advanced labor scheduling optimization"
    ]
    
    for enhancement in enhancements:
        story.append(Paragraph(enhancement, styles['Normal']))
    story.append(Spacer(1, 24))
    
    # ===== SUMMARY =====
    story.append(PageBreak())
    story.append(Paragraph("12. Summary", styles['Heading2Custom']))
    story.append(Spacer(1, 12))
    
    summary_text = """
    The Dunkin Sales Summary & Analytics System provides a comprehensive solution 
    for managing and analyzing sales data across multiple franchise locations. By 
    automating data collection, processing, and visualization, the system enables 
    data-driven decision making and provides valuable insights into business performance.
    <br/><br/>
    The modular architecture ensures maintainability and scalability, while the use 
    of modern cloud technologies (Supabase) guarantees data accessibility and reliability. 
    The interactive dashboard transforms raw sales data into actionable insights, helping 
    franchise owners optimize operations, manage labor costs, understand customer behavior, 
    and maximize profitability.
    <br/><br/>
    With 6 comprehensive database tables tracking everything from sales and labor to 
    payment methods and product mix, the system provides a 360-degree view of business 
    operations. The combination of automated processing, robust validation, and 
    intuitive visualization makes this a powerful tool for franchise management.
    """
    story.append(Paragraph(summary_text, styles['BodyText']))
    
    # Build PDF
    doc.build(story)
    return pdf_filename

if __name__ == "__main__":
    print("Generating comprehensive project summary PDF...")
    filename = create_project_summary()
    print(f"✅ PDF generated successfully: {filename}")
    print(f"   Location: {os.path.abspath(filename)}")
