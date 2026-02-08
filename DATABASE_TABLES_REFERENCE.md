# Database Tables Reference

> **Last Updated**: February 5, 2026
> 
> This document provides detailed schema information for key tables in the Dunkin Sales Summary database.

---

## Table of Contents
- [HME Report](#hme-report)
- [Guest Comments](#guest-comments)
- [Labour Metrics](#labour-metrics)

---

## HME Report

**Table Name**: `hme_report`

**Description**: Stores HME (Headset Measuring Equipment) drive-thru performance metrics for all stores. Data is collected daily via automated email processing.

### Statistics
- **Total Records**: 13,467
- **Date Range**: September 6, 2025 - February 4, 2026
- **Update Frequency**: Daily (automated via `run_hme_pipeline.py`)
- **Data Source**: Gmail emails from `no-reply@hmeqsr.com`

### Schema

| Column Name    | Data Type             | Nullable | Default | Description |
|----------------|----------------------|----------|---------|-------------|
| `id`           | bigint               | NO       | Auto    | Primary key |
| `date`         | date                 | NO       | -       | Report date (YYYY-MM-DD) |
| `store`        | bigint               | YES      | -       | Store PC number |
| `time_measure` | character varying    | YES      | -       | Time measurement type/category |
| `total_cars`   | bigint               | YES      | -       | Total number of cars served |
| `menu_all`     | bigint               | YES      | -       | Menu board time (all measurements) |
| `greet_all`    | bigint               | YES      | -       | Greeting time (all measurements) |
| `service`      | bigint               | YES      | -       | Service window time |
| `lane_queue`   | bigint               | YES      | -       | Lane queue time |
| `lane_total`   | bigint               | YES      | -       | Total lane time |

### Key Metrics Explained

- **Menu Board Time**: Time from car arrival at menu board to order completion
- **Greeting Time**: Time from arrival to initial greeting
- **Service Time**: Time at service window
- **Lane Queue Time**: Time spent waiting in lane
- **Lane Total Time**: Total time from arrival to departure

### Data Collection Pipeline

```
1. Download: data/hme/download_hme_gmail.py (daily)
            data/hme/download_hme_gmail_bulk.py (bulk/historical)
2. Transform: data/hme/transform_hme.py
             data/hme/bulk_transform_hme.py
3. Upload: data/hme/upload_hme_to_supabase.py
4. Pipeline: data/hme/run_hme_pipeline.py (orchestrates all steps)
```

### Usage Examples

```sql
-- Get average service times by store
SELECT 
    store,
    AVG(service) as avg_service_time,
    AVG(lane_total) as avg_total_time
FROM hme_report
WHERE date >= '2026-01-01'
GROUP BY store
ORDER BY avg_total_time;

-- Daily performance for a specific store
SELECT 
    date,
    total_cars,
    service,
    lane_total
FROM hme_report
WHERE store = 357993 
    AND date BETWEEN '2026-01-01' AND '2026-01-31'
ORDER BY date;
```

---

## Guest Comments

**Table Name**: `medallia_reports`

**Description**: Stores customer feedback and satisfaction scores from Medallia daily guest comments surveys. Includes OSAT (Overall Satisfaction) and LTR (Likelihood to Return) metrics.

### Statistics
- **Total Records**: 89
- **Date Range**: January 6, 2026 - February 5, 2026
- **Update Frequency**: Daily (automated via `run_medallia_pipeline.py`)
- **Data Source**: Gmail emails with subject "Daily Guest Comments Summary"

### Schema

| Column Name           | Data Type                    | Nullable | Default      | Description |
|----------------------|------------------------------|----------|--------------|-------------|
| `id`                 | integer                      | NO       | Auto         | Primary key |
| `report_date`        | date                         | NO       | -            | Date of Medallia report |
| `pc_number`          | character varying(10)        | NO       | -            | Restaurant PC number (store ID) |
| `restaurant_address` | text                         | YES      | -            | Full store address |
| `order_channel`      | character varying(20)        | YES      | -            | Order channel (In-store/Other) |
| `transaction_datetime` | timestamp without time zone | YES      | -            | When transaction occurred |
| `response_datetime`  | timestamp without time zone  | NO       | -            | When customer responded to survey |
| `osat`               | integer                      | YES      | -            | Overall Satisfaction (1-5 scale) |
| `ltr`                | integer                      | YES      | -            | Likelihood to Return (0-10 scale) |
| `accuracy`           | character varying(10)        | YES      | -            | Order accuracy (Yes/No) |
| `comment`            | text                         | YES      | -            | Customer comment/feedback |
| `created_at`         | timestamp without time zone  | YES      | now()        | Record creation timestamp |

### Unique Constraint
```sql
UNIQUE (pc_number, response_datetime, comment)
```
This prevents duplicate entries for the same review.

### Scoring Scales

- **OSAT (Overall Satisfaction)**:
  - Scale: 1-5
  - 5 = Highly Satisfied
  - 4 = Satisfied
  - 3 = Neutral
  - 2 = Dissatisfied
  - 1 = Highly Dissatisfied

- **LTR (Likelihood to Return)**:
  - Scale: 0-10
  - 9-10 = Promoters
  - 7-8 = Passives
  - 0-6 = Detractors

### Data Collection Pipeline

```
1. Download: scripts/download_medallia_emails.py
2. Process: scripts/process_medallia_data.py (parses HTML, uploads to DB)
3. Pipeline: scripts/run_medallia_pipeline.py (orchestrates both steps)
```

### Usage Examples

```sql
-- Calculate average scores by store
SELECT 
    pc_number,
    COUNT(*) as total_reviews,
    AVG(osat) as avg_osat,
    AVG(ltr) as avg_ltr,
    COUNT(CASE WHEN accuracy = 'Yes' THEN 1 END) * 100.0 / COUNT(*) as accuracy_pct
  FROM medallia_reports
WHERE report_date >= '2026-01-01'
  GROUP BY pc_number
ORDER BY avg_osat DESC;

-- Find negative reviews (low scores)
SELECT 
    report_date,
    pc_number,
    osat,
    ltr,
    accuracy,
    comment
  FROM medallia_reports
WHERE (osat <= 2 OR ltr <= 5)
    AND report_date >= '2026-01-01'
ORDER BY report_date DESC;

-- Promoters vs Detractors (NPS calculation)
SELECT 
    COUNT(CASE WHEN ltr >= 9 THEN 1 END) * 100.0 / COUNT(*) as promoter_pct,
    COUNT(CASE WHEN ltr <= 6 THEN 1 END) * 100.0 / COUNT(*) as detractor_pct,
    COUNT(CASE WHEN ltr >= 9 THEN 1 END) * 100.0 / COUNT(*) - 
    COUNT(CASE WHEN ltr <= 6 THEN 1 END) * 100.0 / COUNT(*) as nps_score
FROM medallia_reports
WHERE report_date >= '2026-01-01';
```

---

## Labour Metrics

**Status**: Table not yet created in database.

**Planned Implementation**: This table will store labor cost and scheduling metrics for store operations.

### Recommended Schema

```sql
CREATE TABLE labour_metrics (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    store BIGINT NOT NULL,
    scheduled_hours DECIMAL(10,2),
    actual_hours DECIMAL(10,2),
    labor_cost DECIMAL(10,2),
    labor_cost_percentage DECIMAL(5,2),
    employees_scheduled INTEGER,
    employees_worked INTEGER,
    overtime_hours DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(store, date)
);

CREATE INDEX idx_labour_metrics_date ON labour_metrics(date);
CREATE INDEX idx_labour_metrics_store ON labour_metrics(store);
```

### Planned Metrics

| Metric | Description |
|--------|-------------|
| Scheduled Hours | Total hours scheduled for the day |
| Actual Hours | Actual hours worked |
| Labor Cost | Total labor cost for the day |
| Labor Cost % | Labor cost as percentage of sales |
| Employees Scheduled | Number of employees scheduled |
| Employees Worked | Number of employees who actually worked |
| Overtime Hours | Total overtime hours |

---

## Related Documentation

- **Database Schema**: See `db/` folder for table creation scripts
  - `db/guest_comments_schema.sql` - Medallia reports table
  - Additional schemas may be added as needed

- **Data Pipelines**:
  - HME: `data/hme/run_hme_pipeline.py`
  - Medallia: `scripts/run_medallia_pipeline.py`
  - Sales: `scripts/run_pipeline.py`

- **Dashboard**: `dashboard/app.py` - Streamlit application using these tables

---

## Maintenance

### Regular Tasks

1. **Daily**:
   - Run HME pipeline: `python data/hme/run_hme_pipeline.py`
   - Run Medallia pipeline: `python scripts/run_medallia_pipeline.py`

2. **Weekly**:
   - Check for missing dates
   - Verify data quality

3. **Monthly**:
   - Bulk download any missing historical data
   - Database backup (handled by Supabase)

### Data Retention

- HME Report: Retained indefinitely
- Guest Comments: Retained indefinitely
- Database backups: Managed by Supabase (automatic)

### Troubleshooting

**HME Data Not Updating**:
1. Check Gmail authentication in `.env`
2. Verify email delivery from `no-reply@hmeqsr.com`
3. Check pipeline logs in `data/hme/logs/`
4. Run bulk download: `python data/hme/download_hme_gmail_bulk.py`

**Guest Comments Not Updating**:
1. Check Gmail authentication in `.env`
2. Verify "Daily Guest Comments Summary" emails are being received
3. Run manually: `python scripts/run_medallia_pipeline.py`

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-05 | Initial documentation created |

