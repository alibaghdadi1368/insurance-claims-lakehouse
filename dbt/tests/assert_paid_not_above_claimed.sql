-- A payout can never be higher than what the customer asked for.
-- The test fails if this query returns any rows.

SELECT
    claim_id,
    claimed_amount,
    paid_amount
FROM {{ ref('fct_claims') }}
WHERE paid_amount > claimed_amount