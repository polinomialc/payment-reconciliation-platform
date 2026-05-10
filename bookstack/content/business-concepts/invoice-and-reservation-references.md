# Invoice and Reservation References

## Purpose

Explain the core business references used by the finance operations process.

## Invoice Reference

An invoice reference identifies the financial document used for accounting and allocation.

In the reconciliation logic this is represented as `INV`.

The invoice reference is useful when the receipt source and internal payment batch both carry the same financial document identifier.

## Reservation Reference

A reservation reference identifies the underlying car-rental booking.

In the reconciliation logic this is represented as `RES`.

The reservation reference is important because some payment sources do not carry the invoice number directly. In those cases, the reservation can still connect the customer payment, refund, cancellation fee, or exception back to the operational booking.

## Operational Guidance

Use invoice references first when both sides provide a clean invoice identifier.

Use reservation references when the payment evidence relates to the booking rather than the invoice.

If neither reference is reliable, keep the item in review until additional evidence is available.
