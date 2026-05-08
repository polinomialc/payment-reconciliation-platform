-- Example: normalize raw payment-batch and receipt inputs into parsed datasets.

create or replace view parsed_payment_batches as
select
    payment_batch_id,
    transaction_date,
    amount,
    item_description,
    regexp_extract(item_description, 'RES[: ]*([0-9]{10})', 1) as reservation_ref,
    regexp_extract(item_description, 'INV[: ]*([0-9]{12})', 1) as invoice_ref,
    regexp_extract(item_description, 'RA[: ]*([0-9]+)', 1) as acquirer_ref
from raw_payment_batches;

create or replace view parsed_receipts as
select
    receipt_ref,
    transaction_date,
    gross_amount,
    net_amount,
    contract_type,
    your_reference,
    regexp_extract(your_reference, 'RES[: ]*([0-9]{10})', 1) as reservation_ref,
    regexp_extract(your_reference, 'INV[: ]*([0-9]{12})', 1) as invoice_ref,
    regexp_extract(your_reference, 'RA[: ]*([0-9]+)', 1) as acquirer_ref
from raw_receipts;
