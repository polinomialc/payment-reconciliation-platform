# Chargeback Review

## Purpose

Identify receipt transactions that represent chargebacks and route them outside the standard payment allocation flow.

## Business Meaning

A chargeback is not a normal customer payment.

It usually represents a customer dispute, card-scheme adjustment, reversal, or bank-side recovery flow.

Because it changes the payment position after the original transaction, it must be handled as a business exception, not as a standard receipt match.

## Detection

The SQL layer classifies receipt references containing chargeback indicators such as `CHARGEBACK` or `CHB`.

## Procedure

1. Confirm the receipt transaction type is `CHARGEBACK`.
2. Identify the original invoice or reservation reference when available.
3. Check whether the original payment batch had already been allocated.
4. Confirm whether the chargeback creates an open balance, reversal, or manual adjustment.
5. Route the item to the exception owner.
6. Document the final handling decision.

## Output

Chargeback items should be reported separately from normal allocation evidence and included in exception reporting.
