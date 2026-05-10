-- Reporting outputs used by the demo app and validation tests.

create or replace view reconciliation_by_payment_batch as
select
    payment_batch_id,
    receipt_ref,
    reconciliation_outcome,
    count(*) as row_count,
    sum(payment_batch_amount) as payment_batch_total
from reconciled_rows
group by 1, 2, 3;

create or replace view reconciliation_by_receipt as
select
    receipt_ref,
    reconciliation_outcome,
    count(*) as row_count,
    max(receipt_amount) as receipt_total
from reconciled_rows
where receipt_ref is not null
group by 1, 2;

create or replace view receipt_exception_classification as
select
    receipt_ref,
    receipt_transaction_type,
    transaction_date,
    gross_amount,
    net_amount,
    your_reference
from parsed_receipts
where receipt_transaction_type <> 'STANDARD_PAYMENT';
