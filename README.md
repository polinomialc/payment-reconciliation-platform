# Payment Reconciliation Platform

Public, sanitized case study of a reconciliation platform designed to replace spreadsheet-heavy financial operations with a centralized, auditable, and cloud-ready workflow.

## Executive Summary
This project represents the design and prototyping of an internal reconciliation platform for high-volume payment operations.

The original workflow relied on:
- multiple spreadsheets per country
- manual cross-checks between payment batches, receipts, and post-treatment files
- duplicated logic and formula drift
- slow troubleshooting
- low auditability
- dependence on a third-party reconciliation platform for rule changes

To address that, a local proof of concept was built with **sanitized CSV sample inputs, Python, Streamlit, and a lightweight DuckDB validation layer** to validate:
- reconciliation logic
- exception handling
- performance
- operational usability

The intended production architecture was designed for **Google Cloud**, with:
- **BigQuery** as the centralized data and logic layer
- **Streamlit** as the operational interface
- **Cloud Run** as the container runtime
- **Metabase** as the reporting layer
- **BookStack** as the departmental knowledge library for business concepts, procedures, exception playbooks, rule definitions, and operational governance

## Why This Project Matters
This is not just a tooling exercise. It is a process-control and operating-model improvement.

The platform was designed to:
- reduce manual reconciliation effort
- standardize logic across countries
- improve auditability and traceability
- remove vendor bottlenecks for rule changes
- bring reconciliation logic fully under internal control

In the previous vendor-driven model, rule corrections and troubleshooting depended on external workflows. In this model, business-rule changes can be implemented internally in minutes after validation.

## Problem Statement
Large-scale payment reconciliation often breaks down when the process depends on spreadsheets as the main operating layer.

Typical failure modes include:
- slow files with hundreds of thousands of rows
- logic inconsistencies across teams and countries
- manual error from copy/paste and formula drift
- weak visibility into unmatched items
- poor traceability of post-treatment decisions

This project reframed reconciliation as a **data platform problem**, not just a spreadsheet problem.

## Solution Overview
The solution combines:
- raw data ingestion
- SQL-based parsing and normalization
- deterministic key generation
- reconciliation logic
- exception classification
- guided operational outputs
- a governed knowledge base for business concepts, procedures, rule explanations, and exception-handling playbooks

Core rule areas include:
- invoice matching
- reservation matching
- acquirer-reference matching
- payment-channel token resolution
- chargeback handling
- cancellation fee handling for fees charged to the customer after reservation cancellation
- overpayment detection
- intercompany payment detection
- mixed or misapplied payment detection
- country-specific exception logic

## Architecture
### Local Proof of Concept
- sanitized CSV sample inputs
- Python
- Streamlit
- DuckDB used only as an in-memory SQL validation engine
- CSV / XLSX operational outputs

### Production Target
- Google Drive or cloud landing folders by country
- BigQuery raw tables
- SQL transformation and reporting views in BigQuery
- Streamlit deployed as a container on Cloud Run
- Metabase dashboards
- BookStack as the departmental financial-operations knowledge library

The main architectural principle is simple:

> keep business logic in SQL, keep the application layer thin

That makes the platform easier to audit, easier to evolve, and easier to migrate from a local PoC to a cloud production model.

![Payment reconciliation platform flow](docs/platform-flow.svg)

## Key Design Decisions
### 1. Local first, cloud ready
The demo data lives in CSV files so the project can be reviewed without private systems or cloud access. DuckDB is used only as a lightweight in-memory SQL execution layer to validate that the SQL scripts reproduce the published reconciliation outputs from those CSV inputs. The target design was always a cloud-native architecture.

### 2. Logic centralized in SQL
Reconciliation logic stays in views and transformation layers rather than being spread across UI code.

### 3. Vendor independence
The project was explicitly designed to reduce dependence on third-party reconciliation platforms and give the department direct ownership of rules, outputs, and troubleshooting.

