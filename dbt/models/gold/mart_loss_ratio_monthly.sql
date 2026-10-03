-- Loss ratio per month and product: claims paid / premium due.
-- This is the "paid" view; an actuary would also look at claims by incident date.

with premium as (
    SELECT
        due_month as month,
        product_code,
        sum(amount_eur) as premium_eur
    FROM {{ ref('fct_premiums') }}
    GROUP BY 1, 2
),

paid as (
    SELECT
        date_trunc('month', paid_date)::date as month,
        product_code,
        sum(paid_amount) as claims_paid_eur,
        count(*) as claims_paid
    FROM {{ ref('fct_claims') }}
    WHERE paid_date is not null 
    GROUP BY 1, 2
),

reported as (
    SELECT 
        date_trunc('month', reported_date)::date as month,
        product_code,
        count(*) as claims_reported
    FROM {{ ref('fct_claims') }}
    GROUP BY 1, 2
)

SELECT
    pr.month,
    pr.product_code,
    pr.premium_eur,
    coalesce(pd.claims_paid_eur, 0) as claims_paid_eur,
    coalesce(pd.claims_paid, 0) as claims_paid,
    coalesce(rp.claims_reported, 0) as claims_reported,
    round(coalesce(pd.claims_paid_eur, 0) / nullif(pr.premium_eur, 0), 4) as loss_ratio
FROM premium pr
LEFT JOIN paid pd on pd.month = pr.month and pd.product_code = pr.product_code
LEFT JOIN reported rp on rp.month = pr.month and rp.product_code = pr.product_code
