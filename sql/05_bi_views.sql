-- BI-facing views.
--
-- These stay aligned with the compact runtime demo: core matching, open
-- payment-batch items, and receipt-side exceptions.

create or replace view bi_payment_batch_enriched as
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
    primary_reference,
    receipt_ref,
    match_rule,
    match_status,
    workflow_queue,
    greatest(date_diff('day', transaction_date, current_date), 0) as days_open,
    case
        when greatest(date_diff('day', transaction_date, current_date), 0) <= 7 then '0-7 days'
        when greatest(date_diff('day', transaction_date, current_date), 0) <= 30 then '8-30 days'
        when greatest(date_diff('day', transaction_date, current_date), 0) <= 60 then '31-60 days'
        else '60+ days'
    end as aging_bucket,
    case
        when match_status = 'MATCH' then line_total
        else 0
    end as auto_reconciled_amount,
    case
        when match_status in ('CHECK', 'REJECTED', 'MISSING_REFERENCE') then line_total
        else 0
    end as review_amount
from reconciled_payment_batch_lines;

create or replace view bi_reconciliation_daily_kpis as
select
    transaction_date,
    count(*) as payment_batch_line_count,
    sum(line_total) as payment_batch_total,
    sum(auto_reconciled_amount) as auto_reconciled_amount,
    sum(review_amount) as review_amount,
    count(*) filter (where match_status = 'MATCH') as match_line_count,
    count(*) filter (where match_status = 'CHECK') as check_line_count,
    count(*) filter (where match_status = 'REJECTED') as rejected_line_count
from bi_payment_batch_enriched
group by transaction_date;

create or replace view bi_exception_backlog as
select
    match_status,
    workflow_queue,
    market_code,
    channel_type,
    count(*) as payment_batch_line_count,
    sum(line_total) as payment_batch_amount,
    sum(review_amount) as review_amount
from bi_payment_batch_enriched
where match_status <> 'MATCH'
group by match_status, workflow_queue, market_code, channel_type;

create or replace view bi_channel_health as
select
    channel_type,
    count(*) as payment_batch_line_count,
    sum(line_total) as payment_batch_amount,
    count(*) filter (where match_status = 'MATCH') as matched_line_count,
    count(*) filter (where match_status = 'CHECK') as check_line_count,
    count(*) filter (where match_status = 'REJECTED') as rejected_line_count,
    round(
        100.0 * count(*) filter (where match_status = 'MATCH') / nullif(count(*), 0),
        2
    ) as match_rate_pct
from bi_payment_batch_enriched
group by channel_type;

create or replace view bi_receipt_exception_summary as
select
    transaction_date,
    market_code,
    channel_type,
    receipt_exception_type,
    count(*) as receipt_line_count,
    sum(gross_amount) as gross_amount,
    sum(net_amount) as net_amount
from receipt_exception_classification
group by transaction_date, market_code, channel_type, receipt_exception_type;

create or replace view bi_aging_exposure as
select
    aging_bucket,
    match_status,
    workflow_queue,
    count(*) as payment_batch_line_count,
    sum(review_amount) as review_amount
from bi_payment_batch_enriched
where match_status <> 'MATCH'
group by aging_bucket, match_status, workflow_queue;
