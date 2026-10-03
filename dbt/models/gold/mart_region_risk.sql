-- Claim frequency per municipality: how many claims per 1,000 policies.

with policies as (
    SELECT
        p.policy_id,
        c.pc4
    FROM {{ ref('stg_policies') }} p
    join {{ ref('stg_customers') }} c on c.customer_id = p.customer_id
),

by_postcode as (
    SELECT
        pol.pc4,
        count(DISTINCT pol.policy_id) as policies,
        count(DISTINCT cl.claim_id) as claims,
        coalesce(sum(cl.paid_amount), 0) as claims_paid_eur
    FROM policies pol
    LEFT JOIN {{ ref('fct_claims') }} cl on cl.policy_id = pol.policy_id
    GROUP BY pol.pc4
)

SELECT
    r.gm_code,
    r.municipality,
    round(avg(r.urbanity_level)) as urbanity_level,
    sum(b.policies) as policies,
    sum(b.claims) as claims,
    sum(b.claims_paid_eur) as claims_paid_eur,
    round(1000 * sum(b.claims) / nullif(sum(b.policies), 0), 1) as claims_per_1000_policies
    FROM by_postcode b
    JOIN {{ ref('dim_region') }} r on r.pc4 = b.pc4
    GROUP BY r.gm_code, r.municipality