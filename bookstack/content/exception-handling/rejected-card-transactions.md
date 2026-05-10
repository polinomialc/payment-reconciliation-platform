# Rejected Card Transactions

## Purpose

Explain how to handle card transactions attempted by the customer but rejected by the bank, acquirer, or payment processor.

## Business Meaning

A rejected transaction means the customer attempted a card payment, but the payment was not accepted by the payment side.

Rejected transactions should not be treated as standard allocatable receipts.

## Common Causes

- insufficient funds
- card authorization failure
- bank rejection
- payment processor rejection
- technical rejection after authorization attempt

## Reconciliation Treatment

If a receipt line is marked as rejected, the rejected status overrides standard match behavior.

Even when the reference and amount appear to match a payment batch, the item remains an exception because the payment did not settle normally.

## Procedure

1. Confirm the rejected status in the receipt source.
2. Identify the invoice or reservation reference.
3. Check whether a later successful payment exists.
4. Keep the payment batch open if no successful payment evidence exists.
5. Document the review outcome.
