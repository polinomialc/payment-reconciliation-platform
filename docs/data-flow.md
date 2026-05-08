# Data Flow

## Inputs
- payment batch exports
- receipt exports
- reference mapping files
- optional post-treatment adjustments

## Flow
1. load raw files
2. parse relevant identifiers
3. standardize dates and amounts
4. generate matching keys
5. apply reconciliation logic
6. expose outputs for operations and reporting

## Output Types
- reconciliation by payment batch
- reconciliation by receipt
- exception review
- downstream aging support
