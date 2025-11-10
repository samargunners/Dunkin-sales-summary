-- ============================================================================
-- Tender & Sales Report Query
-- ============================================================================
-- This query combines sales summary data with tender type metrics,
-- categorizes tender types, and produces a monthly report.
--
-- Usage: Replace @start_date and @end_date with your desired date range
-- Example: '2025-10-01' and '2025-10-31'
-- ============================================================================

WITH tender_labeled AS (
  -- Step 1: Label each tender type and assign row numbers for deduplication
  SELECT
    t.store,
    t.date,
    t.detail_amount,
    CASE
      WHEN t.tender_type ILIKE '%gift%card%redeem%' THEN 'gift_card_redeem'
      WHEN t.tender_type ILIKE '%uber%eats%' THEN 'uber_eats'
      WHEN t.tender_type ILIKE '%door%dash%' THEN 'door_dash'
      WHEN t.tender_type ILIKE '%grub%hub%' THEN 'grubhub'
      WHEN t.tender_type ILIKE '%visa%' THEN 'visa'
      WHEN t.tender_type ILIKE '%american express%' OR t.tender_type ILIKE '%amex%' THEN 'amex'
      WHEN t.tender_type ILIKE '%discover%' THEN 'discover'
      WHEN t.tender_type ILIKE '%mastercard%' OR t.tender_type ILIKE '%master card%' THEN 'mastercard'
      ELSE NULL
    END AS tcat,
    ROW_NUMBER() OVER (
      PARTITION BY t.store, t.date,
                   CASE
                     WHEN t.tender_type ILIKE '%gift%card%redeem%' THEN 'gift_card_redeem'
                     WHEN t.tender_type ILIKE '%uber%eats%' THEN 'uber_eats'
                     WHEN t.tender_type ILIKE '%door%dash%' THEN 'door_dash'
                     WHEN t.tender_type ILIKE '%grub%hub%' THEN 'grubhub'
                     WHEN t.tender_type ILIKE '%visa%' THEN 'visa'
                     WHEN t.tender_type ILIKE '%american express%' OR t.tender_type ILIKE '%amex%' THEN 'amex'
                     WHEN t.tender_type ILIKE '%discover%' THEN 'discover'
                     WHEN t.tender_type ILIKE '%mastercard%' OR t.tender_type ILIKE '%master card%' THEN 'mastercard'
                     ELSE NULL
                   END
      ORDER BY t.id
    ) AS rn
  FROM tender_type_metrics t
  WHERE t.date BETWEEN @start_date AND @end_date
),
tender_clean AS (
  -- Step 2: Keep only the first occurrence of each tender category per store/date
  SELECT store, date, tcat, detail_amount
  FROM tender_labeled
  WHERE tcat IS NOT NULL AND rn = 1
)
-- Step 3: Join sales summary with tender categories and format output
SELECT
  s.store AS "Store",
  TO_CHAR(s.date, 'MM/DD/YY') AS "Date",
  s.dd_adjusted_no_markup AS "Dunkin Net Sales",
  s.cash_in AS "Cash Due",
  s.gift_card_sales AS "Gift Card Sales",
  s.pa_sales_tax AS "Tax",
  s.paid_out AS "Paid Out",
  COALESCE(gc.detail_amount, 0) AS "Gift Card Redeem",
  COALESCE(ue.detail_amount, 0) AS "Uber Eats",
  COALESCE(dd.detail_amount, 0) AS "Door Dash",
  COALESCE(gh.detail_amount, 0) AS "Grubhub",
  COALESCE(vi.detail_amount, 0) AS "Visa",
  COALESCE(ma.detail_amount, 0) AS "Mastercard",
  COALESCE(di.detail_amount, 0) AS "Discover",
  COALESCE(ax.detail_amount, 0) AS "Amex"
FROM sales_summary s
LEFT JOIN tender_clean gc ON gc.store = s.store AND gc.date = s.date AND gc.tcat = 'gift_card_redeem'
LEFT JOIN tender_clean ue ON ue.store = s.store AND ue.date = s.date AND ue.tcat = 'uber_eats'
LEFT JOIN tender_clean dd ON dd.store = s.store AND dd.date = s.date AND dd.tcat = 'door_dash'
LEFT JOIN tender_clean gh ON gh.store = s.store AND gh.date = s.date AND gh.tcat = 'grubhub'
LEFT JOIN tender_clean vi ON vi.store = s.store AND vi.date = s.date AND vi.tcat = 'visa'
LEFT JOIN tender_clean ma ON ma.store = s.store AND ma.date = s.date AND ma.tcat = 'mastercard'
LEFT JOIN tender_clean ax ON ax.store = s.store AND ax.date = s.date AND ax.tcat = 'amex'
LEFT JOIN tender_clean di ON di.store = s.store AND di.date = s.date AND di.tcat = 'discover'
WHERE s.date BETWEEN @start_date AND @end_date
ORDER BY s.store, s.date;

-- ============================================================================
-- EXAMPLE USAGE:
-- ============================================================================
-- For October 2025:
-- Replace @start_date with '2025-10-01'
-- Replace @end_date with '2025-10-31'
--
-- For November 2025:
-- Replace @start_date with '2025-11-01'
-- Replace @end_date with '2025-11-30'
-- ============================================================================
