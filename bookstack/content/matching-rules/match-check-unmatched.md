# Allocation Status Definitions

## Ready for Allocation

A payment batch is ready for allocation when receipt evidence exists for the same:

- normalized payment reference
- payment amount
- transaction date

These items are considered ready for allocation because the batch and receipt evidence agree.

## Evidence Review

A payment batch enters evidence review when it has a normalized reference, but the platform cannot find an exact receipt match.

Common causes:

- receipt not loaded yet
- amount difference
- date difference
- missing payment-channel mapping
- payment grouped differently in the receipt source

Evidence-review items must not show a matched receipt reference unless the SQL match condition was satisfied.

## Missing Payment Evidence

A payment batch is missing payment evidence when the source description does not provide a reliable reference.

Common causes:

- incomplete batch description
- unsupported payment description format
- reference removed or masked by the source system
- manual adjustment without a traceable receipt reference

## Allocation Rule

Only items with complete receipt evidence are ready to allocate automatically.

Evidence-review and missing-evidence items remain in the open-balance aging queue.
