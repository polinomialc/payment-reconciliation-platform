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
   - BookStack for governance and documentation

## Local PoC
- DuckDB
- Python
- Streamlit
- CSV and spreadsheet outputs

## Production Target
- Google Drive / Cloud Storage landing zone
- BigQuery raw tables
- BigQuery SQL views
- Streamlit container on Cloud Run
- optional BI and documentation services alongside the main interface

## Why Keep Logic Out Of The App
- easier to audit
- easier to test
- easier to migrate from local PoC to cloud
- business-rule changes do not require application rewrites