### 4. Governance by design
Raw data is preserved, transformations are explicit, and reporting outputs can be traced back to governed rule layers.

### 5. Knowledge management as part of the platform
BookStack was included in the target operating model as a departmental library for business concepts, reconciliation procedures, payment exception playbooks, rule definitions, and change history. This keeps business knowledge close to the platform instead of scattered across email threads, private notes, and spreadsheet comments.

## What This Repository Contains
- architecture notes
- business-rule documentation
- BookStack knowledge-library design
- real BookStack demo configuration and sample procedure content
- sanitized SQL examples
- fake sample datasets
- example reconciliation outputs
- a small Streamlit demo
- a sample Dockerfile for the target deployment direction

## What This Repository Does Not Contain
- real customer or merchant data
- production database dumps
- proprietary identifiers
- company-specific names
- confidential operational metrics
- exact internal rule sets that would expose private process details

## Repository Structure
```text
payment-reconciliation-platform/
├─ README.md
├─ docs/
│  ├─ architecture.md
│  ├─ bookstack-knowledge-library.md
│  ├─ business-rules.md
│  ├─ data-flow.md
│  └─ vendor-independence.md
├─ sql/
├─ scripts/
├─ app/
├─ bookstack/
├─ sample_data/
├─ output_examples/
├─ docker/
└─ .gitignore
```

## Example Impact Areas
While this repository uses sanitized examples, the original project was aimed at improving:
- reconciliation speed
- consistency across countries
- traceability of exceptions
- operational maintainability
- departmental knowledge retention
- internal control over business rules
- historical aging review by allowing older balances to be reanalyzed whenever new receipts, payment batches, or reference mappings become available

## Terminology
To keep the case study understandable outside the original internal context:
- **payment batch** = grouped payment block generated on the ERP side
- **receipt reference** = identifier of the external receipt or remittance document

## Resume Version
Designed and prototyped a financial reconciliation platform to replace spreadsheet-based operational workflows across multiple countries. Built a local proof of concept using sanitized CSV inputs, Python, Streamlit, and DuckDB-based SQL validation to test reconciliation logic, exception handling, and operational workflows, while defining the target production architecture in Google Cloud using BigQuery and a containerized Streamlit interface on Cloud Run.

## Demo
Run the small Streamlit demo locally:

```bash
pip install -r requirements.txt
streamlit run app/streamlit_demo.py
```

Run the separate BookStack knowledge-library demo:

```bash
cd bookstack
cp .env.example .env
# Generate APP_KEY, then update .env:
docker run -it --rm --entrypoint /bin/bash lscr.io/linuxserver/bookstack:latest appkey
docker compose up -d
```

BookStack will be available at `http://localhost:6875`.

## Validation
Validate that the sanitized CSV sample data reproduces the published output examples. The second command runs the SQL scripts in DuckDB memory as a local validation substitute for the target warehouse layer:

```bash
python3 tests/validate_examples.py
python3 tests/validate_duckdb_sql.py
```

Build an optional local DuckDB database from the CSV samples and SQL views:

```bash
python3 scripts/build_duckdb_demo.py
```

This creates `local_reconciliation_demo.duckdb`, which is ignored by Git. The repository keeps CSVs as transparent sample inputs while the generated DuckDB file provides a local database artifact for SQL inspection.

Regenerate the deterministic sample dataset:

```bash
python3 scripts/generate_sample_data.py
```

## Related Docs
- [Architecture](docs/architecture.md)
- [Business Rules](docs/business-rules.md)
- [BookStack Knowledge Library](docs/bookstack-knowledge-library.md)
- [Data Flow](docs/data-flow.md)
- [Platform Flow Diagram](docs/platform-flow.svg)
- [Vendor Independence](docs/vendor-independence.md)

## Sample Screenshots
- [Operations dashboard mockup](docs/screenshots/dashboard_overview.svg)
- [Exception review mockup](docs/screenshots/exception_review.svg)

## License
MIT
