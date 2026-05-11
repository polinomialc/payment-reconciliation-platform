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

## 2. Open Streamlit Operations

Run:

```bash
streamlit run app/streamlit_demo.py
```

Open:

```text
http://localhost:8501
```

Start with the Operations Dashboard.

Explain:

> This page is the operational control surface. It shows open amount, allocation readiness, review volume, chargeback indicators, and aging exposure. The purpose is not to replace BI. It is to help analysts act on the current reconciliation queue.

Show:

- status filters
- aging buckets
- owner and reference-type filtering
- aging exposure
- exception queue
- allocation evidence

## 3. Open Receipt Reconciliation

Use the sidebar or open:

```text
http://localhost:8501/?view=receipt&receipt=receipt_ref_001
```

Explain:

> A receipt can contain many transaction lines. Each line has a date, payment channel, provider status, transaction type, reference, and amount. The procedure tries to link those lines to payment batches. Matched lines become allocation evidence. Unmatched or special lines become review items.

Show:

- selected receipt reference
- receipt line count
- allocation-ready lines
- review lines
- linked payment groups
- line-level reconciliation table
- payment group coverage
- items requiring review

Useful talking point:

> The value is not just that a row says ready or review. The value is that the app shows which receipt line supports which payment group, and which receipt lines need a separate treatment such as chargeback, rejected card transaction, amount variance, or missing evidence.

## 4. Explain The SQL Behind It

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

## 5. Open BookStack

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

## 6. Open Metabase

Run:

```bash
cd metabase
docker compose up -d
```

Open:

```text
http://localhost:3000
```

Explain:

> Streamlit is for doing the operational work. Metabase is for management visibility. It consumes published BI views from the same reconciliation outputs and turns them into dashboards for aging exposure, backlog, allocation readiness, and exception trends.

Suggested views:

- `analytics.bi_reconciliation_daily_kpis`
- `analytics.bi_aging_exposure`
- `analytics.bi_exception_backlog`
- `analytics.bi_receipt_exception_summary`
- `analytics.bi_allocation_readiness`

## 7. Run Validation

Run:

```bash
python3 tests/validate_examples.py
python3 tests/validate_duckdb_sql.py
```

Explain:

> The validation tests prove that the sanitized sample inputs reproduce the published output examples, and that the SQL can run locally through DuckDB. This is what makes the demo reviewable without private systems.

## 8. Closing Statement

End with:

> The project demonstrates a full operating model: governed SQL logic, analyst workflows, management reporting, and procedural documentation. The specific sample data is sanitized, but the pattern applies to any finance process where expected records must be reconciled against received payment evidence.
