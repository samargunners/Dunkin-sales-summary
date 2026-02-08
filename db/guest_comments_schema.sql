-- Guest Comments (Medallia Reviews) Schema
-- Table to store daily guest feedback from Medallia reports

CREATE TABLE IF NOT EXISTS medallia_reports (
    id SERIAL PRIMARY KEY,
    report_date DATE NOT NULL,
    pc_number VARCHAR(10) NOT NULL,
    restaurant_address TEXT,
    order_channel VARCHAR(20),
    transaction_datetime TIMESTAMP,
    response_datetime TIMESTAMP NOT NULL,
    osat INTEGER CHECK (osat >= 1 AND osat <= 5),
    ltr INTEGER CHECK (ltr >= 0 AND ltr <= 10),
    accuracy VARCHAR(10),
    comment TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Unique constraint to prevent duplicate entries
    CONSTRAINT unique_guest_comment UNIQUE (pc_number, response_datetime, comment)
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_medallia_reports_report_date ON medallia_reports(report_date);
CREATE INDEX IF NOT EXISTS idx_medallia_reports_pc_number ON medallia_reports(pc_number);
CREATE INDEX IF NOT EXISTS idx_medallia_reports_response_datetime ON medallia_reports(response_datetime);
CREATE INDEX IF NOT EXISTS idx_medallia_reports_osat ON medallia_reports(osat);
CREATE INDEX IF NOT EXISTS idx_medallia_reports_ltr ON medallia_reports(ltr);

-- Add comment to table
COMMENT ON TABLE medallia_reports IS 'Stores daily guest feedback from Medallia email reports';
COMMENT ON COLUMN medallia_reports.report_date IS 'Date of the Medallia report';
COMMENT ON COLUMN medallia_reports.pc_number IS 'Restaurant PC number (store identifier)';
COMMENT ON COLUMN medallia_reports.order_channel IS 'Where order was placed (In-store, Other, etc.)';
COMMENT ON COLUMN medallia_reports.transaction_datetime IS 'When the transaction occurred (null for Other)';
COMMENT ON COLUMN medallia_reports.response_datetime IS 'When the customer responded to survey';
COMMENT ON COLUMN medallia_reports.osat IS 'Overall Satisfaction score (1-5)';
COMMENT ON COLUMN medallia_reports.ltr IS 'Likelihood to Return score (0-10)';
COMMENT ON COLUMN medallia_reports.accuracy IS 'Order accuracy (Yes/No)';
COMMENT ON COLUMN medallia_reports.comment IS 'Customer comment text';
