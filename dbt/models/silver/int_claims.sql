-- turns many events into one row per claim. int_ marks an intermediate model that isn't meant for end users.
-- One row per claim: its current status and the date and amount of every step.

with steps as (
    SELECT
        claim_id,
        any_value(policy_id) as policy_id,
        max(claim_type) as claim_type,
        max(incident_date) as incident_date,
        max(channel) as channel,
        -- conditional aggregation: min(iff(event_type = 'CLAIM_PAID', event_ts, null)) looks only at the paid event of each claim. It pivots rows into columns without a single join.
        min(iff(event_type = 'CLAIM_REPORTED', event_ts, null))::date as reported_date,
        min(iff(event_type = 'CLAIM_ASSESSED', event_ts, null))::date as assessed_date,
        min(iff(event_type in ('CLAIM_APPROVED', 'CLAIM_REJECTED'), event_ts, null))::date as decided_date,
        min(iff(event_type = 'CLAIM_PAID', event_ts, null))::date as paid_date,
        max(claimed_amount) as claimed_amount,
        max(assessed_amount) as assessed_amount,
        max(approved_amount) as approved_amount,
        max(paid_amount) as paid_amount,
        max(rejection_reason) as rejection_reason,
        max(event_ts) as last_event_ts
    FROM {{ ref('stg_claim_events') }}
    GROUP BY claim_id
)

SELECT
    *,
    CASE 
        WHEN paid_date is not null THEN 'paid'
        WHEN rejection_reason is not null THEN 'rejected'
        WHEN decided_date is not null THEN 'approved'
        WHEN assessed_date is not null THEN 'assessed'  
        ELSE  'reported'
    END as claim_status
FROM steps
-- One row per claim: its current status and the date and amount of every step.
WHERE reported_date is not null