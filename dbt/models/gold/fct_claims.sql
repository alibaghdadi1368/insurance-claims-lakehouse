-- One row per claim, with the policy, car and customer it belongs to.
SELECT
    cl.claim_id,
    cl.policy_id,
    p.customer_id,
    p.vehicle_id,
    p.product_code,
    c.pc4,
    cl.claim_type,
    cl.channel,
    cl.claim_status,
    cl.incident_date,
    cl.reported_date,
    cl.assessed_date,
    cl.decided_date,
    cl.paid_date,
    cl.claimed_amount,
    cl.approved_amount,
    cl.paid_amount,
    cl.rejection_reason,
    v.catalog_value_eur,
    datediff(day, cl.incident_date, cl.reported_date) as days_to_report,
    datediff(day, cl.reported_date, cl.decided_date) as days_to_decision,
    datediff(day, cl.reported_date, cl.paid_date) as days_to_payment,
    datediff(day, p.start_date, cl.incident_date) as days_after_policy_start,
    datediff(year, c.date_of_birth, cl.incident_date) as driver_age
FROM {{ ref('int_claims') }} cl 
JOIN {{ ref('stg_policies') }} p on p.policy_id = cl.policy_id
JOIN {{ ref('stg_customers') }} c on c.customer_id = p.customer_id
LEFT JOIN {{ ref('stg_vehicles') }} v on v.vehicle_id = p.vehicle_id