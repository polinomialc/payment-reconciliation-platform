-- Example: generate deterministic matching keys.

create or replace view schedule_keys as
select
    schedule_id,
    transaction_date,
    amount,
    coalesce(reservation_ref, invoice_ref, acquirer_ref) as primary_ref,
    concat(coalesce(reservation_ref, invoice_ref, acquirer_ref), '|', amount) as amount_key
from parsed_schedules;

create or replace view receipt_keys as
select
    receipt_ref,
    transaction_date,
    gross_amount,
    coalesce(reservation_ref, invoice_ref, acquirer_ref) as primary_ref,
    concat(coalesce(reservation_ref, invoice_ref, acquirer_ref), '|', gross_amount) as amount_key
from parsed_receipts;

