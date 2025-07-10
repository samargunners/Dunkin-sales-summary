-- sales_summary table
CREATE TABLE sales_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    store TEXT NOT NULL,
    pc_number TEXT NOT NULL,
    date DATE NOT NULL,
    gross_sales REAL,
    net_sales REAL,
    dd_adjusted_no_markup REAL,
    pa_sales_tax REAL,
    dd_discount REAL,
    guest_count INTEGER,
    avg_check REAL,
    gift_card_sales REAL,
    void_amount REAL,
    refund REAL,
    void_qty INTEGER,
    cash_in REAL
);

-- sales_by_daypart table
CREATE TABLE sales_by_daypart (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    store TEXT NOT NULL,
    pc_number TEXT NOT NULL,
    date DATE NOT NULL,
    daypart TEXT NOT NULL,
    net_sales REAL,
    percent_sales REAL,
    check_count INTEGER,
    avg_check REAL
);

-- tender_type_metrics table
CREATE TABLE tender_type_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    store TEXT NOT NULL,
    pc_number TEXT NOT NULL,
    date DATE NOT NULL,
    tender_type TEXT NOT NULL,
    detail_amount REAL
);

-- labor_metrics table
CREATE TABLE labor_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    store TEXT NOT NULL,
    pc_number TEXT NOT NULL,
    date DATE NOT NULL,
    labor_position TEXT NOT NULL,
    reg_hours REAL,
    ot_hours REAL,
    total_hours REAL,
    reg_pay REAL,
    ot_pay REAL,
    total_pay REAL,
    percent_labor REAL
);

-- sales_by_order_type table
CREATE TABLE sales_by_order_type (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    store TEXT NOT NULL,
    pc_number TEXT NOT NULL,
    date DATE NOT NULL,
    order_type TEXT NOT NULL,
    net_sales REAL,
    percent_sales REAL,
    guests INTEGER,
    percent_guest REAL,
    avg_check REAL
);

-- sales_by_subcategory table
CREATE TABLE sales_by_subcategory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    store TEXT NOT NULL,
    pc_number TEXT NOT NULL,
    date DATE NOT NULL,
    subcategory TEXT NOT NULL,
    qty_sold INTEGER,
    net_sales REAL,
    percent_sales REAL
);
