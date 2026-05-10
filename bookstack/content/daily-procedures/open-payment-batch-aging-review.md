# Open Payment Batch Aging Review

## Purpose

Review payment batches that remain open after deterministic receipt matching.

## Business Definition

An open payment batch is a processed payment block that does not yet have enough receipt evidence for allocation.

Open balances are reviewed by age because older items represent higher operational risk.

## Status Meaning

Evidence review means the payment batch has a usable reference, but no exact receipt match by reference, amount, and date.

Missing payment evidence means the payment batch does not have a reliable reference for deterministic matching.

Ready-for-allocation items are excluded from the open-balance queue because they already have receipt evidence.

## Review Procedure

1. Sort open balances by aging bucket.
2. Prioritize `60+ days`, then `31-60 days`.
3. Check whether a new receipt, corrected reference, or mapping update is available.
4. If evidence is found, update the source mapping or rerun the reconciliation.
5. If evidence is not found, assign the item for operational follow-up.

## Escalation

Escalate items when:

- the balance is over the local materiality threshold
- the item is older than the allowed review window
- the same reference appears in multiple unresolved batches
- a transaction appears to be a refund, chargeback, or correction
