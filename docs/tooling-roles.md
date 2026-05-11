# Tooling Roles

This project intentionally separates operational workflow, management reporting, knowledge governance, and data execution.

## Streamlit

**Role:** operational execution.

Streamlit is the analyst-facing workflow layer. It is used to review payment receipts, inspect line-level reconciliation, identify linked payment batches, and route exceptions to the correct operational queue.

Typical users:
- reconciliation analysts
- finance operations analysts
- process owners reviewing open items

Typical use cases:
- receipt reconciliation
- open-balance aging review
- allocation evidence review
- exception investigation

## Metabase

**Role:** management reporting.

Metabase consumes BI-facing SQL views and turns them into dashboards for management visibility. It is not the place where reconciliation actions happen; it is the place where leads monitor volume, exposure, backlog, and trends.

Typical users:
- team leads
- finance operations managers
- stakeholders reviewing process performance

Typical use cases:
- allocation readiness by day
- open exposure by aging bucket
- exception backlog by outcome
- chargeback and refund exception trends
- market-level backlog comparison

## BookStack

**Role:** business knowledge and governance.

BookStack stores the business concepts, operating procedures, exception playbooks, rule definitions, and rule-change governance that support the platform.

Typical users:
- analysts learning the process
- process owners maintaining procedures
- managers reviewing rule definitions and approvals

Typical use cases:
- document reconciliation rules
- explain chargebacks, rejected payments, cancellation fees, and amount variances
- maintain daily procedure checklists
- preserve department knowledge outside spreadsheets and private notes

## BigQuery

**Role:** production data and logic layer.

BigQuery is the intended production warehouse layer. Raw source data would land in BigQuery, and governed SQL views would apply parsing, key generation, reconciliation logic, exception classification, reporting, and aging outputs.

## DuckDB

**Role:** local SQL validation.

DuckDB is not the target production database. It is used locally to prove that the SQL scripts execute against the sanitized CSV samples and reproduce the published reconciliation outputs.

## Summary

```text
BigQuery  = production data and SQL logic layer
Streamlit = operational workflow
Metabase  = management reporting
BookStack = procedures, rules, and knowledge governance
DuckDB    = local SQL validation
```
