-- One row per monthly instalment.
SELECT
    pr.payment_id,
    pr.policy_id,
    p.customer_id,
    p.product_code,
    c.pc4,
    pr.due_date,
    date_trunc('month', pr.due_date)::date  as due_month,
    pr.amount_eur,
    pr.paid_date,
    pr.paid_date is not null as is_paid,
    datediff(day, pr.due_date, pr.paid_date) as days_late,
    pr.payment_method
FROM {{ ref('stg_premiums') }} pr
JOIN {{ ref('stg_policies') }} p on p.policy_id = pr.policy_id
join {{ ref('stg_customers') }} c on c.customer_id = p.customer_id
