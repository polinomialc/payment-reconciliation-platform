# Demo Walkthrough

This walkthrough is a presentation script for the local demo. It is designed for a short project discussion, technical interview, or business-case review.

## 1. Start With The Problem

Open the README and platform-flow diagram.

Explain:

> This project models a reconciliation platform for finance operations. The goal is to replace spreadsheet-heavy matching and aging review with governed SQL logic, operational queues, BI visibility, and documented procedures.

Call out the main architecture:

- source exports land as raw evidence
- BigQuery is the production SQL layer
- Streamlit is the analyst workflow
- Metabase is the reporting layer
- BookStack is the business knowledge library
- DuckDB is only the local validation substitute for the public demo

## 2. Open Streamlit

Run:

```bash
streamlit run app/streamlit_demo.py
```

Open:

```text
http://localhost:8501
```

Start with the overview tab.

Explain:

> This page is the compact operational surface. It runs the SQL live in DuckDB and shows a small but readable sample of payment batches, receipts, open check lines, chargebacks, and rejected receipt transactions.

Show:

- channel scope
- payment-batch snapshot
- receipt snapshot
- matched amount
- open amount
- direct row-per-target reading

## 3. Open Receipt Reconciliation

Open the receipt tab inside the app.

Explain:

> A receipt can contain many transaction lines. Each line has a transaction date, payment channel, provider status, transaction type, reference, and amount. The procedure links those lines to payment batches where possible. The receipt view also keeps chargebacks and rejected card transactions visible on the receipt side instead of hiding them in a batch-only summary.

Show:

- selected receipt reference
- receipt line count
- linked payment batches
- chargeback or rejected examples
- receipt breakdown table
- line detail table

Useful talking point:

> The value is not just that a row says matched or review. The value is that the app shows which receipt line supports which payment batch, and which receipt lines remain outside the normal matching flow because they are chargebacks, rejected transactions, or simply still open.

## 4. Open Payment-Batch Reconciliation

Stay in the same app and open the payment-batch tab.

Explain:

> This side reads like an analyst pivot. A payment batch total is shown once, then split across the receipts or open queue targets that explain it. If a payment batch links to two receipts and still has a review amount, the app shows three rows rather than compressing everything into one text field.

Show:

- payment-batch summary table
- one row per receipt or review queue
- selected payment-batch breakdown
- line detail tied to a receipt or queue target

## 5. Explain The SQL Behind It

Open:

```text
sql/01_raw_to_parsed.sql
sql/02_key_generation.sql
sql/03_reconciliation_logic.sql
sql/04_reporting_views.sql
sql/05_bi_views.sql
```

Explain the layers:

- parsing normalizes source fields
- key generation creates comparable references
- reconciliation logic applies matching and exception rules
- reporting views shape operational outputs
- BI views shape management reporting outputs

Use [SQL Reconciliation Walkthrough](sql-reconciliation-walkthrough.md) as the detailed reference.

## 6. Open BookStack

Run:

```bash
cd bookstack
docker compose up -d
```

Open:

```text
http://localhost:6875
```

Explain:

> The platform is not only code. Reconciliation depends on business concepts and procedures. BookStack stores the department's knowledge: definitions, chargeback handling, rejected card handling, cancellation-fee treatment, aging procedures, and governance of rule changes.

Show:

- books as categories
- procedure pages
- business glossary
- exception playbooks
- page history or updates

## 7. Open Metabase

Run:

```bash
cd ..
python3 scripts/export_metabase_seed.py
cd metabase
docker compose up -d
```

Open:

```text
http://localhost:3000
```

Explain:

> Streamlit is for doing the operational work. Metabase is for management visibility. It consumes BI views from the same reconciliation outputs and turns them into dashboards for aging exposure, backlog, matched versus open balances, and exception trends.

Suggested views:

- `analytics.bi_reconciliation_daily_kpis`
- `analytics.bi_aging_exposure`
- `analytics.bi_exception_backlog`
- `analytics.bi_receipt_exception_summary`
- `analytics.bi_channel_health`

## 8. Run Validation

Run:

```bash
python3 tests/validate_examples.py
python3 tests/validate_duckdb_sql.py
```

Explain:

> The validation tests prove that the sanitized sample inputs can run locally through DuckDB and still produce the same operational views the app uses. This is what makes the demo reviewable without private systems.

## 9. Closing Statement

End with:

> The project demonstrates a full operating model: governed SQL logic, analyst workflows, management reporting, and procedural documentation. The specific sample data is sanitized, but the pattern applies to any finance process where expected records must be reconciled against received payment evidence.
