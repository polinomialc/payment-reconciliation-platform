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

The live demo keeps the visible outcomes intentionally simple:

- **Matched to receipts**: payment-batch evidence and receipt evidence agree.
- **Check**: the payment batch remains open and still needs analyst follow-up.
- **Rejected**: the payment batch is tied to rejected provider evidence and should not be treated as a normal successful payment.
- **Linked to payment batches**: the receipt has usable evidence tied back to payment batches.
- **Chargeback**: the receipt line represents a dispute or reversal.
- **Rejected receipt**: the receipt contains rejected provider-side evidence.
- **Unlinked receipt**: the receipt line is still outside the current matching result.

More advanced scenarios can still be documented in the portfolio, but they are not pushed into the compact Streamlit surface.

## Rule Themes

- Prefer deterministic reference + amount + date matching where possible.
- Use payment-channel mapping when external provider references need translation.
- Use occurrence counters to avoid accidental many-to-many joins.
- Keep rejected transactions out of allocation-ready outputs.
- Treat chargebacks as receipt-side evidence that follows a separate exception procedure.
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
