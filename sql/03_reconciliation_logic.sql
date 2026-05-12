-- Reconciliation engine.
--
-- This public version keeps the same operating objects as the internal tool:
-- payment-batch lines, receipt lines, channel-aware matching, explicit
-- exception queues, and channel-aware invoice / reservation logic.

create or replace view exact_match_candidates as
select
    s.payment_batch_line_id,
    s.payment_batch_id,
    s.transaction_date as payment_batch_date,
    s.market_code,
    s.channel_type as payment_batch_channel,
    s.primary_reference,
    s.line_total,
    r.receipt_line_id,
    r.receipt_ref,
    r.transaction_date as receipt_date,
    r.channel_type as receipt_channel,
    r.transaction_status,
    r.receipt_exception_type,
    r.reference_resolution_method,
    r.gross_amount as receipt_amount,
    'INVOICE' as match_rule,
    1 as match_priority,
    cast(null as decimal(18, 2)) as variance_amount
from payment_batch_keys s
join receipt_keys r
  on s.market_code = r.market_code
 and s.invoice_ref is not null
 and s.invoice_ref = r.invoice_ref
 and s.line_total = r.gross_amount
 and sign(s.line_total) = sign(r.gross_amount)
join channel_rules c
  on c.channel_type = s.channel_type
where abs(date_diff('day', s.transaction_date, r.transaction_date)) <= c.date_window_days

union all

select
    s.payment_batch_line_id,
    s.payment_batch_id,
    s.transaction_date as payment_batch_date,
    s.market_code,
    s.channel_type as payment_batch_channel,
    s.primary_reference,
    s.line_total,
    r.receipt_line_id,
    r.receipt_ref,
    r.transaction_date as receipt_date,
    r.channel_type as receipt_channel,
    r.transaction_status,
    r.receipt_exception_type,
    r.reference_resolution_method,
    r.gross_amount as receipt_amount,
    'RESERVATION' as match_rule,
    2 as match_priority,
    cast(null as decimal(18, 2)) as variance_amount
from payment_batch_keys s
join receipt_keys r
  on s.market_code = r.market_code
 and s.reservation_ref is not null
 and s.reservation_ref = r.reservation_ref
 and s.line_total = r.gross_amount
 and sign(s.line_total) = sign(r.gross_amount)
 and s.channel_type <> 'E_COMMERCE'
 and r.channel_type <> 'E_COMMERCE'
join channel_rules c
  on c.channel_type = s.channel_type
where abs(date_diff('day', s.transaction_date, r.transaction_date)) <= c.date_window_days

union all

select
    s.payment_batch_line_id,
    s.payment_batch_id,
    s.transaction_date as payment_batch_date,
    s.market_code,
    s.channel_type as payment_batch_channel,
    s.primary_reference,
    s.line_total,
    r.receipt_line_id,
    r.receipt_ref,
    r.transaction_date as receipt_date,
    r.channel_type as receipt_channel,
    r.transaction_status,
    r.receipt_exception_type,
    r.reference_resolution_method,
    r.gross_amount as receipt_amount,
    'ACQUIRER_REFERENCE' as match_rule,
    3 as match_priority,
    cast(null as decimal(18, 2)) as variance_amount
from payment_batch_keys s
join receipt_keys r
  on s.market_code = r.market_code
 and s.acquirer_reference is not null
 and s.acquirer_reference = r.acquirer_reference
 and s.line_total = r.gross_amount
 and sign(s.line_total) = sign(r.gross_amount)
join channel_rules c
  on c.channel_type = s.channel_type
where abs(date_diff('day', s.transaction_date, r.transaction_date)) <= c.date_window_days

union all

select
    s.payment_batch_line_id,
    s.payment_batch_id,
    s.transaction_date as payment_batch_date,
    s.market_code,
    s.channel_type as payment_batch_channel,
    s.primary_reference,
    s.line_total,
    r.receipt_line_id,
    r.receipt_ref,
    r.transaction_date as receipt_date,
    r.channel_type as receipt_channel,
    r.transaction_status,
    r.receipt_exception_type,
    r.reference_resolution_method,
    r.gross_amount as receipt_amount,
    'GATEWAY_TOKEN_RESOLUTION' as match_rule,
    4 as match_priority,
    cast(null as decimal(18, 2)) as variance_amount
from payment_batch_keys s
join receipt_keys r
  on s.market_code = r.market_code
 and s.channel_type = 'E_COMMERCE'
 and r.channel_type = 'E_COMMERCE'
 and s.reservation_ref is not null
 and s.reservation_ref = r.reservation_ref
 and s.line_total = r.gross_amount
 and sign(s.line_total) = sign(r.gross_amount)
join channel_rules c
  on c.channel_type = s.channel_type
where abs(date_diff('day', s.transaction_date, r.transaction_date)) <= c.date_window_days

;

