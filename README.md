<h1 align="center">
  <img src="docs/assets/reconciliation-platform-icon.svg" width="54" alt="Payment Reconciliation Platform icon"> Payment Reconciliation Platform
</h1>

<p align="center">
  Public, sanitized case study of a financial reconciliation platform designed to replace spreadsheet-heavy operations with governed SQL logic, analyst workflows, BI reporting, and procedural knowledge management.
</p>

## Quick Read

This repository demonstrates how a finance operations process can be moved from manual spreadsheets into a controlled platform pattern:

- **BigQuery-first architecture** for production-grade SQL transformations and governed reporting views
- **Streamlit** for analyst-facing workflows such as receipt reconciliation, allocation readiness, and exception review
- **Metabase** for management reporting on aging exposure, backlog, and operational KPIs
- **BookStack** for business definitions, reconciliation procedures, exception playbooks, and rule-change governance
- **DuckDB** only as a local validation engine so the sanitized SQL can be tested without private systems or cloud access

The project is intentionally public and sanitized. It contains fake sample data, simplified business rules, and generic terminology while preserving the core structure of a real reconciliation operating model.

## Business Problem

High-volume reconciliation becomes fragile when spreadsheets are the operating layer. Common failure points include:

- manual matching between payment batches, receipts, and reference mapping files
- duplicated formulas and inconsistent rules across teams or markets
- weak visibility into aging exposure and unresolved exceptions
- limited traceability of why a transaction was allocated, reviewed, or excluded
- slow rule changes when logic is locked inside external tools or undocumented analyst workbooks

The platform reframes reconciliation as a governed data workflow: raw evidence is preserved, SQL views apply explicit rules, analysts work from structured queues, and management reporting consumes the same controlled outputs.

## What The Demo Shows

The repository includes a complete local demo using sanitized inputs:

- payment batch samples
- receipt samples with accepted, rejected, chargeback, refund, cancellation-fee, and amount-variance scenarios
- payment-channel reference mapping
- SQL layers for parsing, key generation, matching, exception classification, reporting, and BI views
- Streamlit operational demo
- BookStack knowledge-library demo
- optional Metabase reporting stack
- validation tests that compare generated results to published output examples

The demo is small enough to run locally, but the design mirrors a cloud production model where BigQuery is the central SQL layer.

## Architecture

![Payment reconciliation platform flow](docs/platform-flow.svg)

The architecture separates responsibilities deliberately:

- **Source exports** provide raw operational evidence.
- **BigQuery data layer** parses, keys, matches, classifies, and publishes governed views.
- **Streamlit Operations** gives analysts a guided workflow for allocation and exception review.
- **Metabase Reporting** gives leaders KPI visibility without turning the operational app into a BI tool.
- **BookStack Library** keeps business concepts, procedures, and rule-change history close to the platform.
- **DuckDB Local SQL Validation** runs the same SQL locally against sanitized CSVs for demo and testing only.

The main design principle:

> Keep business logic in SQL; keep applications thin, explainable, and replaceable.

## Core Reconciliation Logic

The SQL flow is split into clear layers:

1. **Raw to parsed**: normalize dates, amounts, receipt references, payment references, and channel fields.
2. **Key generation**: derive comparable business keys from invoice references, reservation references, payment-channel tokens, and mapped external references.
3. **Reconciliation logic**: match payment batches to receipt lines using reference, amount, sign, date, and channel-specific rules.
4. **Exception classification**: separate allocation-ready items from rejected card transactions, chargebacks, cancellation-fee reviews, amount variances, and missing evidence.
5. **Reporting views**: expose aging, allocation readiness, receipt-level reconciliation, and exception backlog outputs.
6. **BI views**: publish management-friendly summaries for Metabase.

See [SQL Reconciliation Walkthrough](docs/sql-reconciliation-walkthrough.md) for a deeper explanation.

## Tooling Roles

| Tool | Role | Why it is included |
| --- | --- | --- |
| BigQuery | Target production data warehouse and SQL logic layer | Centralizes rules, auditability, and reporting outputs |
| Streamlit | Operational analyst interface | Lets users inspect receipts, payment batches, exceptions, and allocation readiness |
| Metabase | BI and management reporting | Provides dashboards for KPIs, aging exposure, and backlog trends |
| BookStack | Knowledge governance | Documents business concepts, procedures, exception playbooks, and rule changes |
| DuckDB | Local SQL validation only | Lets reviewers run the SQL demo without cloud access |
| Docker | Demo runtime | Makes BookStack and Metabase reproducible locally |

## Repository Structure

```text
payment-reconciliation-platform/
├─ app/                         # Streamlit operational demo
├─ bookstack/                   # BookStack demo configuration and content import scripts
├─ docs/                        # Architecture, business rules, walkthroughs, and visual assets
├─ metabase/                    # Optional Metabase + PostgreSQL reporting demo
├─ output_examples/             # Published expected outputs from sanitized data
├─ sample_data/                 # Sanitized source CSV samples
├─ scripts/                     # Sample-data and local DuckDB build scripts
├─ sql/                         # Reconciliation and reporting SQL layers
└─ tests/                       # Output and SQL validation checks
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

Useful direct demo route:

```text
http://localhost:8501/?view=receipt&receipt=receipt_ref_001
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

The `bookstack/content/` folder contains sanitized pages that can be imported into BookStack as a departmental knowledge library.

## Run The Optional Metabase Demo

```bash
cd metabase
docker compose up -d
```

Metabase is available at:

```text
http://localhost:3000
```

The reporting database is initialized from sanitized CSV samples and published reconciliation outputs. Dashboard screenshots are intentionally not committed; see [Screenshot Placement Guide](docs/screenshots/README.md).

## Validate The Demo

Validate published outputs:

```bash
python3 tests/validate_examples.py
```

Run the SQL scripts locally through DuckDB:

```bash
python3 tests/validate_duckdb_sql.py
```

Build an optional local DuckDB file for SQL inspection:

```bash
python3 scripts/build_duckdb_demo.py
```

This creates `local_reconciliation_demo.duckdb`, which is ignored by Git.

Regenerate deterministic sample data:

```bash
python3 scripts/generate_sample_data.py
```

## Case Study Summary

**Business challenge:** spreadsheet-driven reconciliation created manual effort, inconsistent rules, limited auditability, and slow exception follow-up.

**Technical approach:** model the process as a SQL-governed reconciliation pipeline, expose operational workflows through Streamlit, expose management views through Metabase, and document business procedures in BookStack.

**Design outcome:** a reusable platform pattern where rule changes are explicit, historical aging can be recalculated, receipt-level evidence can be traced to payment batches, and exceptions become managed queues rather than spreadsheet comments.

See [Case Study](docs/case-study.md) and [Demo Walkthrough](docs/demo-walkthrough.md).

## What This Repository Does Not Contain

- real customer or merchant data
- production database dumps
- proprietary identifiers
- company-specific names
- confidential operational metrics
- exact internal rules that would expose private processes

## Resume Version

Designed and prototyped a financial reconciliation platform to replace spreadsheet-based operational workflows. Built a sanitized local proof of concept using Python, Streamlit, SQL, and DuckDB validation; modeled the target production architecture around BigQuery, containerized operations, BI reporting, and governed procedural documentation.

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

## Visual Assets

- [Platform flow diagram](docs/platform-flow.svg)
- [Operations dashboard mockup](docs/screenshots/dashboard_overview.svg)
- [Exception review mockup](docs/screenshots/exception_review.svg)

## License

MIT
