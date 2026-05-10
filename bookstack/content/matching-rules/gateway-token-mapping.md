# Payment-Channel Token Mapping

## Purpose

Payment-channel token mapping resolves payment references that arrive in different formats across payment sources.

## Example

A payment batch may contain a reservation reference while an e-commerce receipt contains a payment-channel token.

The mapping table connects that token to the reservation reference used for reconciliation.

## Review Procedure

1. Identify evidence-review items with a reference that does not appear in receipts.
2. Search the payment-channel mapping for equivalent tokens.
3. Add or correct the mapping when evidence supports it.
4. Rerun reconciliation.
5. Confirm whether the item moves from evidence review to ready for allocation.

## Control Requirement

Every mapping update should include:

- source reference
- target receipt reference
- reason for the update
- reviewer
- approval date
