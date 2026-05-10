-- Sanitized payment-batch reconciliation logic.
--
-- This layer mirrors the complete operational pattern without exposing
-- private system names:
-- 1. exact matching by INV, RA, RES, and gateway token
-- 2. rejected receipt override
-- 3. cancellation-fee pairing for refund + fee lines
-- 4. over/under-payment detection
-- 5. evidence-review and missing-evidence open-balance classification

create or replace view market_rules as
select * from (
    values
        ('MKT_A', 45.00::decimal(18, 2)),
        ('MKT_B', 50.00::decimal(18, 2)),
        ('MKT_C', 50.00::decimal(18, 2)),
        ('MKT_D', 50.00::decimal(18, 2))
) as t(market_code, cancellation_fee);

create or replace view exact_match_candidates as
select
    s.payment_batch_id,
    r.receipt_ref,
    s.primary_ref,
    s.amount as payment_batch_amount,
    r.gross_amount as receipt_amount,
    r.reference_resolution_method,
    r.receipt_transaction_type,
    s.transaction_date as payment_batch_date,
    r.transaction_date as receipt_date,
    r.status as receipt_status,
    'INV' as match_rule,
    1 as match_priority,
    null::decimal(18, 2) as variance_amount
from payment_batch_keys s
join receipt_keys r
  on r.market_code = s.market_code
 and upper(r.contract_type) <> 'ONLINE CARD PAYMENT'
 and s.key_inv = r.key_inv
 and s.occurrence_inv = r.occurrence_inv
 and s.transaction_date = r.transaction_date
 and sign(s.amount) = sign(r.gross_amount)

union all

select
    s.payment_batch_id,
    r.receipt_ref,
    s.primary_ref,
    s.amount as payment_batch_amount,
    r.gross_amount as receipt_amount,
    r.reference_resolution_method,
    r.receipt_transaction_type,
    s.transaction_date as payment_batch_date,
    r.transaction_date as receipt_date,
    r.status as receipt_status,
    'RA' as match_rule,
    2 as match_priority,
    null::decimal(18, 2) as variance_amount
from payment_batch_keys s
join receipt_keys r
  on r.market_code = s.market_code
 and upper(r.contract_type) <> 'ONLINE CARD PAYMENT'
 and s.is_maestro = true
 and s.key_ra = r.key_ra
 and s.occurrence_ra = r.occurrence_ra
 and s.transaction_date = r.transaction_date
 and sign(s.amount) = sign(r.gross_amount)

union all

select
    s.payment_batch_id,
    r.receipt_ref,
    s.primary_ref,
    s.amount as payment_batch_amount,
    r.gross_amount as receipt_amount,
    r.reference_resolution_method,
    r.receipt_transaction_type,
    s.transaction_date as payment_batch_date,
    r.transaction_date as receipt_date,
    r.status as receipt_status,
    'RES' as match_rule,
    3 as match_priority,
    null::decimal(18, 2) as variance_amount
from payment_batch_keys s
join receipt_keys r
  on r.market_code = s.market_code
 and upper(r.contract_type) <> 'ONLINE CARD PAYMENT'
 and s.key_res = r.key_res
 and s.occurrence_res = r.occurrence_res
 and s.transaction_date = r.transaction_date
 and sign(s.amount) = sign(r.gross_amount)

union all

select
    s.payment_batch_id,
    r.receipt_ref,
    s.primary_ref,
    s.amount as payment_batch_amount,
    r.gross_amount as receipt_amount,
    r.reference_resolution_method,
    r.receipt_transaction_type,
    s.transaction_date as payment_batch_date,
    r.transaction_date as receipt_date,
    r.status as receipt_status,
    'GATEWAY_TOKEN' as match_rule,
    4 as match_priority,
    null::decimal(18, 2) as variance_amount
from payment_batch_keys s
join receipt_keys r
  on r.market_code = s.market_code
 and upper(r.contract_type) = 'ONLINE CARD PAYMENT'
 and s.reservation_ref = r.reservation_ref
 and s.amount = r.gross_amount
 and s.occurrence_ref_amount = r.occurrence_cyb
 and abs(date_diff('day', s.transaction_date, r.transaction_date)) <= 180
 and sign(s.amount) = sign(r.gross_amount);

create or replace view exact_matches as
select *
from exact_match_candidates
qualify row_number() over (
    partition by payment_batch_id
    order by match_priority, receipt_date, receipt_ref
) = 1;