create or replace view exact_matches_ranked as
select
    *,
    row_number() over (
        partition by payment_batch_line_id
        order by match_priority, abs(date_diff('day', payment_batch_date, receipt_date)), receipt_line_id
    ) as payment_batch_rank,
    row_number() over (
        partition by receipt_line_id
        order by match_priority, abs(date_diff('day', payment_batch_date, receipt_date)), payment_batch_line_id
    ) as receipt_rank
from exact_match_candidates;

create or replace view exact_matches as
select
    payment_batch_line_id,
    payment_batch_id,
    payment_batch_date,
    market_code,
    payment_batch_channel,
    primary_reference,
    line_total,
    receipt_line_id,
    receipt_ref,
    receipt_date,
    receipt_channel,
    transaction_status,
    receipt_exception_type,
    reference_resolution_method,
    receipt_amount,
    match_rule,
    match_priority,
    variance_amount
from exact_matches_ranked
where payment_batch_rank = 1
  and receipt_rank = 1;

create or replace view unmatched_after_exact as
select s.*
from payment_batch_keys s
left join exact_matches m
  on m.payment_batch_line_id = s.payment_batch_line_id
where m.payment_batch_line_id is null;

create or replace view cancellation_fee_pair_candidates as
with refunds as (
    select
        s.payment_batch_line_id as refund_line_id,
        s.payment_batch_id,
        s.transaction_date,
        s.market_code,
        s.reservation_ref,
        s.line_total as refund_amount
    from unmatched_after_exact s
    where s.line_total < 0
      and s.reservation_ref is not null
),
fees as (
    select
        s.payment_batch_line_id as fee_line_id,
        s.payment_batch_id,
        s.market_code,
        s.reservation_ref,
        s.line_total as fee_amount
    from unmatched_after_exact s
    join market_rules m
      on m.market_code = s.market_code
     and s.line_total = m.cancellation_fee_amount
    where s.reservation_ref is not null
)
select
    r.refund_line_id,
    f.fee_line_id,
    r.payment_batch_id,
    r.transaction_date as payment_batch_date,
    r.market_code,
    r.reservation_ref,
    r.refund_amount,
    f.fee_amount,
    round(r.refund_amount + f.fee_amount, 2) as expected_receipt_amount,
    rcpt.receipt_line_id,
    rcpt.receipt_ref,
    rcpt.transaction_date as receipt_date,
    rcpt.transaction_status,
    rcpt.receipt_exception_type,
    rcpt.reference_resolution_method
from refunds r
join fees f
  on f.market_code = r.market_code
 and f.reservation_ref = r.reservation_ref
 and f.payment_batch_id = r.payment_batch_id
join receipt_keys rcpt
  on rcpt.market_code = r.market_code
 and rcpt.channel_type = 'E_COMMERCE'
 and rcpt.reservation_ref = r.reservation_ref
 and rcpt.gross_amount = round(r.refund_amount + f.fee_amount, 2)
 and rcpt.transaction_status <> 'Rejected';

create or replace view cancellation_fee_matches as
select
    refund_line_id as payment_batch_line_id,
    payment_batch_id,
    payment_batch_date,
    market_code,
    'E_COMMERCE' as payment_batch_channel,
    reservation_ref as primary_reference,
    refund_amount as line_total,
    receipt_line_id,
    receipt_ref,
    receipt_date,
    'E_COMMERCE' as receipt_channel,
    transaction_status,
    receipt_exception_type,
    reference_resolution_method,
    expected_receipt_amount as receipt_amount,
    'CANCELLATION_FEE' as match_rule,
    10 as match_priority,
    cast(null as decimal(18, 2)) as variance_amount
from cancellation_fee_pair_candidates

union all

select
    fee_line_id as payment_batch_line_id,
    payment_batch_id,
    payment_batch_date,
    market_code,
    'E_COMMERCE' as payment_batch_channel,
    reservation_ref as primary_reference,
    fee_amount as line_total,
    receipt_line_id,
    receipt_ref,
    receipt_date,
    'E_COMMERCE' as receipt_channel,
    transaction_status,
    receipt_exception_type,
    reference_resolution_method,
    expected_receipt_amount as receipt_amount,
    'CANCELLATION_FEE' as match_rule,
    10 as match_priority,
    cast(null as decimal(18, 2)) as variance_amount
from cancellation_fee_pair_candidates;

create or replace view unmatched_after_cfee as
select s.*
from unmatched_after_exact s
left join cancellation_fee_matches c
  on c.payment_batch_line_id = s.payment_batch_line_id
where c.payment_batch_line_id is null;

create or replace view amount_variance_candidates as
select
    s.payment_batch_line_id,
    s.payment_batch_id,
    s.transaction_date as payment_batch_date,
    s.market_code,
    s.channel_type as payment_batch_channel,
    s.primary_reference,
    s.line_total,
    r.receipt_line_id,
    r.receipt_ref,
    r.transaction_date as receipt_date,
    r.channel_type as receipt_channel,
    r.transaction_status,
    r.receipt_exception_type,
    r.reference_resolution_method,
    r.gross_amount as receipt_amount,
    'AMOUNT_VARIANCE' as match_rule,
    20 as match_priority,
    round(r.gross_amount - s.line_total, 2) as variance_amount
