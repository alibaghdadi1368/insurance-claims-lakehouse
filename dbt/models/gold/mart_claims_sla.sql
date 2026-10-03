-- How fast claims are handled, per report month and claim type.
-- Service level: a decision within 14 days, money within 30 days of the report.

SELECT
    date_trunc('month', reported_date)::date as month,
    claim_type,
    count(*)  as claims,
    count_if(claim_status not in ('paid', 'rejected')) as still_open,
    median(days_to_decision) as median_days_to_decision,
    median(days_to_payment) as median_days_to_payment,
    round(count_if(days_to_decision <= 14) / nullif(count_if(decided_date is not null), 0), 4) as pct_decided_within_14d,
    round(count_if(days_to_payment <= 30) / nullif(count_if(paid_date is not null), 0), 4) as pct_paid_within_30d
FROM {{ ref('fct_claims') }}
GROUP BY 1, 2
