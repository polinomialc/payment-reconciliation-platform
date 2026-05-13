# SQL Reconciliation Walkthrough

This document explains the SQL model behind the demo. The SQL is sanitized and simplified, but it follows the same platform structure used in a production reconciliation workflow.

## Layer 1: Raw To Parsed

File:

```text
sql/01_raw_to_parsed.sql
```

Purpose:

- keep source data recognizable
- normalize dates and amounts
- expose receipt references and payment-batch references
- split useful identifiers from raw descriptive fields
- standardize payment channel and provider status values

Example concept:

```sql
select
    receipt_ref,
    transaction_date,
    contract_type,
    status,
    type_of_transaction,
    your_reference,
    gross_amount
from raw_receipts;
```

This layer avoids business decisions where possible. It prepares the data for consistent matching.

## Layer 2: Key Generation

File:

```text
sql/02_key_generation.sql
```

Purpose:

- derive comparable keys from payment batches and receipts
- extract invoice references, reservation references, and external payment-channel tokens
- attach mapping data when payment providers use their own transaction references
- calculate occurrence counters so repeated references can still be matched deterministically

Why occurrence counters matter:

If the same reference appears multiple times on the same day, a simple join can create false matches. Occurrence counters reduce accidental many-to-many joins by matching the first instance to the first instance, the second to the second, and so on.

Typical key families:

- invoice key
- reservation key
- acquirer or payment-channel token
- reference + amount occurrence
- transaction date
- sign of amount

## Layer 3: Exact Match Candidates

File:

```text
sql/03_reconciliation_logic.sql
```

The first reconciliation layer creates candidate matches. A payment-batch line can be matched to a receipt line when the business reference, amount direction, amount value, and date rule agree.

Simplified pattern:

```sql
select
    p.payment_batch_id,
    r.receipt_ref,
    p.primary_ref,
    p.amount as payment_batch_amount,
    r.gross_amount as receipt_amount,
    'INVOICE_REFERENCE' as match_rule
from payment_batch_keys p
join receipt_keys r
  on p.market_code = r.market_code
 and p.key_inv = r.key_inv
 and p.transaction_date = r.transaction_date
 and sign(p.amount) = sign(r.gross_amount);
```

The same structure can be repeated with different reference priorities:

- invoice reference
- reservation reference
- payment-channel token
- mapped external reference

The final exact match view keeps one best match per payment-batch line using match priority.

## Layer 4: Receipt-Side Exceptions

Not every valid financial event is a simple one-to-one payment match. The current public demo keeps the operational surface compact and separates receipt-side exceptions from normal payment-batch matching.

### Rejected Transactions

A rejected transaction is visible in the receipt feed, but it should not be treated as a normal successful payment. The receipt view keeps it visible as a rejected transaction so the analyst can explain why it does not support allocation.

### Chargebacks

Chargebacks represent a reversal or dispute. They are receipt-side evidence, but they are not treated like normal customer payment settlement. The demo keeps them on the receipt side as a separate outcome so they remain visible without being forced into a clean match.

### Advanced Review Scenarios

The SQL engine still contains hooks for advanced review patterns such as cancellation-fee treatment and amount variance detection. The compact Streamlit demo does not foreground those scenarios; it focuses on the clearer public read-out: matched payment evidence, open review queues, chargebacks, and rejected transactions.

## Layer 5: Reconciled Rows

The reporting layer exposes business-facing outcomes for payment batches and receipts. Internally, SQL uses stable tokens; the Streamlit app maps those tokens to cleaner labels.

Payment-batch outcomes:

- **Matched to receipts**: the payment batch is fully supported by receipt evidence.
- **Review**: one or more payment-batch lines remain open for analyst follow-up.
- **Rejected transaction**: the payment batch is tied to rejected provider evidence.

Receipt outcomes:

- **Linked to payment batches**: receipt evidence is tied back to one or more payment batches.
- **Chargeback**: the receipt contains dispute or reversal evidence.
- **Rejected transaction**: the receipt contains rejected provider-side evidence.
- **Unlinked receipt**: receipt evidence is not yet linked to a payment batch.

Simplified pattern:

```sql
case
    when matched_line_count = line_count
        then 'Matched to receipts'
    when rejected_line_count > 0
        then 'Rejected transaction'
    else 'Review'
end as reconciliation_outcome
```

For receipts, the same idea is applied from the opposite side:

```sql
case
    when chargeback_line_count > 0
        then 'Chargeback'
    when rejected_line_count > 0
        then 'Rejected transaction'
    when unreconciled_receipt_line_count > 0
        then 'Unlinked receipt'
    else 'Linked to payment batches'
end as reconciliation_outcome
```

The key idea is readability. The app shows where the money landed: a receipt, a payment batch, a review queue, a chargeback, or a rejected transaction.

## Layer 6: Reporting Views

File:

```text
sql/04_reporting_views.sql
```

Purpose:

- expose reconciliation by payment batch
- expose reconciliation by receipt
- expose receipt exception classification
- calculate matched amount and open review amount
- support aging review

The operational app consumes these outputs rather than recomputing the full business logic in Python.

## Layer 7: BI Views

File:

```text
sql/05_bi_views.sql
```

Purpose:

- summarize daily KPIs
- publish aging exposure
- publish allocation readiness
- publish exception backlog
- support Metabase dashboards

This keeps management reporting separate from analyst workflow logic.

## How The Model Can Be Adapted

The platform can be adapted by changing rule inputs and SQL precedence, not by rebuilding the whole application.

Examples:

- date tolerance by payment channel
- reference priority by market or source system
- cancellation-fee values by market
- ownership of exception queues
- chargeback handling procedures
- aging bucket definitions
- reporting dimensions

In production, those settings can be moved into governed configuration tables.

## Why SQL Is The Right Center

SQL is the strongest center for this project because:

- analysts and auditors can inspect the logic
- transformations are versionable
- historical data can be reprocessed when mappings improve
- reporting and operational apps can consume the same governed views
- business rules are not hidden inside a UI

The Streamlit app demonstrates the workflow, but the SQL is the actual reconciliation engine.
