# Business Rules

This repository contains a simplified, sanitized version of the rule model used in the project.

## Matching Keys
Typical reconciliation keys can include:
- invoice reference
- reservation reference
- acquirer reference
- e-commerce token
- payment-channel transaction token
- amount
- transaction date

## Payment Gateway Reference Mapping
In some payment flows, customer prepayment transactions are not emitted with the original internal invoice reference.

Instead, the payment provider or channel may generate its own external transaction token. In those cases, reconciliation requires an intermediate mapping layer that links:
- external payment-channel transaction token
- internal merchant or reservation reference
- transaction date
- amount

This repository uses generic terminology for that layer:
- **payment-channel token**
- **reference mapping dataset**

This keeps the case study platform-agnostic while still representing a common reconciliation problem in payment operations.

## Typical Match Outcomes
- ready for allocation
- evidence review
- cancellation fee review for fees charged to the customer after reservation cancellation
- amount variance review for over/under payment cases
- `CHARGEBACK`

## Example Rule Themes
- prefer deterministic identifier + amount + date when possible
- tolerate date offsets only when justified by a country-specific exception
- treat cancellation-fee cases as customer cancellation charges linked back to the reservation
- distinguish face-to-face vs e-commerce receipts based on available reference structures
- identify intercompany payment scenarios separately from standard customer settlement flows
- detect mixed or misapplied payments when funds appear to settle the wrong balance or reference chain
- preserve raw data and apply all logic in the transformation layer

## Historical Reanalysis
One important capability of this model is that historical aging can be revisited whenever the data picture improves.

If new receipts, payment batches, or reference-mapping files are imported later, older open balances can be recalculated and reinterpreted using the same governed logic layer. This makes retrospective aging review far easier than in spreadsheet-only workflows.

## Governance Principle
Rules should be:
- explicit
- versioned
- explainable to business users
- easy to adjust internally without vendor dependency
