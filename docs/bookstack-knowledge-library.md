# BookStack Knowledge Library

## Purpose
BookStack is part of the target operating model as the department's financial-operations knowledge library.

Its role is not to run the reconciliation logic. Its role is to make the operating knowledge around that logic visible, searchable, auditable, and reusable by the team.

The reconciliation platform centralizes data and rules.

BookStack centralizes the human procedures, business concepts, payment exceptions, and operational context needed to run the finance process correctly.

## Why It Matters
Spreadsheet-based processes often hide knowledge in:
- personal notes
- email threads
- undocumented exceptions
- comments inside files
- local country-specific workarounds
- informal explanations from senior analysts

That creates operational risk. If the person who knows the rule is unavailable, the process becomes slower and harder to audit.

BookStack addresses that by acting as a shared library for:
- finance operations procedures
- aging review steps
- exception-handling playbooks
- rule definitions
- business concepts
- payment-channel behavior
- approval flows
- business glossary
- change history
- onboarding material

## Proposed Book Structure
```text
Book: Financial Operations Knowledge Library
├─ Overview
│  ├─ Platform purpose
│  ├─ Source systems and file types
│  └─ Operating model
├─ Business Concepts
│  ├─ Invoice and reservation references
│  ├─ Payment channels and e-commerce
│  └─ Receipts and payment batches
├─ Daily Procedures
│  ├─ Load receipt exports
│  ├─ Load payment batch exports
│  ├─ Run reconciliation
│  └─ Review open aging
├─ Matching Rules
│  ├─ Ready for allocation definition
│  ├─ Evidence review definition
│  ├─ Missing payment evidence definition
│  ├─ Reference hierarchy
│  └─ Payment-channel token mapping
├─ Exception Handling
│  ├─ Chargebacks
│  ├─ Rejected card transactions
│  ├─ Refunds
│  ├─ Refunds with cancellation fee
│  ├─ Over and under payments
│  └─ Mixed or misapplied payments
├─ Aging Review
│  ├─ Aging buckets
│  ├─ Open-balance review
│  ├─ Escalation criteria
│  └─ Historical reanalysis
├─ Governance
│  ├─ Rule-change request
│  ├─ Validation checklist
│  ├─ Approval matrix
│  └─ Change log
└─ Onboarding
   ├─ Glossary
   ├─ Common scenarios
   └─ Troubleshooting guide
```

## Example Page: Evidence Review Procedure
```text
Title: Reviewing payment batches that require evidence review

Purpose:
Evidence-review items represent payment batches that remain open because receipt evidence did not produce a full deterministic match.

Inputs:
- payment batch identifier
- parsed payment reference
- amount
- transaction date
- available receipt exports
- payment-channel reference mapping file

Procedure:
1. Confirm that the payment batch contains a parseable reference.
2. Search receipt evidence for the same reference, amount, and expected date.
3. If an e-commerce payment-channel token is involved, verify whether a mapping exists.
4. If evidence is missing, keep the item open in aging.
5. If evidence is found later, rerun reconciliation and confirm the updated status.
6. Document any rule exception or mapping correction before applying it.

Expected outcome:
- item remains in evidence review
- item becomes ready for allocation after new evidence or mapping
- item is escalated if no evidence is found after the agreed aging threshold
```

## Example Page: Refund With Cancellation Fee
```text
Title: Refund with cancellation fee

Definition:
A refund with cancellation fee is a customer refund where part of the original payment is retained as a cancellation charge.

Identification:
- receipt reference contains refund wording or a refund code
- receipt reference contains cancellation-fee wording or a cancellation-fee marker
- gross amount is negative
- net amount reflects the retained cancellation fee

Operational treatment:
1. Classify separately from standard payment receipts.
2. Link back to the reservation or invoice reference when available.
3. Confirm whether the cancellation fee should remain allocated.
4. Exclude the item from standard payment-batch matching unless the business rule explicitly requires it.
5. Preserve the classification for reporting and audit review.
```

## Platform Relationship
BookStack complements the technical layers:

| Layer | Responsibility |
| --- | --- |
| SQL / BigQuery / DuckDB | Transform data, generate keys, apply matching rules, classify exceptions |
| Streamlit | Guide operational review and aging analysis |
| Metabase | Provide KPI and management reporting |
| BookStack | Store procedures, business concepts, exception playbooks, rule explanations, governance notes, and department knowledge |

## Governance Benefit
Using BookStack makes rule ownership clearer.

When a reconciliation rule changes, the team can update:
- the SQL logic
- the validation output
- the BookStack rule explanation
- the operating procedure
- the change log

That closes the gap between technical implementation and business understanding.
