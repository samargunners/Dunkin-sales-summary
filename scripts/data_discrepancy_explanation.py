"""
REASONS FOR DATA DISCREPANCIES BETWEEN EMAIL REPORTS AND CURRENT SYSTEM
=========================================================================

When email data differs from current system data, here are the common causes:

1. **REPORT TIMING MISMATCH** ⏰
   - Email reports are SNAPSHOTS taken at a specific time
   - The source system (Dunkin's POS) may continue processing transactions after report generation
   - Example: Report sent at 9:00 AM on Nov 7, but late transactions from Nov 6 posted at 10:00 AM

2. **LATE TRANSACTIONS / ADJUSTMENTS** 💳
   - Credit card batches processed after report generation
   - Void transactions applied retroactively
   - Manager adjustments or corrections made days later
   - Refunds processed after the fact

3. **DATA CORRECTIONS BY CORPORATE/MANAGEMENT** ✏️
   - Accounting corrections made in the source system
   - Reconciliation adjustments after month-end
   - Error corrections (duplicate entries removed, wrong amounts fixed)
   - Cash discrepancy adjustments

4. **SYSTEM RECONCILIATION** 🔄
   - Daily reports are "preliminary" 
   - End-of-month reports are "final" with reconciliations
   - Bank deposits may not match initial sales (adjustments applied)
   - Gift card processing delays causing balance updates

5. **REPORTING PERIOD CONFUSION** 📅
   - "Nov 7 report" may contain Nov 6 data (business day vs report date)
   - Time zone differences (report generated in different timezone)
   - Business day ends at different time than calendar day

6. **SOURCE SYSTEM UPDATES** 🖥️
   - POS system software updates that change calculation methods
   - Database migrations or data cleanup operations
   - Historical data corrections applied in bulk

7. **MULTIPLE REPORT VERSIONS** 📄
   - Preliminary vs Final reports
   - Daily vs Weekly vs Monthly consolidations
   - Different report types may show different totals (e.g., net sales vs gross sales)

WHAT THIS MEANS FOR YOUR DATA:
-------------------------------
- Your EMAIL data is a POINT-IN-TIME snapshot (Nov 7 at 9:00 AM)
- Current SYSTEM data may reflect corrections/updates made AFTER that snapshot
- Neither is "wrong" - they represent different time points
- Corporate/source system data is usually the "final truth"

COMMON PATTERNS:
---------------
- Gift Card Sales: Often adjusted due to redemption vs sale timing
- Credit Cards: Batch settlements can take 24-48 hours
- Refunds: Applied retroactively to original transaction dates
- Cash: Reconciliation adjustments after deposit verification

RECOMMENDATIONS:
----------------
1. Use MOST RECENT data from source system as "authoritative"
2. Keep email archives for audit trail / dispute resolution
3. Expect small differences between daily emails and final system data
4. Run reconciliation reports monthly to catch large discrepancies
5. Document any manual adjustments or corrections
"""

print(__doc__)
