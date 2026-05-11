-- BI-facing views for a management reporting layer such as Metabase.
--
-- These views are expressed against the published reconciliation outputs.
-- In production, the same pattern would be implemented as governed BigQuery
-- views on top of the reconciliation layer.

create or replace view bi_payment_batch_enriched as
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
    greatest(date_diff('day', b.transaction_date, current_date), 0) as days_open,
    case
        when greatest(date_diff('day', b.transaction_date, current_date), 0) <= 7 then '0-7 days'
        when greatest(date_diff('day', b.transaction_date, current_date), 0) <= 30 then '8-30 days'
        when greatest(date_diff('day', b.transaction_date, current_date), 0) <= 60 then '31-60 days'
        else '60+ days'
    end as aging_bucket,
    case
        when r.reconciliation_outcome = 'Allocation Ready' then 'Auto-allocation'
        when r.reconciliation_outcome in ('Cancellation Fee Review', 'Amount Variance Review', 'Evidence Review Required') then 'Operations'
        else 'Finance'
    end as operational_owner
from raw_payment_batches b
left join reconciliation_by_payment_batch r
  on r.payment_batch_id = b.payment_batch_id;

create or replace view bi_reconciliation_daily_kpis as
select
    transaction_date,
    count(*) as payment_batch_lines,
    sum(payment_batch_total) as total_payment_batch_amount,
    sum(allocation_ready_amount) as allocation_ready_amount,
    sum(open_exposure_amount) as open_exposure_amount,
    count(*) filter (where reconciliation_outcome = 'Allocation Ready') as allocation_ready_lines,
    count(*) filter (where reconciliation_outcome <> 'Allocation Ready') as review_lines
from bi_payment_batch_enriched
group by transaction_date;

create or replace view bi_aging_exposure as
select
    aging_bucket,
    reconciliation_outcome,
    operational_owner,
    count(*) as payment_batch_lines,
    sum(open_exposure_amount) as open_exposure_amount
from bi_payment_batch_enriched
where open_exposure_amount <> 0
group by aging_bucket, reconciliation_outcome, operational_owner;

create or replace view bi_exception_backlog as
select
    reconciliation_outcome,
    operational_owner,
    market_code,
    count(*) as payment_batch_lines,
    sum(payment_batch_total) as payment_batch_amount,
    sum(open_exposure_amount) as open_exposure_amount
from bi_payment_batch_enriched
where reconciliation_outcome <> 'Allocation Ready'
group by reconciliation_outcome, operational_owner, market_code;

create or replace view bi_receipt_exception_summary as
select
    transaction_date,
    receipt_transaction_type,
    count(*) as receipt_lines,
    sum(gross_amount) as gross_amount,
    sum(net_amount) as net_amount
from receipt_exception_classification
group by transaction_date, receipt_transaction_type;

create or replace view bi_allocation_readiness as
select
    market_code,
    reconciliation_outcome,
    count(*) as payment_batch_lines,
    sum(payment_batch_total) as payment_batch_amount,
    sum(allocation_ready_amount) as allocation_ready_amount,
    sum(open_exposure_amount) as open_exposure_amount
from bi_payment_batch_enriched
group by market_code, reconciliation_outcome;
