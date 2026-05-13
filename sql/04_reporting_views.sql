-- Operational reporting views consumed by the live Streamlit demo.
--
-- This layer stays intentionally narrow: it exposes clean payment-batch and
-- receipt-side reading for the Streamlit app without surfacing advanced review
-- scenarios that are documented elsewhere in the portfolio.

create or replace view reconciliation_by_payment_batch as
select
    payment_batch_id,
    market_code,
    channel_type,
    min(transaction_date) as transaction_date,
    count(*) as line_count,
    sum(line_total) as payment_batch_total,
    count(*) filter (where match_status = 'MATCH') as matched_line_count,
    count(*) filter (where match_status = 'REJECTED') as rejected_line_count,
    count(*) filter (where match_status = 'CHECK') as check_line_count,
    count(*) filter (where match_status = 'MISSING_REFERENCE') as missing_reference_line_count,
    count(distinct receipt_ref) filter (where receipt_ref is not null) as linked_receipt_count,
    string_agg(distinct receipt_ref, ', ' order by receipt_ref) filter (where receipt_ref is not null) as linked_receipts,
    coalesce(sum(line_total) filter (where receipt_ref is not null), 0) as linked_receipt_total,
    coalesce(sum(line_total) filter (where receipt_ref is null), 0) as open_line_total,
    case
        when count(*) filter (where match_status in ('CHECK', 'MISSING_REFERENCE')) > 0 then 'CHECK'
        when count(*) filter (where match_status = 'REJECTED') > 0 then 'REJECTED'
        else 'MATCHED_TO_RECEIPTS'
    end as reconciliation_outcome
from reconciled_payment_batch_lines
group by payment_batch_id, market_code, channel_type;

create or replace view payment_batch_receipt_summary as
select
    payment_batch_id,
    market_code,
    channel_type,
    min(transaction_date) as transaction_date,
    max(payment_batch_total) as payment_batch_total,
    reconciliation_target,
    count(*) as line_count,
    sum(line_total) as linked_amount,
    string_agg(distinct match_status, ', ' order by match_status) as line_statuses
from reconciled_payment_batch_lines
group by payment_batch_id, market_code, channel_type, reconciliation_target;

create or replace view reconciled_receipt_lines as
select
    r.receipt_line_id,
    r.receipt_ref,
    r.transaction_date,
    r.transaction_time,
    r.market_code,
    r.channel_type,
    r.contract_type,
    r.card_brand,
    r.transaction_status,
    r.transaction_type,
    r.source_capture_method,
    r.your_reference,
    r.acquirer_reference,
    r.gross_amount,
    r.net_amount,
    r.terminal_id,
    r.reservation_ref,
    r.invoice_ref,
    r.receipt_exception_type,
    r.reference_resolution_method,
    coalesce(count(distinct p.payment_batch_line_id), 0) as linked_payment_batch_line_count,
    coalesce(sum(p.line_total), 0) as linked_payment_batch_total,
    string_agg(distinct p.match_status, ', ' order by p.match_status) as linked_statuses,
    string_agg(distinct p.payment_batch_id, ', ' order by p.payment_batch_id) as linked_payment_batches
from receipt_keys r
left join reconciled_payment_batch_lines p
  on p.receipt_line_id = r.receipt_line_id
group by
    r.receipt_line_id,
    r.receipt_ref,
    r.transaction_date,
    r.transaction_time,
    r.market_code,
    r.channel_type,
    r.contract_type,
    r.card_brand,
    r.transaction_status,
    r.transaction_type,
    r.source_capture_method,
    r.your_reference,
    r.acquirer_reference,
    r.gross_amount,
    r.net_amount,
    r.terminal_id,
    r.reservation_ref,
    r.invoice_ref,
    r.receipt_exception_type,
    r.reference_resolution_method;

create or replace view receipt_payment_batch_targets as
select
    r.receipt_line_id,
    r.receipt_ref,
    r.transaction_date,
    r.market_code,
    r.channel_type,
    p.payment_batch_id,
    count(*) as linked_payment_batch_line_count,
    sum(p.line_total) as linked_amount,
    string_agg(distinct p.match_status, ', ' order by p.match_status) as linked_statuses
from reconciled_payment_batch_lines p
join receipt_keys r
  on r.receipt_line_id = p.receipt_line_id
group by
    r.receipt_line_id,
    r.receipt_ref,
    r.transaction_date,
    r.market_code,
    r.channel_type,
    p.payment_batch_id;

