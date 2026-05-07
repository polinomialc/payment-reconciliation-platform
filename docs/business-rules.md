# Business Rules

This repository contains a simplified, sanitized version of the rule model used in the project.

## Matching Keys
Typical reconciliation keys can include:
- invoice reference
- reservation reference
- acquirer reference
- e-commerce token
- payment-gateway transaction token
- amount
- transaction date

## Payment Gateway Reference Mapping
In some payment flows, customer prepayment transactions are not emitted with the original internal invoice reference.

Instead, the payment provider or gateway may generate its own external transaction token. In those cases, reconciliation requires an intermediate mapping layer that links:
- external gateway transaction token
- internal merchant or reservation reference
- transaction date
- amount

This repository uses generic terminology for that layer:
- **payment-gateway token**
- **reference mapping dataset**

This keeps the case study platform-agnostic while still representing a common reconciliation problem in payment operations.

## Typical Match Outcomes
- `MATCH`
- `CHECK`
- `CFEE` for cancellation fees charged to the customer after reservation cancellation
- `OVP` for overpayment cases
- `CHARGEBACK`

## Example Rule Themes
- prefer deterministic identifier + amount + date when possible
- tolerate date offsets only when justified by a country-specific exception
- treat cancellation-fee cases as customer cancellation charges linked back to the reservation
- distinguish face-to-face vs e-commerce receipts based on available reference structures
- preserve raw data and apply all logic in the transformation layer

## Governance Principle
Rules should be:
- explicit
- versioned
- explainable to business users
- easy to adjust internally without vendor dependency
