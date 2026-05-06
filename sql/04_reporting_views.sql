-- Example: reporting outputs.

create or replace view reconciliation_by_schedule as
select
    schedule_id,
    match_status,
    count(*) as row_count,
    sum(schedule_amount) as schedule_total
from reconciled_rows
group by 1, 2;

create or replace view reconciliation_by_receipt as
select
    receipt_ref,
    match_status,
    count(*) as row_count,
    sum(receipt_amount) as receipt_total
from reconciled_rows
group by 1, 2;

