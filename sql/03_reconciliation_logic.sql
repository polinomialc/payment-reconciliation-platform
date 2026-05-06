-- Example: simplified reconciliation logic.

create or replace view reconciled_rows as
select
    s.schedule_id,
    r.receipt_ref,
    s.primary_ref,
    s.amount as schedule_amount,
    r.gross_amount as receipt_amount,
    s.transaction_date as schedule_date,
    r.transaction_date as receipt_date,
    case
        when s.primary_ref = r.primary_ref
         and s.amount = r.gross_amount
         and s.transaction_date = r.transaction_date
            then 'MATCH'
        when s.primary_ref = r.primary_ref
         and s.amount = r.gross_amount
            then 'CHECK'
        else 'UNMATCHED'
    end as match_status
from schedule_keys s
left join receipt_keys r
  on s.primary_ref = r.primary_ref
 and s.amount = r.gross_amount;

