create schema if not exists analytics;

create table analytics.payment_batches (
    payment_batch_line_id text primary key,
    payment_batch_id text,
    transaction_date date,
    market_code text,
    channel_type text,
    customer_name text,
    customer_number text,
    item_description text,
    line_total numeric(18, 2)
);

create table analytics.receipts (
    receipt_line_id text primary key,
    receipt_ref text,
    transaction_date date,
    transaction_time time,
    market_code text,
    channel_type text,
    contract_type text,
    card_brand text,
    transaction_status text,
    transaction_type text,
    source_capture_method text,
    your_reference text,
    acquirer_reference text,
    gross_amount numeric(18, 2),
    net_amount numeric(18, 2),
    terminal_id text
);

create table analytics.gateway_reference_mapping (
    gateway_token text,
    merchant_reference text,
    transaction_date date,
    amount numeric(18, 2),
    market_code text,
    source_channel text
);

create table analytics.reconciliation_by_payment_batch (
    payment_batch_id text,
    transaction_date date,
    market_code text,
    channel_type text,
    payment_batch_total numeric(18, 2),
    linked_to text,
    line_count integer,
    linked_amount numeric(18, 2),
    line_statuses text
);

create table analytics.reconciliation_by_receipt (
    receipt_ref text,
    transaction_date date,
    market_code text,
    channel_type text,
    receipt_total numeric(18, 2),
    linked_to text,
    line_count integer,
    linked_amount numeric(18, 2),
    line_statuses text
);

create table analytics.receipt_exception_classification (
    receipt_ref text,
    transaction_date date,
    market_code text,
    channel_type text,
    transaction_status text,
    receipt_exception_type text,
    gross_amount numeric(18, 2),
    net_amount numeric(18, 2),
    your_reference text
);

\copy analytics.payment_batches from '/sample_data/payment_batches_sample.csv' with (format csv, header true);
\copy analytics.receipts from '/sample_data/receipts_sample.csv' with (format csv, header true);
\copy analytics.gateway_reference_mapping from '/sample_data/gateway_reference_mapping_sample.csv' with (format csv, header true);
\copy analytics.reconciliation_by_payment_batch from '/generated/reconciliation_by_payment_batch.csv' with (format csv, header true);
\copy analytics.reconciliation_by_receipt from '/generated/reconciliation_by_receipt.csv' with (format csv, header true);
\copy analytics.receipt_exception_classification from '/generated/receipt_exception_classification.csv' with (format csv, header true);

create or replace view analytics.bi_payment_batch_summary as
select
    payment_batch_id,
    transaction_date,
    market_code,
    channel_type,
    max(payment_batch_total) as payment_batch_total,
    sum(case when linked_to <> 'Review queue' then linked_amount else 0 end) as matched_amount,
    sum(case when linked_to = 'Review queue' then linked_amount else 0 end) as open_amount
from analytics.reconciliation_by_payment_batch
group by payment_batch_id, transaction_date, market_code, channel_type;

create or replace view analytics.bi_reconciliation_daily_kpis as
select
    transaction_date,
    count(distinct payment_batch_id) as payment_batches,
    sum(payment_batch_total) as payment_batch_total,
    sum(matched_amount) as matched_amount,
    sum(open_amount) as open_amount
from analytics.bi_payment_batch_summary
group by transaction_date;

create or replace view analytics.bi_aging_exposure as
select
    case
        when greatest(current_date - transaction_date, 0) <= 7 then '0-7 days'
        when greatest(current_date - transaction_date, 0) <= 30 then '8-30 days'
        when greatest(current_date - transaction_date, 0) <= 60 then '31-60 days'
        else '60+ days'
    end as aging_bucket,
    market_code,
    channel_type,
    count(*) as payment_batches,
    sum(open_amount) as open_amount
from analytics.bi_payment_batch_summary
where open_amount <> 0
group by 1, market_code, channel_type;

create or replace view analytics.bi_exception_backlog as
select
    linked_to,
    market_code,
    channel_type,
    count(*) as rows_in_queue,
    sum(linked_amount) as queue_amount
from analytics.reconciliation_by_payment_batch
where linked_to = 'Review queue'
group by linked_to, market_code, channel_type;

create or replace view analytics.bi_receipt_exception_summary as
select
    transaction_date,
    market_code,
    channel_type,
    receipt_exception_type,
    count(*) as receipt_lines,
    sum(gross_amount) as gross_amount,
    sum(net_amount) as net_amount
from analytics.receipt_exception_classification
group by transaction_date, market_code, channel_type, receipt_exception_type;

create or replace view analytics.bi_channel_health as
select
    channel_type,
    count(distinct payment_batch_id) as payment_batches,
    sum(payment_batch_total) as payment_batch_total,
    sum(matched_amount) as matched_amount,
    sum(open_amount) as open_amount
from analytics.bi_payment_batch_summary
group by channel_type;
