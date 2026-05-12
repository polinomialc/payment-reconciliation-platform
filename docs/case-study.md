# Case Study

## Context

Finance operations teams often inherit reconciliation processes that work, but only because analysts know how to keep a chain of spreadsheets alive. The process may start with reliable source exports, but the actual operating model becomes difficult to audit when matching logic, exception notes, aging calculations, and follow-up actions live across separate files.

This project models a cleaner platform pattern for that problem. It is public and sanitized, but it keeps the important structure: payment batches, receipt files, reference mapping, matching logic, exception classification, operational review, reporting, and documented procedures.

## Business Problem

The original workflow pattern had several risks:

- matching depended on repeated spreadsheet operations
- rules could drift between analysts, markets, and reporting cycles
- exception handling was difficult to standardize
- open balances could age without a clear audit trail
- rule changes required too much manual coordination
- business knowledge lived outside the system that analysts used every day

The goal was not only to make a dashboard. The goal was to turn reconciliation into a controlled workflow.

## Platform Response

The proposed platform separates the process into four responsibilities:

1. **Governed SQL logic**
   BigQuery is the intended production layer for parsing, key generation, matching, exception classification, aging, and reporting views.

2. **Operational workflow**
   Streamlit gives analysts a focused interface for payment-batch reconciliation, receipt-level reconciliation, open checks, chargebacks, and rejected receipt transactions.

3. **Management visibility**
   Metabase consumes reporting views for exposure, backlog, trend, and KPI dashboards.

4. **Knowledge governance**
   BookStack stores business definitions, procedures, exception playbooks, and rule-change documentation.

DuckDB is included only so the public demo can run SQL locally against sanitized CSVs.

## Design Principles

- Preserve raw inputs before transformation.
- Express matching logic in SQL instead of UI code.
- Make every output traceable to a payment batch, receipt line, and rule outcome.
- Separate matched evidence from open checks and receipt-side exceptions.
- Keep business terminology understandable outside the original company context.
- Make the platform adaptable by changing rules and reference priorities, not by rewriting the whole app.

## What The Demo Proves

The demo proves that the reconciliation model can:

- parse receipt and payment-batch files
- normalize references across payment channels
- match transactions using deterministic keys
- show how payment-batch totals split across linked receipts and open check queues
- isolate chargebacks and rejected card transactions on the receipt side
- produce open-balance aging views
- expose both operational and management outputs from the same governed data layer
- support a knowledge library for business procedures and rule explanations

## Why This Is Transferable

Although the example data uses financial operations terminology, the pattern is not specific to one industry. Any business that receives money through multiple channels can face the same problem:

- retail settlement
- subscription billing
- marketplace payouts
- insurance payments
- travel and booking platforms
- logistics billing
- healthcare payment posting
- wholesale invoice settlement

The core idea is reusable: compare expected financial records against received financial evidence, classify differences, expose the work queue, and make the rules auditable.

## Interview Framing

A concise explanation:

> I built a sanitized case study of a reconciliation platform. The business problem was spreadsheet-heavy financial operations: payment batches, receipts, reference mappings, open balances, and exception follow-up. The technical solution keeps business logic in SQL, uses Streamlit for analyst workflows, Metabase for management reporting, and BookStack for procedure governance. The local demo runs on CSVs and DuckDB, but the production target is BigQuery-centered.

## AI-Assisted Development Note

The repository does not need a banner saying the code was AI-assisted. Most public repositories do not disclose development tooling in the README unless the tooling itself is the subject of the project.

The honest interview position is different:

> I directed the business logic, architecture, terminology, validation, and review criteria, and used AI as an implementation accelerator. I can explain the SQL layers, the data model, the containers, and the operational workflow because I designed the process and validated the outputs.

That is a better framing than making the repository look like a disclaimer.