create or replace view reconciliation_by_receipt as
with receipt_target_rollup as (
    select
        receipt_ref,
        market_code,
        channel_type,
        sum(linked_amount) as linked_payment_batch_total,
        count(distinct receipt_line_id) as reconciled_receipt_line_count,
        count(distinct payment_batch_id) as linked_batch_group_count,
        string_agg(distinct payment_batch_id, ', ' order by payment_batch_id) as linked_payment_batches
    from receipt_payment_batch_targets
    group by receipt_ref, market_code, channel_type
)
select
    r.receipt_ref,
    r.market_code,
    r.channel_type,
    min(r.transaction_date) as transaction_date,
    count(*) as receipt_line_count,
    sum(r.gross_amount) as receipt_total,
    coalesce(t.linked_payment_batch_total, 0) as linked_payment_batch_total,
    coalesce(t.reconciled_receipt_line_count, 0) as reconciled_receipt_line_count,
    count(*) - coalesce(t.reconciled_receipt_line_count, 0) as unreconciled_receipt_line_count,
    count(*) filter (where r.receipt_exception_type = 'CHARGEBACK') as chargeback_line_count,
    count(*) filter (where r.transaction_status = 'Rejected') as rejected_line_count,
    coalesce(t.linked_batch_group_count, 0) as linked_batch_group_count,
    t.linked_payment_batches,
    case
        when count(*) filter (where r.receipt_exception_type = 'CHARGEBACK') > 0 then 'CHARGEBACK'
        when count(*) filter (where r.transaction_status = 'Rejected') > 0 then 'REJECTED_RECEIPT'
        when count(*) > coalesce(t.reconciled_receipt_line_count, 0) then 'UNLINKED_RECEIPT'
        else 'LINKED_TO_PAYMENT_BATCHES'
    end as reconciliation_outcome
from reconciled_receipt_lines r
left join receipt_target_rollup t
  on t.receipt_ref = r.receipt_ref
 and t.market_code = r.market_code
 and t.channel_type = r.channel_type
group by
    r.receipt_ref,
    r.market_code,
    r.channel_type,
    t.linked_payment_batch_total,
    t.reconciled_receipt_line_count,
    t.linked_batch_group_count,
    t.linked_payment_batches;

create or replace view receipt_payment_batch_summary as
with matched_targets as (
    select
        receipt_ref,
        market_code,
        channel_type,
        min(transaction_date) as transaction_date,
        payment_batch_id as distribution_target,
        count(distinct receipt_line_id) as line_count,
        sum(linked_amount) as linked_amount,
        string_agg(distinct linked_statuses, ', ' order by linked_statuses) as line_statuses
    from receipt_payment_batch_targets
    group by receipt_ref, market_code, channel_type, payment_batch_id
),
exception_targets as (
    select
        receipt_ref,
        market_code,
        channel_type,
        min(transaction_date) as transaction_date,
        case
            when receipt_exception_type = 'CHARGEBACK' then 'CHARGEBACK'
            when transaction_status = 'Rejected' then 'REJECTED'
            else 'UNLINKED'
        end as distribution_target,
        count(*) as line_count,
        sum(gross_amount) as linked_amount,
        string_agg(
            distinct case
                when receipt_exception_type = 'CHARGEBACK' then 'CHARGEBACK'
                when transaction_status = 'Rejected' then 'REJECTED'
                else 'UNLINKED'
            end,
            ', ' order by case
                when receipt_exception_type = 'CHARGEBACK' then 'CHARGEBACK'
                when transaction_status = 'Rejected' then 'REJECTED'
                else 'UNLINKED'
            end
        ) as line_statuses
    from reconciled_receipt_lines
    where linked_payment_batch_line_count = 0
    group by
        receipt_ref,
        market_code,
        channel_type,
        case
            when receipt_exception_type = 'CHARGEBACK' then 'CHARGEBACK'
            when transaction_status = 'Rejected' then 'REJECTED'
            else 'UNLINKED'
        end
),
receipt_distribution as (
    select * from matched_targets
    union all
    select * from exception_targets
)
select
    receipt_ref,
    market_code,
    channel_type,
    transaction_date,
    distribution_target as payment_batch_id,
    line_count,
    linked_amount,
    line_statuses
from receipt_distribution
order by receipt_ref, market_code, channel_type, distribution_target;

create or replace view receipt_exception_classification as
select
    receipt_line_id,
    receipt_ref,
    transaction_date,
    market_code,
    channel_type,
    transaction_status,
    receipt_exception_type,
    source_capture_method,
    gross_amount,
    net_amount,
    your_reference,
    reservation_ref,
    invoice_ref
from receipt_keys
where receipt_exception_type in ('CHARGEBACK', 'REJECTED_CARD_TRANSACTION')
   or transaction_status = 'Rejected';

create or replace view reconciliation_runtime_summary as
select 'payment_batch_lines' as object_name, count(*) as row_count from payment_batch_keys
union all
select 'receipt_lines', count(*) from receipt_keys
union all
select 'reconciled_payment_batch_lines', count(*) from reconciled_payment_batch_lines
union all
select 'reconciliation_by_payment_batch', count(*) from reconciliation_by_payment_batch
union all
select 'reconciliation_by_receipt', count(*) from reconciliation_by_receipt
union all
select 'receipt_exception_classification', count(*) from receipt_exception_classification;
