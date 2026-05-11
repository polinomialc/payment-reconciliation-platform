create schema if not exists analytics;

create table analytics.payment_batches (
    payment_batch_id text primary key,
    transaction_date date,
    market_code text,
    customer text,
    item_description text,
    amount numeric(18, 2)
);

create table analytics.receipts (
    receipt_ref text,
    transaction_date date,
    market_code text,
    brand text,
    contract_type text,
    status text,
    type_of_transaction text,
    your_reference text,
    gross_amount numeric(18, 2),
    net_amount numeric(18, 2)
);

create table analytics.gateway_reference_mapping (
    gateway_token text,
    merchant_reference text,
    transaction_date date,
    amount numeric(18, 2),
    market_code text
);

create table analytics.reconciliation_by_payment_batch (
    payment_batch_id text,
    receipt_ref text,
    reconciliation_outcome text,
    row_count integer,
    payment_batch_total numeric(18, 2)
);

create table analytics.reconciliation_by_receipt (
    receipt_ref text,
    reconciliation_outcome text,
    row_count integer,
    receipt_total numeric(18, 2)
);

create table analytics.receipt_exception_classification (
    receipt_ref text,
    receipt_transaction_type text,
    transaction_date date,
    gross_amount numeric(18, 2),
    net_amount numeric(18, 2),
    your_reference text
);

\copy analytics.payment_batches from '/sample_data/payment_batches_sample.csv' with (format csv, header true);
\copy analytics.receipts from '/sample_data/receipts_sample.csv' with (format csv, header true);
\copy analytics.gateway_reference_mapping from '/sample_data/gateway_reference_mapping_sample.csv' with (format csv, header true);
\copy analytics.reconciliation_by_payment_batch from '/output_examples/reconciliation_by_payment_batch.csv' with (format csv, header true);
\copy analytics.reconciliation_by_receipt from '/output_examples/reconciliation_by_receipt.csv' with (format csv, header true);
\copy analytics.receipt_exception_classification from '/output_examples/receipt_exception_classification.csv' with (format csv, header true);

create or replace view analytics.bi_payment_batch_enriched as
select
    b.payment_batch_id,
    b.transaction_date,
    b.market_code,
    b.customer,
    b.item_description,
    b.amount,
    coalesce(r.receipt_ref, '') as receipt_ref,
    r.reconciliation_outcome,
    r.row_count,
    r.payment_batch_total,
    case
        when r.reconciliation_outcome = 'Allocation Ready' then r.payment_batch_total
        else 0
    end as allocation_ready_amount,
    case
        when r.reconciliation_outcome in ('Allocation Ready', 'Cancellation Fee Review') then 0
        else r.payment_batch_total
    end as open_exposure_amount,
    greatest(current_date - b.transaction_date, 0) as days_open,
    case
        when greatest(current_date - b.transaction_date, 0) <= 7 then '0-7 days'
        when greatest(current_date - b.transaction_date, 0) <= 30 then '8-30 days'
        when greatest(current_date - b.transaction_date, 0) <= 60 then '31-60 days'
        else '60+ days'
    end as aging_bucket,
    case
        when r.reconciliation_outcome = 'Allocation Ready' then 'Auto-allocation'
        when r.reconciliation_outcome in ('Cancellation Fee Review', 'Amount Variance Review', 'Evidence Review Required') then 'Operations'
        else 'Finance'
    end as operational_owner
from analytics.payment_batches b
left join analytics.reconciliation_by_payment_batch r
  on r.payment_batch_id = b.payment_batch_id;

create or replace view analytics.bi_reconciliation_daily_kpis as
select
    transaction_date,
    count(*) as payment_batch_lines,
    sum(payment_batch_total) as total_payment_batch_amount,
    sum(allocation_ready_amount) as allocation_ready_amount,
    sum(open_exposure_amount) as open_exposure_amount,
    count(*) filter (where reconciliation_outcome = 'Allocation Ready') as allocation_ready_lines,
    count(*) filter (where reconciliation_outcome <> 'Allocation Ready') as review_lines
from analytics.bi_payment_batch_enriched
group by transaction_date;

create or replace view analytics.bi_aging_exposure as
select
    aging_bucket,
    reconciliation_outcome,
    operational_owner,
    count(*) as payment_batch_lines,
    sum(open_exposure_amount) as open_exposure_amount
from analytics.bi_payment_batch_enriched
where open_exposure_amount <> 0
group by aging_bucket, reconciliation_outcome, operational_owner;

create or replace view analytics.bi_exception_backlog as
select
    reconciliation_outcome,
    operational_owner,
    market_code,
    count(*) as payment_batch_lines,
    sum(payment_batch_total) as payment_batch_amount,
    sum(open_exposure_amount) as open_exposure_amount
from analytics.bi_payment_batch_enriched
where reconciliation_outcome <> 'Allocation Ready'
group by reconciliation_outcome, operational_owner, market_code;

create or replace view analytics.bi_receipt_exception_summary as
select
    transaction_date,
    receipt_transaction_type,
    count(*) as receipt_lines,
    sum(gross_amount) as gross_amount,
    sum(net_amount) as net_amount
from analytics.receipt_exception_classification
group by transaction_date, receipt_transaction_type;

create or replace view analytics.bi_allocation_readiness as
select
    market_code,
    reconciliation_outcome,
    count(*) as payment_batch_lines,
    sum(payment_batch_total) as payment_batch_amount,
    sum(allocation_ready_amount) as allocation_ready_amount,
    sum(open_exposure_amount) as open_exposure_amount
from analytics.bi_payment_batch_enriched
group by market_code, reconciliation_outcome;
