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

To address that, a local proof of concept was built in **DuckDB + Python + Streamlit** to validate:
- reconciliation logic
- exception handling
- performance
- operational usability

The intended production architecture was designed for **Google Cloud**, with:
- **BigQuery** as the centralized data and logic layer
- **Streamlit** as the operational interface
- **Cloud Run** as the container runtime
- **Metabase** as the reporting layer
- **BookStack** as the documentation and governance layer

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

Core rule areas include:
- invoice matching
- reservation matching
- acquirer-reference matching
- payment-gateway token resolution
- chargeback handling
- cancellation fee handling for fees charged to the customer after reservation cancellation
- overpayment detection
- intercompany payment detection
- mixed or misapplied payment detection
- country-specific exception logic

## Architecture
### Local Proof of Concept
- DuckDB
- Python
- Streamlit
- CSV / XLSX operational outputs

### Production Target
- Google Drive or cloud landing folders by country
- BigQuery raw tables
- SQL transformation and reporting views in BigQuery
- Streamlit deployed as a container on Cloud Run
- Metabase dashboards
- BookStack documentation

The main architectural principle is simple:

> keep business logic in SQL, keep the application layer thin

That makes the platform easier to audit, easier to evolve, and easier to migrate from a local PoC to a cloud production model.

## Key Design Decisions
### 1. Local first, cloud ready
DuckDB was used to validate the model quickly and cheaply, but the target design was always a cloud-native architecture.

### 2. Logic centralized in SQL
Reconciliation logic stays in views and transformation layers rather than being spread across UI code.

### 3. Vendor independence
The project was explicitly designed to reduce dependence on third-party reconciliation platforms and give the department direct ownership of rules, outputs, and troubleshooting.

### 4. Governance by design
Raw data is preserved, transformations are explicit, and reporting outputs can be traced back to governed rule layers.

## What This Repository Contains
- architecture notes
- business-rule documentation
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
│  ├─ business-rules.md
│  ├─ data-flow.md
│  └─ vendor-independence.md
├─ sql/
├─ app/
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
- internal control over business rules
- historical aging review by allowing older balances to be reanalyzed whenever new receipts, payment batches, or reference mappings become available

## Terminology
To keep the case study understandable outside the original internal context:
- **payment batch** = grouped payment block generated on the ERP side
- **receipt reference** = identifier of the external receipt or remittance document

## Resume Version
Designed and prototyped a financial reconciliation platform to replace spreadsheet-based operational workflows across multiple countries. Built a local proof of concept in DuckDB and Python to validate reconciliation logic, exception handling, and operational workflows, while defining the target production architecture in Google Cloud using BigQuery and a containerized Streamlit interface on Cloud Run.

## Demo
Run the small Streamlit demo locally:

```bash
pip install streamlit pandas
streamlit run app/streamlit_demo.py
```

## Related Docs
- [Architecture](docs/architecture.md)
- [Business Rules](docs/business-rules.md)
- [Data Flow](docs/data-flow.md)
- [Vendor Independence](docs/vendor-independence.md)

## Sample Screenshots
- [Operations dashboard mockup](docs/screenshots/dashboard_overview.svg)
- [Exception review mockup](docs/screenshots/exception_review.svg)

## License
MIT
