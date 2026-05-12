-- Generate deterministic reconciliation keys and 1:1 occurrence counters.
--
-- The public demo mirrors the structure of a real reconciliation engine:
-- line-level references are parsed first, then keys are created for invoice,
-- reservation, acquirer, and gateway-driven flows.

create or replace view payment_batch_keys as
select
    payment_batch_line_id,
    payment_batch_id,
    transaction_date,
    market_code,
    channel_type,
    customer_name,
    customer_number,
    item_description,
    line_total,
    reservation_ref,
    invoice_ref,
    acquirer_reference,
    reference_parse_status,
    coalesce(invoice_ref, reservation_ref, acquirer_reference) as primary_reference,
    case
        when invoice_ref is not null then invoice_ref || '|' || printf('%.2f', line_total)
        else null
    end as key_invoice,
    case
        when reservation_ref is not null then reservation_ref || '|' || printf('%.2f', line_total)
        else null
    end as key_reservation,
    case
        when acquirer_reference is not null then acquirer_reference || '|' || printf('%.2f', line_total)
        else null
    end as key_acquirer,
    row_number() over (
        partition by market_code, invoice_ref, line_total
        order by transaction_date, payment_batch_line_id
    ) as occurrence_invoice,
    row_number() over (
        partition by market_code, reservation_ref, line_total
        order by transaction_date, payment_batch_line_id
    ) as occurrence_reservation,
    row_number() over (
        partition by market_code, acquirer_reference, line_total
        order by transaction_date, payment_batch_line_id
    ) as occurrence_acquirer
from parsed_payment_batch_lines;

create or replace view receipt_keys as
select
    receipt_line_id,
    receipt_ref,
    transaction_date,
    transaction_time,
    market_code,
    channel_type,
    contract_type,
    card_brand,
    transaction_status,
    transaction_type,
    source_capture_method,
    your_reference,
    gateway_token,
    acquirer_reference,
    gross_amount,
    net_amount,
    terminal_id,
    direct_reservation_ref,
    reservation_ref,
    invoice_ref,
    chargeback_target_ref,
    receipt_exception_type,
    reference_resolution_method,
    coalesce(invoice_ref, reservation_ref, acquirer_reference, chargeback_target_ref) as primary_reference,
    case
        when invoice_ref is not null then invoice_ref || '|' || printf('%.2f', gross_amount)
        else null
    end as key_invoice,
    case
        when reservation_ref is not null then reservation_ref || '|' || printf('%.2f', gross_amount)
        else null
    end as key_reservation,
    case
        when acquirer_reference is not null then acquirer_reference || '|' || printf('%.2f', gross_amount)
        else null
    end as key_acquirer,
    row_number() over (
        partition by market_code, invoice_ref, gross_amount
        order by transaction_date, transaction_time, receipt_line_id
    ) as occurrence_invoice,
    row_number() over (
        partition by market_code, reservation_ref, gross_amount
        order by transaction_date, transaction_time, receipt_line_id
    ) as occurrence_reservation,
    row_number() over (
        partition by market_code, acquirer_reference, gross_amount
        order by transaction_date, transaction_time, receipt_line_id
    ) as occurrence_acquirer,
    row_number() over (
        partition by market_code, reservation_ref, gross_amount
        order by transaction_date, transaction_time, receipt_line_id
    ) as occurrence_gateway
from parsed_receipt_lines;