create or replace view cancellation_fee_pairs as
with refunds as (
    select
        s.payment_batch_id as refund_batch_id,
        s.market_code,
        s.reservation_ref,
        s.amount as refund_amount,
        s.transaction_date
    from payment_batch_keys s
    where s.amount < 0
      and s.reservation_ref is not null
),
fees as (
    select
        s.payment_batch_id as fee_batch_id,
        s.market_code,
        s.reservation_ref,
        s.amount as fee_amount
    from payment_batch_keys s
    join market_rules m
      on m.market_code = s.market_code
     and s.amount = m.cancellation_fee
),
pairs as (
    select
        r.refund_batch_id,
        f.fee_batch_id,
        r.market_code,
        r.reservation_ref,
        r.refund_amount,
        f.fee_amount,
        r.refund_amount + f.fee_amount as expected_receipt_amount
    from refunds r
    join fees f
      on f.market_code = r.market_code
     and f.reservation_ref = r.reservation_ref
)
select
    p.refund_batch_id,
    p.fee_batch_id,
    p.market_code,
    p.reservation_ref,
    p.refund_amount,
    p.fee_amount,
    p.expected_receipt_amount,
    r.receipt_ref,
    r.transaction_date as receipt_date,
    r.status as receipt_status,
    r.reference_resolution_method,
    r.receipt_transaction_type
from pairs p
join receipt_keys r
  on r.market_code = p.market_code
 and upper(r.contract_type) = 'ONLINE CARD PAYMENT'
 and r.reservation_ref = p.reservation_ref
 and r.gross_amount = p.expected_receipt_amount
 and r.status <> 'Rejected';

create or replace view cancellation_fee_matches as
select
    refund_batch_id as payment_batch_id,
    receipt_ref,
    reservation_ref as primary_ref,
    refund_amount as payment_batch_amount,
    expected_receipt_amount as receipt_amount,
    reference_resolution_method,
    receipt_transaction_type,
    null::date as payment_batch_date,
    receipt_date,
    receipt_status,
    'CANCELLATION_FEE_PAIR' as match_rule,
    5 as match_priority,
    null::decimal(18, 2) as variance_amount
from cancellation_fee_pairs

union all

select
    fee_batch_id as payment_batch_id,
    receipt_ref,
    reservation_ref as primary_ref,
    fee_amount as payment_batch_amount,
    expected_receipt_amount as receipt_amount,
    reference_resolution_method,
    receipt_transaction_type,
    null::date as payment_batch_date,
    receipt_date,
    receipt_status,
    'CANCELLATION_FEE_PAIR' as match_rule,
    5 as match_priority,
    null::decimal(18, 2) as variance_amount
from cancellation_fee_pairs;

create or replace view ovp_matches as
select
    s.payment_batch_id,
    r.receipt_ref,
    s.primary_ref,
    s.amount as payment_batch_amount,
    r.gross_amount as receipt_amount,
    r.reference_resolution_method,
    r.receipt_transaction_type,
    s.transaction_date as payment_batch_date,
    r.transaction_date as receipt_date,
    r.status as receipt_status,
    'OVER_UNDER_PAYMENT' as match_rule,
    6 as match_priority,
    round(r.gross_amount - s.amount, 2) as variance_amount
from payment_batch_keys s
join receipt_keys r
  on r.market_code = s.market_code
 and upper(r.contract_type) = 'ONLINE CARD PAYMENT'
 and r.status <> 'Rejected'
 and s.reservation_ref = r.reservation_ref
 and sign(s.amount) = sign(r.gross_amount)
 and s.amount <> r.gross_amount
 and abs(date_diff('day', s.transaction_date, r.transaction_date)) <= 180
left join exact_matches em
  on em.payment_batch_id = s.payment_batch_id
left join cancellation_fee_matches cf
  on cf.payment_batch_id = s.payment_batch_id
left join market_rules m
  on m.market_code = s.market_code
where em.payment_batch_id is null
  and cf.payment_batch_id is null
  and round(abs(r.gross_amount - s.amount), 2) <> m.cancellation_fee
qualify row_number() over (
    partition by s.payment_batch_id
    order by round(abs(r.gross_amount - s.amount), 2), r.transaction_date, r.receipt_ref
) = 1;

create or replace view all_reconciliation_matches as
select * from exact_matches
union all
select * from cancellation_fee_matches
union all
select * from ovp_matches;

create or replace view reconciled_rows as
select
    s.payment_batch_id,
    m.receipt_ref,
    s.primary_ref,
    s.amount as payment_batch_amount,
    m.receipt_amount,
    m.reference_resolution_method,
    m.receipt_transaction_type,
    s.transaction_date as payment_batch_date,
    m.receipt_date,
    m.match_rule,
    m.variance_amount,
    case
        when m.receipt_ref is not null and m.receipt_status = 'Rejected'
            then 'Rejected Card Transaction'
        when m.match_rule = 'CANCELLATION_FEE_PAIR'
            then 'Cancellation Fee Review'
        when m.match_rule = 'OVER_UNDER_PAYMENT'
            then 'Amount Variance Review'
        when m.receipt_ref is not null
            then 'Allocation Ready'
        when s.primary_ref is not null
            then 'Evidence Review Required'
        else 'Missing Receipt Evidence'
    end as reconciliation_outcome
from payment_batch_keys s
left join all_reconciliation_matches m
  on m.payment_batch_id = s.payment_batch_id
qualify row_number() over (
    partition by s.payment_batch_id
    order by coalesce(m.match_priority, 99), m.receipt_date, m.receipt_ref
) = 1;
