# Common Review Scenarios

## Missing Receipt

The payment batch has a reference, but no receipt evidence exists yet.

Expected status: Evidence Review

## Missing Reference

The payment batch does not contain a reliable invoice or reservation reference.

Expected status: Missing Payment Evidence

## Rejected Card Transaction

The receipt exists, but the card transaction was rejected by the payment side.

Expected status: Rejected Card Transaction

## Amount Variance

The reference matches, but the payment amount differs from the expected amount.

Expected status: Amount Variance Review

## Cancellation Fee

A cancelled reservation has a refund movement and a retained cancellation fee.

Expected status: Cancellation Fee Review
