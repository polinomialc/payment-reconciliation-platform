# Metabase Reporting Demo

This optional demo adds a management-reporting layer on top of the sanitized reconciliation outputs.

Streamlit remains the operational workflow interface. Metabase is intended for managers and leads who need KPI visibility across allocation readiness, aging exposure, exception backlog, and receipt-side disputes.

## Run Locally

Start Docker Desktop first, then run:

```bash
cd metabase
docker compose up -d
```

Open Metabase:

```text
http://localhost:3000
```

During Metabase setup, add a PostgreSQL database connection:

```text
Host: analytics-db
Port: 5432
Database name: metabase
Username: metabase
Password: metabase
Schema: analytics
```

The analytics database is initialized automatically from the repository CSV samples and published outputs.

## BI Views

The demo creates these reporting views:

- `analytics.bi_reconciliation_daily_kpis`
- `analytics.bi_aging_exposure`
- `analytics.bi_exception_backlog`
- `analytics.bi_receipt_exception_summary`
- `analytics.bi_allocation_readiness`

## Suggested Dashboards

- Allocation readiness by day
- Aging exposure by bucket and operational owner
- Exception backlog by outcome and market
- Chargeback and refund exception trend
- Cancellation fee review volume

## Reset

To rebuild the reporting database from scratch:

```bash
docker compose down -v
docker compose up -d
```
