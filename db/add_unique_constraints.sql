-- Add proper unique constraints to prevent duplicates while allowing multiple stores per date
-- Each table should have a unique constraint on the combination of identifying columns

-- Sales Summary: unique per store/pc_number/date (only one summary per store per date)
ALTER TABLE sales_summary 
ADD CONSTRAINT unique_sales_summary 
UNIQUE (store, pc_number, date);

-- Labor Metrics: unique per store/pc_number/date/labor_position
ALTER TABLE labor_metrics 
ADD CONSTRAINT unique_labor_metrics 
UNIQUE (store, pc_number, date, labor_position);

-- Sales by Daypart: unique per store/pc_number/date/daypart  
ALTER TABLE sales_by_daypart 
ADD CONSTRAINT unique_sales_daypart 
UNIQUE (store, pc_number, date, daypart);

-- Sales by Subcategory: unique per store/pc_number/date/subcategory
ALTER TABLE sales_by_subcategory 
ADD CONSTRAINT unique_sales_subcategory 
UNIQUE (store, pc_number, date, subcategory);

-- Sales by Order Type: unique per store/pc_number/date/order_type
ALTER TABLE sales_by_order_type 
ADD CONSTRAINT unique_sales_order_type 
UNIQUE (store, pc_number, date, order_type);

-- Tender Type Metrics: unique per store/pc_number/date/tender_type
ALTER TABLE tender_type_metrics 
ADD CONSTRAINT unique_tender_type 
UNIQUE (store, pc_number, date, tender_type);