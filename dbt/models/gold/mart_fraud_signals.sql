-- Claims with two or more warning signs. Not proof of fraud, a list to check by hand.

with claims as (
    select * from {{ ref('fct_claims') }}
),

claims_last_year as (
    select a.claim_id, count(b.claim_id) as claims_12m
    from claims a
    join claims b
      on b.customer_id = a.customer_id
     and b.reported_date between dateadd(day, -365, a.reported_date) and a.reported_date
    group by a.claim_id
),

flags as (
    select
        c.*,
        y.claims_12m,
        c.days_after_policy_start <= 30                           as flag_early_claim,
        c.days_to_report >= 7                                     as flag_late_report,
        c.claimed_amount >= 0.8 * c.catalog_value_eur             as flag_near_car_value,
        y.claims_12m >= 3                                         as flag_repeat_claimer
    from claims c
    join claims_last_year y on y.claim_id = c.claim_id
)

select
    claim_id,
    policy_id,
    customer_id,
    claim_type,
    claim_status,
    reported_date,
    claimed_amount,
    paid_amount,
    catalog_value_eur,
    days_after_policy_start,
    days_to_report,
    claims_12m,
    flag_early_claim::int + flag_late_report::int
        + flag_near_car_value::int + flag_repeat_claimer::int     as risk_score,
    -- glue the reasons together, then drop the final '; '
    regexp_replace(
        iff(flag_early_claim, 'claim within 30 days of start; ', '')
        || iff(flag_late_report, 'reported a week or more late; ', '')
        || iff(flag_near_car_value, 'claim near full car value; ', '')
        || iff(flag_repeat_claimer, '3+ claims in 12 months; ', ''),
    '; $', '')                                                    as reasons
from flags
where flag_early_claim::int + flag_late_report::int
      + flag_near_car_value::int + flag_repeat_claimer::int >= 2
