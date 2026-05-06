# Business Rules

This repository contains a simplified, sanitized version of the rule model used in the project.

## Matching Keys
Typical reconciliation keys can include:
- invoice reference
- reservation reference
- acquirer reference
- e-commerce token
- amount
- transaction date

## Typical Match Outcomes
- `MATCH`
- `CHECK`
- `CFEE` for cancellation-fee patterns
- `OVP` for overpayment cases
- `CHARGEBACK`

## Example Rule Themes
- prefer deterministic identifier + amount + date when possible
- tolerate date offsets only when justified by a country-specific exception
- treat cancellation-fee cases as paired financial events
- distinguish face-to-face vs e-commerce receipts based on available reference structures
- preserve raw data and apply all logic in the transformation layer

## Governance Principle
Rules should be:
- explicit
- versioned
- explainable to business users
- easy to adjust internally without vendor dependency

