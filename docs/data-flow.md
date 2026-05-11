# Data Flow

![Payment reconciliation platform flow](platform-flow.svg)

## Inputs

- payment batch exports
- receipt exports
- payment-channel reference mapping files
- optional operational adjustment files

## Transformation Flow

1. Load raw files unchanged.
2. Parse relevant identifiers from payment-batch and receipt fields.
3. Standardize dates, amounts, channels, and provider statuses.
4. Generate comparable business keys.
5. Apply matching logic by reference, amount, sign, and date rule.
6. Classify exceptions such as rejected transactions, chargebacks, cancellation-fee cases, amount variances, and missing evidence.
7. Publish operational views for Streamlit.
8. Publish BI views for Metabase.
9. Document procedures, definitions, and rule-change governance in BookStack.

## Output Types

- reconciliation by payment batch
- reconciliation by receipt
- receipt exception classification
- open-balance aging support
- allocation readiness
- management KPI views
- governed operational procedures and rule documentation
