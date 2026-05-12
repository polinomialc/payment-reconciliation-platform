<p align="center">
  <img src="docs/assets/reconciliation-platform-icon.svg" width="96" alt="Payment Reconciliation Platform icon">
</p>

<h1 align="center">Payment Reconciliation Platform</h1>

<p align="center">
  Public, sanitized case study of a reconciliation operating model built around SQL, Streamlit, BI reporting, and procedural knowledge.
</p>

## Quick Read

This repository shows how a spreadsheet-heavy reconciliation process can be turned into a governed data workflow:

- `sample_data/` contains small but realistic public inputs
- `sql/` holds the parsing, keying, reconciliation, and reporting layers
- `app/streamlit_demo.py` runs the SQL live in DuckDB
- `metabase/` is the optional BI-facing layer
- `bookstack/` holds procedural documentation examples

The public demo is intentionally compact. It focuses on:

- payment-batch to receipt matching
- channel-aware logic for `E_COMMERCE` and `CARD_PRESENT`
- open `CHECK` queues
- receipt-side chargebacks
- receipt-side rejected transactions

More advanced scenarios can still be documented in the portfolio, but they are no longer pushed into the Streamlit surface.

## Business Problem

High-volume reconciliation becomes fragile when spreadsheets are the operating layer. Typical issues include:

- manual matching between payment batches, receipts, and external reference files
- duplicated rules across analysts or markets
- weak traceability of why a line was allocated, checked, or excluded
- slow exception handling
- slow rule changes when logic lives outside governed SQL

The platform reframes reconciliation as a governed workflow: raw evidence is preserved, SQL applies explicit rules, analysts work from structured views, and BI consumes the same controlled outputs.

## What The Demo Shows

The local demo runs directly from sanitized CSVs:

- payment-batch lines shaped like ERP settlement exports
- receipt lines shaped like payment-provider exports
- gateway-token mapping for e-commerce
- live DuckDB runtime for SQL execution
- Streamlit views that read like analyst pivots
- optional Metabase layer
- BookStack knowledge-library examples
- runtime validation tests

## Architecture

![Payment reconciliation platform flow](docs/platform-flow.svg)

The main design principle is simple:

> Keep business logic in SQL; keep applications thin, explainable, and replaceable.

## Repository Structure

```text
payment-reconciliation-platform/
|- app/                         # Streamlit operational demo
|- bookstack/                   # BookStack demo configuration and content examples
|- docs/                        # Architecture, business rules, walkthroughs, and assets
|- metabase/                    # Optional BI-facing demo artifacts
|- sample_data/                 # Sanitized source CSV samples
|- scripts/                     # Local DuckDB build and helper scripts
|- sql/                         # Reconciliation and reporting SQL layers
`- tests/                       # Live runtime validation checks
```

## Run The Streamlit Demo

```bash
pip install -r requirements.txt
streamlit run app/streamlit_demo.py
```

Open:

```text
http://localhost:8501
```

## Run The BookStack Demo

```bash
cd bookstack
cp .env.example .env
docker run -it --rm --entrypoint /bin/bash lscr.io/linuxserver/bookstack:latest appkey
docker compose up -d
```

After replacing `APP_KEY` in `.env`, BookStack is available at:

```text
http://localhost:6875
```

## Run The Optional Metabase Demo

```bash
python3 scripts/export_metabase_seed.py
cd metabase
docker compose up -d
```

Metabase is available at:

```text
http://localhost:3000
```

## Validate The Demo

Validate the compact sample design:

```bash
python3 tests/validate_examples.py
```

Validate the live SQL runtime:

```bash
python3 tests/validate_duckdb_sql.py
```

Build an optional local DuckDB file for inspection:

```bash
python3 scripts/build_duckdb_demo.py
```

This creates `payment_reconciliation_demo.duckdb`, which is ignored by Git.

## Case Study Summary

**Business challenge:** spreadsheet-driven reconciliation created manual effort, inconsistent rules, weak auditability, and slow exception follow-up.

**Technical approach:** model the process as a SQL-governed reconciliation pipeline, expose operational workflows through Streamlit, expose management views through Metabase, and document business procedures in BookStack.

**Design outcome:** a reusable platform pattern where rule changes are explicit, historical aging can be recalculated, receipt-level evidence can be traced to payment batches, and exceptions become managed queues rather than spreadsheet comments.

## What This Repository Does Not Contain

- real customer or merchant data
- production database dumps
- proprietary identifiers
- company-specific names
- confidential operational metrics
- exact internal rules that would expose private processes

## Resume Version

Designed and prototyped a financial reconciliation platform to replace spreadsheet-based operational workflows. Built a sanitized proof of concept using Python, Streamlit, SQL, and DuckDB; modeled the target production architecture around governed SQL, BI reporting, and procedural knowledge management.

## Related Docs

- [Architecture](docs/architecture.md)
- [Business Rules](docs/business-rules.md)
- [Case Study](docs/case-study.md)
- [Data Flow](docs/data-flow.md)
- [Demo Walkthrough](docs/demo-walkthrough.md)
- [SQL Reconciliation Walkthrough](docs/sql-reconciliation-walkthrough.md)
- [Tooling Roles](docs/tooling-roles.md)
- [Metabase Dashboard Guide](docs/metabase-dashboard-guide.md)
- [BookStack Knowledge Library](docs/bookstack-knowledge-library.md)
- [Screenshot Placement Guide](docs/screenshots/README.md)
- [Vendor Independence](docs/vendor-independence.md)

## License

MIT