from unmatched_after_cfee s
join receipt_keys r
  on s.market_code = r.market_code
 and sign(s.line_total) = sign(r.gross_amount)
 and r.transaction_status <> 'Rejected'
 and (
        (s.channel_type = 'E_COMMERCE' and s.reservation_ref is not null and s.reservation_ref = r.reservation_ref)
     or (s.channel_type <> 'E_COMMERCE' and s.invoice_ref is not null and s.invoice_ref = r.invoice_ref)
     or (s.channel_type <> 'E_COMMERCE' and s.reservation_ref is not null and s.reservation_ref = r.reservation_ref)
     or (s.acquirer_reference is not null and s.acquirer_reference = r.acquirer_reference)
 )
join channel_rules c
  on c.channel_type = s.channel_type
left join market_rules m
  on m.market_code = s.market_code
where abs(date_diff('day', s.transaction_date, r.transaction_date)) <= c.date_window_days
  and s.line_total <> r.gross_amount
  and not (
        m.cancellation_fee_amount is not null
    and s.line_total = m.cancellation_fee_amount
    and s.reservation_ref is not null
  );

create or replace view amount_variance_matches_ranked as
select
    *,
    row_number() over (
        partition by payment_batch_line_id
        order by abs(variance_amount), abs(date_diff('day', payment_batch_date, receipt_date)), receipt_line_id
    ) as payment_batch_rank,
    row_number() over (
        partition by receipt_line_id
        order by abs(variance_amount), abs(date_diff('day', payment_batch_date, receipt_date)), payment_batch_line_id
    ) as receipt_rank
from amount_variance_candidates;

create or replace view amount_variance_matches as
select
    payment_batch_line_id,
    payment_batch_id,
    payment_batch_date,
    market_code,
    payment_batch_channel,
    primary_reference,
    line_total,
    receipt_line_id,
    receipt_ref,
    receipt_date,
    receipt_channel,
    transaction_status,
    receipt_exception_type,
    reference_resolution_method,
    receipt_amount,
    match_rule,
    match_priority,
    variance_amount
from amount_variance_matches_ranked
where payment_batch_rank = 1
  and receipt_rank = 1;

create or replace view all_reconciliation_matches as
select * from exact_matches
union all
select * from cancellation_fee_matches
union all
select * from amount_variance_matches;

create or replace view reconciled_payment_batch_lines as
select
    s.payment_batch_line_id,
    s.payment_batch_id,
    s.transaction_date,
    s.market_code,
    s.channel_type,
    s.customer_name,
    s.customer_number,
    s.item_description,
    s.line_total,
    sum(s.line_total) over (partition by s.payment_batch_id) as payment_batch_total,
    s.invoice_ref,
    s.reservation_ref,
    s.acquirer_reference,
    s.primary_reference,
    s.reference_parse_status,
    m.receipt_line_id,
    m.receipt_ref,
    m.receipt_date,
    m.receipt_channel,
    m.transaction_status as receipt_status,
    m.receipt_exception_type,
    m.reference_resolution_method,
    m.match_rule,
    m.receipt_amount,
    m.variance_amount,
    case
        when m.payment_batch_line_id is not null and m.transaction_status = 'Rejected' then 'REJECTED'
        when m.match_rule = 'CANCELLATION_FEE' then 'CANCELLATION_FEE'
        when m.match_rule = 'AMOUNT_VARIANCE' then 'AMOUNT_VARIANCE'
        when m.payment_batch_line_id is not null then 'MATCH'
        when s.line_total = mr.cancellation_fee_amount and s.reservation_ref is not null then 'CHECK'
        when s.primary_reference is not null then 'CHECK'
        else 'MISSING_REFERENCE'
    end as match_status,
    case
        when m.payment_batch_line_id is not null and m.transaction_status = 'Rejected' then 'REJECTED'
        when m.match_rule in ('CANCELLATION_FEE', 'AMOUNT_VARIANCE') then 'REVIEW'
        when m.payment_batch_line_id is not null then 'READY'
        when s.primary_reference is not null then 'CHECK_QUEUE'
        else 'DATA_QUALITY_QUEUE'
    end as workflow_queue,
    case
        when m.receipt_ref is not null then m.receipt_ref
        when s.primary_reference is not null then 'CHECK'
        else 'MISSING_REFERENCE'
    end as reconciliation_target,
    case
        when m.payment_batch_line_id is not null and m.transaction_status = 'Rejected' then 'REJECTED_CARD_TRANSACTION'
        when m.match_rule = 'CANCELLATION_FEE' then 'CANCELLATION_FEE'
        when m.match_rule = 'AMOUNT_VARIANCE' then 'AMOUNT_VARIANCE'
        when s.primary_reference is not null and m.payment_batch_line_id is null then 'CHECK'
        else null
    end as review_reason
from payment_batch_keys s
left join all_reconciliation_matches m
  on m.payment_batch_line_id = s.payment_batch_line_id
left join market_rules mr
  on mr.market_code = s.market_code;
