# Payment Channels and E-Commerce

## Purpose

Describe how payment channels affect reconciliation behavior.

## Payment Channel

A payment channel is the route used to process the customer transaction.

Examples include:

- card-present payment
- e-commerce payment
- payment gateway transaction
- manual adjustment

The channel matters because each source can carry different reference formats.

## E-Commerce

E-commerce is an online payment channel.

For e-commerce transactions, the receipt may contain a payment-channel token instead of the invoice or reservation reference directly.

The reconciliation platform uses a mapping table to translate that token into the reservation reference used by the internal payment batch.

## Operational Guidance

If an e-commerce receipt does not match a payment batch, first check whether the token-to-reservation mapping exists and is current.

If the mapping is missing or stale, the item should remain in review until the mapping can be validated.
