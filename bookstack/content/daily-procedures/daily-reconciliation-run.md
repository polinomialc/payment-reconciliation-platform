# Daily Reconciliation Run

## Purpose

Run the daily financial reconciliation cycle and confirm which payment batches can be allocated, which remain open, and which require review.

## Inputs

- payment batch export
- receipt export
- payment-channel reference mapping
- prior open-balance review notes

## Procedure

1. Load the latest source files into the reconciliation platform.
2. Run the parsing and key-generation SQL layers.
3. Run reconciliation logic.
4. Review summary totals by status.
5. Confirm all ready-for-allocation items have receipt evidence.
6. Send evidence-review and missing-evidence items to open-balance aging review.

## Output

- allocatable payment batch list
- open-balance aging queue
- exception review queue
- reconciliation summary by source and status
