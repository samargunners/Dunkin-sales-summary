-- Guest Comments (Medallia Reviews) Schema
-- Table to store daily guest feedback from Medallia reports

CREATE TABLE IF NOT EXISTS guest_comments (
    id SERIAL PRIMARY KEY,
    report_date DATE NOT NULL,
    restaurant_pc VARCHAR(10) NOT NULL,
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
    CONSTRAINT unique_guest_comment UNIQUE (restaurant_pc, response_datetime, comment)
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_guest_comments_report_date ON guest_comments(report_date);
CREATE INDEX IF NOT EXISTS idx_guest_comments_restaurant_pc ON guest_comments(restaurant_pc);
CREATE INDEX IF NOT EXISTS idx_guest_comments_response_datetime ON guest_comments(response_datetime);
CREATE INDEX IF NOT EXISTS idx_guest_comments_osat ON guest_comments(osat);
CREATE INDEX IF NOT EXISTS idx_guest_comments_ltr ON guest_comments(ltr);

-- Add comment to table
COMMENT ON TABLE guest_comments IS 'Stores daily guest feedback from Medallia email reports';
COMMENT ON COLUMN guest_comments.report_date IS 'Date of the Medallia report';
COMMENT ON COLUMN guest_comments.restaurant_pc IS 'Restaurant PC number (store identifier)';
COMMENT ON COLUMN guest_comments.order_channel IS 'Where order was placed (In-store, Other, etc.)';
COMMENT ON COLUMN guest_comments.transaction_datetime IS 'When the transaction occurred (null for Other)';
COMMENT ON COLUMN guest_comments.response_datetime IS 'When the customer responded to survey';
COMMENT ON COLUMN guest_comments.osat IS 'Overall Satisfaction score (1-5)';
COMMENT ON COLUMN guest_comments.ltr IS 'Likelihood to Return score (0-10)';
COMMENT ON COLUMN guest_comments.accuracy IS 'Order accuracy (Yes/No)';
COMMENT ON COLUMN guest_comments.comment IS 'Customer comment text';
