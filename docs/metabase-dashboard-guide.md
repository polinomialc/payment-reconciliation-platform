# Metabase Dashboard Guide

Metabase provides the management reporting layer for the reconciliation platform. It sits on top of governed SQL views and helps stakeholders monitor aging exposure, matched versus open balances, exception backlog, and receipt-side disputes.

Streamlit remains the operational tool for analysts. Metabase is used for visibility and management review.

## Data Source

The optional Metabase demo runs with:

- PostgreSQL container: `analytics-db`
- Metabase container: `metabase`
- schema: `analytics`
- source data: sanitized CSV samples transformed through the same SQL layers used by the live Streamlit demo

Connection details:

```text
Host: analytics-db
Port: 5432
Database: metabase
Username: metabase
Password: metabase
Schema: analytics
```

## BI Views

Use these views for dashboards:

- `bi_payment_batch_summary`
- `bi_reconciliation_daily_kpis`
- `bi_aging_exposure`
- `bi_exception_backlog`
- `bi_receipt_exception_summary`
- `bi_channel_health`

## Recommended Dashboard

Dashboard name:

```text
Financial Reconciliation Management Dashboard
```

### 1. Open Exposure By Aging Bucket

Source:

```text
Bi Aging Exposure
```

Purpose:

Shows the value of open payment batches grouped by aging bucket. Allocation-ready items are excluded, so the chart focuses on unresolved operational exposure.

Suggested Metabase setup:

- Metric: sum of `open_exposure_amount`
- Group by: `aging_bucket`
- Visualization: bar chart

### 2. Exception Backlog By Outcome

Source:

```text
Bi Exception Backlog
```

Purpose:

Shows how many payment-batch lines remain open by outcome, with emphasis on `CHECK`, rejected evidence, and other unresolved balances.

Suggested Metabase setup:

- Metric: sum of `payment_batch_lines`
- Group by: `reconciliation_outcome`
- Visualization: bar chart or table

### 3. Matched Amount By Day

Source:

```text
Bi Reconciliation Daily Kpis
```

Purpose:

Shows how much value matched cleanly over time. This helps distinguish normal throughput from unresolved exposure.

Suggested Metabase setup:

- Metric: sum of `allocation_ready_amount`
- Group by: `transaction_date`
- Visualization: line chart or bar chart

### 4. Receipt Exceptions By Type

Source:

```text
Bi Receipt Exception Summary
```

Purpose:

Tracks receipt-side exceptions such as chargebacks and rejected transactions. These are separated from standard matching because they follow different operational treatment.

Suggested Metabase setup:

- Metric: sum of `gross_amount` or count of `receipt_lines`
- Group by: `receipt_transaction_type`
- Optional breakout: `transaction_date`
- Visualization: stacked bar chart or table

### 5. Open Versus Matched By Market

Source:

```text
Bi Allocation Readiness
```

Purpose:

Compares matched value and open exposure across sanitized market groups. This helps identify where backlog or exceptions are concentrated.

Suggested Metabase setup:

- Metric: sum of `payment_batch_amount`
- Group by: `market_code`
- Breakout: `reconciliation_outcome`
- Visualization: stacked bar chart

## How To Explain The Layer

Metabase is not replacing Streamlit.

```text
Streamlit = operational action
Metabase  = management visibility
```

The same governed reconciliation outputs can support both:

- an analyst workflow for line-level review;
- a management dashboard for trends, exposure, and backlog.
