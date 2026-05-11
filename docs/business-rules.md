# Business Rules

This repository contains a simplified, sanitized rule model for payment reconciliation. The rules are written with generic terminology so the case study can be understood outside the original operating context.

## Core Concepts

- **Payment batch**: a grouped financial record from the internal accounting or payment-processing side.
- **Receipt**: external payment evidence, often received from a bank, payment provider, or settlement file.
- **Receipt line**: one transaction inside a receipt.
- **Business reference**: the normalized reference used to compare the receipt line with the payment batch. It can come from an invoice, reservation, payment-channel token, or mapped external reference.
- **Reference mapping**: a bridge table used when the payment provider emits a token that must be translated back to an internal business reference.

## Matching Inputs

Typical reconciliation keys can include:

- invoice reference
- reservation reference
- acquirer reference
- payment-channel transaction token
- mapped business reference
- transaction date
- amount
- sign of amount
- occurrence counter for repeated references

## Payment-Channel Reference Mapping

Some payment flows do not expose the internal invoice or reservation reference directly. Instead, the payment provider emits an external token.

In those cases, reconciliation needs a mapping layer that links:

- external payment-channel token
- internal business reference
- transaction date
- amount
- channel or market

This keeps matching deterministic while still supporting payment methods that do not carry the original business reference in the receipt file.

## Public Outcomes

The demo uses business-facing outcomes instead of internal shorthand:

- **Allocation Ready**: receipt evidence and payment-batch evidence agree.
- **Evidence Review Required**: a usable reference exists, but exact evidence is incomplete or requires review.
- **Missing Receipt Evidence**: the payment batch remains open because no receipt evidence was found.
- **Rejected Card Transaction**: the provider rejected the transaction; it should not be allocated as a successful payment.
- **Chargeback Review**: the receipt line represents a dispute or reversal that needs a separate treatment.
- **Cancellation Fee Review**: a refund and a cancellation fee must be reviewed together before financial treatment.
- **Amount Variance Review**: the reference chain exists, but the value is above or below the expected amount.

## Rule Themes

- Prefer deterministic reference + amount + date matching where possible.
- Use payment-channel mapping when external provider references need translation.
- Use occurrence counters to avoid accidental many-to-many joins.
- Keep rejected transactions out of allocation-ready outputs.
- Treat chargebacks as receipt-side evidence that follows a separate exception procedure.
- Identify cancellation-fee cases as financial-treatment items, not clean allocations.
- Identify amount variance cases when the reference is present but the value differs.
- Preserve raw data and apply all logic in the SQL transformation layer.

## Historical Reanalysis

One important capability of this model is that historical aging can be revisited whenever the data picture improves.

If new receipts, payment batches, or reference-mapping files are imported later, older open balances can be recalculated using the same governed logic layer. This makes retrospective aging review far easier than in spreadsheet-only workflows.

## Governance Principle

Rules should be:

- explicit
- versioned
- explainable to business users
- testable against sample data
- documented in operational procedures
- easy to adjust internally without vendor dependency
