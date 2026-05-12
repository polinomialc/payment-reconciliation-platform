-- Parse sanitized raw exports into realistic operational structures.
--
-- The public demo keeps the form of a payment-operations dataset while using
-- fake values and generic wording:
-- - payment batch lines coming from an ERP settlement export
-- - receipt lines coming from payment-provider exports
-- - gateway-token mapping for e-commerce prepayments
-- - invoice-only card-present examples handled without leaking internal terminology

create or replace view market_rules as
select * from (
    values
        ('GB', 45.00::decimal(18, 2)),
        ('DE', 50.00::decimal(18, 2)),
        ('ES', 50.00::decimal(18, 2))
) as t(market_code, cancellation_fee_amount);

create or replace view channel_rules as
select * from (
    values
        ('E_COMMERCE', 3),
        ('CARD_PRESENT', 0)
) as t(channel_type, date_window_days);

create or replace view parsed_payment_batch_lines as
select
    payment_batch_line_id,
    payment_batch_id,
    cast(transaction_date as date) as transaction_date,
    upper(trim(market_code)) as market_code,
    upper(trim(channel_type)) as channel_type,
    trim(customer_name) as customer_name,
    trim(customer_number) as customer_number,
    trim(item_description) as item_description,
    cast(line_total as decimal(18, 2)) as line_total,
    nullif(regexp_extract(item_description, 'RES[: ]*([0-9]{10})', 1), '') as reservation_ref,
    nullif(regexp_extract(item_description, 'INV[: ]*([0-9]{12})', 1), '') as invoice_ref,
    nullif(regexp_extract(item_description, 'RA[: ]*([0-9]{6,20})', 1), '') as acquirer_reference,
    case
        when regexp_extract(item_description, 'RES[: ]*([0-9]{10})', 1) <> ''
          or regexp_extract(item_description, 'INV[: ]*([0-9]{12})', 1) <> ''
          or regexp_extract(item_description, 'RA[: ]*([0-9]{6,20})', 1) <> ''
            then 'PARSED'
        else 'UNRESOLVED'
    end as reference_parse_status
from raw_payment_batches;

create or replace view parsed_receipt_lines as
with extracted as (
    select
        receipt_line_id,
        receipt_ref,
        cast(transaction_date as date) as transaction_date,
        cast(transaction_time as time) as transaction_time,
        upper(trim(market_code)) as market_code,
        upper(trim(channel_type)) as channel_type,
        trim(contract_type) as contract_type,
        trim(card_brand) as card_brand,
        trim(transaction_status) as transaction_status,
        trim(transaction_type) as transaction_type,
        trim(source_capture_method) as source_capture_method,
        trim(your_reference) as your_reference,
        nullif(trim(cast(acquirer_reference as varchar)), '') as acquirer_reference_raw,
        cast(gross_amount as decimal(18, 2)) as gross_amount,
        cast(net_amount as decimal(18, 2)) as net_amount,
        trim(terminal_id) as terminal_id,
        nullif(regexp_extract(your_reference, '^([A-Z0-9]{8,20})', 1), '') as gateway_token,
        nullif(regexp_extract(your_reference, 'RES[: ]*([0-9]+)', 1), '') as direct_reservation_ref_raw,
        nullif(regexp_extract(your_reference, 'INV[: ]*([0-9]{12})', 1), '') as invoice_ref,
        case
            when upper(transaction_type) like '%CHARGEBACK%'
                then nullif(regexp_extract(your_reference, '([0-9]{10})', 1), '')
            else null
        end as chargeback_target_ref,
        nullif(regexp_extract(your_reference, 'RA[: ]*([0-9]{6,20})', 1), '') as acquirer_reference_from_text
    from raw_receipts
),
mapped as (
    select
        e.*,
        g.merchant_reference as gateway_merchant_reference
    from extracted e
    left join raw_gateway_reference_mapping g
      on e.gateway_token = g.gateway_token
     and e.market_code = upper(trim(g.market_code))
)
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
    coalesce(acquirer_reference_raw, acquirer_reference_from_text) as acquirer_reference,
    gross_amount,
    net_amount,
    terminal_id,
    direct_reservation_ref_raw as direct_reservation_ref,
    invoice_ref,
    chargeback_target_ref,
    case
        when channel_type = 'E_COMMERCE' then cast(gateway_merchant_reference as varchar)
        else coalesce(direct_reservation_ref_raw, chargeback_target_ref)
    end as reservation_ref,
    case
        when upper(transaction_type) like '%CHARGEBACK%'
            then 'CHARGEBACK'
        when replace(upper(transaction_type), '_', ' ') like '%REFUND%FEE%'
            then 'REFUND_WITH_CANCELLATION_FEE'
        when transaction_status = 'Rejected'
            then 'REJECTED_CARD_TRANSACTION'
        when (upper(transaction_type) like '%REFUND%' or gross_amount < 0)
         and upper(your_reference) like '%CANCELLATION_FEE%'
            then 'REFUND_WITH_CANCELLATION_FEE'
        when upper(your_reference) like '%CANCELLATION_FEE%'
            then 'CANCELLATION_FEE'
        else 'STANDARD_PAYMENT'
    end as receipt_exception_type,
    case
        when channel_type = 'E_COMMERCE' and gateway_merchant_reference is not null
            then 'GATEWAY_MAPPING'
        when coalesce(acquirer_reference_raw, acquirer_reference_from_text) is not null
            then 'ACQUIRER_REFERENCE'
        when direct_reservation_ref_raw is not null
            then 'DIRECT_RESERVATION'
        when invoice_ref is not null
            then 'DIRECT_INVOICE'
        when chargeback_target_ref is not null
            then 'CHARGEBACK_REFERENCE'
        else 'UNRESOLVED'
    end as reference_resolution_method
from mapped;
