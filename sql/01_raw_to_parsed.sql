-- Normalize raw payment-batch and receipt inputs into parsed datasets.
--
-- This public version keeps the original reconciliation concepts while using
-- generic names and sanitized sample data:
-- - INV / RES / RA reference extraction
-- - e-commerce gateway-token mapping
-- - receipt exception classification

create or replace view parsed_payment_batches as
select
    payment_batch_id,
    transaction_date,
    market_code,
    customer,
    amount,
    item_description,
    coalesce(
        nullif(regexp_extract(item_description, 'RES[: ]*([0-9]{10})', 1), ''),
        nullif(regexp_extract(item_description, '^([0-9]{10}):', 1), '')
    ) as reservation_ref,
    coalesce(
        nullif(regexp_extract(item_description, 'INV[: ]*([0-9]{12})', 1), ''),
        nullif(regexp_extract(item_description, '^[0-9]{10}:([0-9]{12}):', 1), '')
    ) as invoice_ref,
    case
        when upper(customer) like '%MAESTRO%' then coalesce(
            nullif(regexp_extract(item_description, 'RA[: ]*([0-9]+)', 1), ''),
            nullif(regexp_extract(split_part(item_description, ':', 1), '([0-9]+)', 1), '')
        )
        else nullif(regexp_extract(item_description, 'RA[: ]*([0-9]+)', 1), '')
    end as acquirer_ref,
    case
        when upper(customer) like '%MAESTRO%' then true
        else false
    end as is_maestro
from raw_payment_batches;

create or replace view parsed_receipts as
select
    r.receipt_ref,
    r.transaction_date,
    r.market_code,
    r.brand,
    r.contract_type,
    r.status,
    r.type_of_transaction,
    r.your_reference,
    r.gross_amount,
    r.net_amount,
    nullif(regexp_extract(r.your_reference, 'RES[: ]*([0-9]{10})', 1), '') as direct_reservation_ref,
    nullif(regexp_extract(r.your_reference, 'INV[: ]*([0-9]{12})', 1), '') as invoice_ref,
    nullif(regexp_extract(r.your_reference, 'RA[: ]*([0-9]+)', 1), '') as acquirer_ref,
    nullif(cast(g.merchant_reference as varchar), '') as gateway_reservation_ref,
    case
        when upper(r.contract_type) = 'ONLINE CARD PAYMENT'
            then nullif(cast(g.merchant_reference as varchar), '')
        else nullif(regexp_extract(r.your_reference, 'RES[: ]*([0-9]{10})', 1), '')
    end as reservation_ref,
    case
        when g.gateway_token is not null then 'GATEWAY_TOKEN'
        when coalesce(
            nullif(regexp_extract(r.your_reference, 'RES[: ]*([0-9]{10})', 1), ''),
            nullif(regexp_extract(r.your_reference, 'INV[: ]*([0-9]{12})', 1), ''),
            nullif(regexp_extract(r.your_reference, 'RA[: ]*([0-9]+)', 1), '')
        ) is not null then 'DIRECT_REFERENCE'
        else 'UNRESOLVED_REFERENCE'
    end as reference_resolution_method,
    case
        when upper(r.type_of_transaction) like '%CHARGEBACK%'
          or upper(r.your_reference) like '%CHARGEBACK%'
          or upper(r.your_reference) like 'CHB:%'
            then 'CHARGEBACK'
        when (
            upper(r.type_of_transaction) like '%REFUND%'
            or upper(r.your_reference) like '%REFUND%'
            or upper(r.your_reference) like 'RFND:%'
        )
        and (
            upper(r.type_of_transaction) like '%CANCELLATION FEE%'
            or upper(r.your_reference) like '%CANCELLATION_FEE%'
            or upper(r.your_reference) like '%CANCELLATION_FEE%'
        )
            then 'REFUND_WITH_CANCELLATION_FEE'
        when upper(r.your_reference) like '%CANCELLATION_FEE%'
          or upper(r.your_reference) like '%CANCELLATION_FEE%'
            then 'CANCELLATION_FEE'
        else 'STANDARD_PAYMENT'
    end as receipt_transaction_type
from raw_receipts r
left join raw_gateway_reference_mapping g
  on r.your_reference like '%' || g.gateway_token || '%'
 and r.market_code = g.market_code;
