-- Example: simplified reconciliation logic.

create or replace view reconciled_rows as
select
    s.payment_batch_id,
    r.receipt_ref,
    s.primary_ref,
    s.amount as payment_batch_amount,
    r.gross_amount as receipt_amount,
    s.transaction_date as payment_batch_date,
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
from payment_batch_keys s
left join receipt_keys r
  on s.primary_ref = r.primary_ref
 and s.amount = r.gross_amount;
