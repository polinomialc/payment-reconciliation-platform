-- Generate deterministic matching keys and occurrence counters.
--
-- Occurrence counters are important for 1-to-1 matching when the same
-- reference/amount appears more than once.

create or replace view payment_batch_keys as
select
    payment_batch_id,
    transaction_date,
    market_code,
    customer,
    item_description,
    amount,
    reservation_ref,
    invoice_ref,
    acquirer_ref,
    is_maestro,
    coalesce(reservation_ref, invoice_ref, acquirer_ref) as primary_ref,
    case
        when invoice_ref is not null then invoice_ref || '|' || cast(amount as varchar)
        else null
    end as key_inv,
    case
        when reservation_ref is not null then reservation_ref || '|' || cast(amount as varchar)
        else null
    end as key_res,
    case
        when acquirer_ref is not null then acquirer_ref || '|' || cast(amount as varchar)
        else null
    end as key_ra,
    row_number() over (
        partition by market_code, coalesce(reservation_ref, invoice_ref, acquirer_ref), amount
        order by payment_batch_id
    ) as occurrence_ref_amount,
    row_number() over (
        partition by market_code, invoice_ref, amount
        order by payment_batch_id
    ) as occurrence_inv,
    row_number() over (
        partition by market_code, reservation_ref, amount
        order by payment_batch_id
    ) as occurrence_res,
    row_number() over (
        partition by market_code, acquirer_ref, amount
        order by payment_batch_id
    ) as occurrence_ra
from parsed_payment_batches;

create or replace view receipt_keys as
select
    receipt_ref,
    transaction_date,
    market_code,
    brand,
    contract_type,
    status,
    type_of_transaction,
    your_reference,
    gross_amount,
    net_amount,
    reference_resolution_method,
    receipt_transaction_type,
    reservation_ref,
    invoice_ref,
    acquirer_ref,
    case
        when upper(contract_type) = 'SECURE E-COMMERCE' then reservation_ref
        when upper(brand) like '%MAESTRO%' then coalesce(invoice_ref, acquirer_ref, reservation_ref)
        else coalesce(invoice_ref, reservation_ref, acquirer_ref)
    end as primary_ref,
    case
        when invoice_ref is not null then invoice_ref || '|' || cast(gross_amount as varchar)
        else null
    end as key_inv,
    case
        when reservation_ref is not null then reservation_ref || '|' || cast(gross_amount as varchar)
        else null
    end as key_res,
    case
        when acquirer_ref is not null then acquirer_ref || '|' || cast(gross_amount as varchar)
        else null
    end as key_ra,
    row_number() over (
        partition by market_code, invoice_ref, gross_amount, transaction_date
        order by receipt_ref
    ) as occurrence_inv,
    row_number() over (
        partition by market_code, reservation_ref, gross_amount, transaction_date
        order by receipt_ref
    ) as occurrence_res,
    row_number() over (
        partition by market_code, acquirer_ref, gross_amount, transaction_date
        order by receipt_ref
    ) as occurrence_ra,
    row_number() over (
        partition by market_code, reservation_ref, gross_amount
        order by transaction_date, receipt_ref
    ) as occurrence_cyb
from parsed_receipts;
