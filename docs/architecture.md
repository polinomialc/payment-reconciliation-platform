# Architecture

## Design Principle
Keep reconciliation logic in SQL and the application layer thin.

This project separates concerns into four layers:

1. **Landing / Raw**
   - source exports land unchanged
   - raw files are preserved for auditability

2. **Transformation / Logic**
   - parsing and normalization
   - key generation
   - matching rules
   - exception handling

3. **Reporting / Views**
   - reconciliation by payment batch
   - reconciliation by receipt
   - exception reporting
   - aging support views

4. **Consumption**
   - Streamlit for guided operational execution
   - Metabase for reporting
   - BookStack as the departmental procedure and knowledge library

5. **Knowledge / Governance**
   - rule definitions and business glossary
   - exception-handling procedures
   - aging review playbooks
   - change history and approval notes
   - onboarding and troubleshooting material

## Local PoC
- sanitized CSV sample inputs
- Python
- Streamlit
- DuckDB used only as an in-memory SQL validation engine
- CSV and spreadsheet outputs

The local demo keeps its inputs in CSV files. DuckDB is included to execute and validate the SQL logic locally against those files, not as the source system or the intended production database.

## Production Target
- Google Drive / Cloud Storage landing zone
- BigQuery raw tables
- BigQuery SQL views
- Streamlit container on Cloud Run
- Metabase dashboards for reporting
- BookStack for departmental knowledge management and governed procedures

## Why Keep Logic Out Of The App
- easier to audit
- easier to test
- easier to migrate from local PoC to cloud
- business-rule changes do not require application rewrites

## Why Include BookStack
Reconciliation platforms do not fail only because of code. They also fail when operational knowledge is scattered across spreadsheets, emails, and individual analysts.

BookStack is included as the shared library for the department's procedures and rule knowledge. It stores how to interpret matched items, open checks, chargebacks, advanced refund scenarios, aging thresholds, escalation criteria, and rule-change approvals.

## Platform Flow
![Payment reconciliation platform flow](platform-flow.svg)

## Tool Responsibilities

The platform separates responsibilities across tools:

- **BigQuery** is the production data and SQL logic layer.
- **Streamlit** is the operational workflow interface for analysts.
- **Metabase** is the management reporting layer for KPIs, exposure, and backlog.
- **BookStack** is the business knowledge and governance library.
- **DuckDB** is used only for local SQL validation in the local demo.

See [Tooling Roles](tooling-roles.md) for the full breakdown.
