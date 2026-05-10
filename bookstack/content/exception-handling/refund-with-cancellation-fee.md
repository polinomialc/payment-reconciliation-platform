# Refund With Cancellation Fee

## Purpose

Identify refunds where a cancellation fee was charged to the customer after a reservation cancellation.

## Business Meaning

These transactions are not standard payment receipts.

They combine a customer refund with a retained cancellation fee.

The cancellation fee is a business charge linked to the cancelled reservation, so it must be treated separately from the refunded amount.

## Detection

The SQL layer classifies receipt references as `REFUND_WITH_CANCELLATION_FEE` when the receipt indicates both:

- refund behavior
- cancellation fee behavior

## Procedure

1. Confirm the reservation reference.
2. Confirm the refund amount.
3. Confirm the cancellation fee amount.
4. Check whether the receipt amount equals refund plus retained fee.
5. Route the retained fee to the correct financial treatment.
6. Document the handling decision in the exception log.

## Output

These items should remain separate from standard matched allocations.
