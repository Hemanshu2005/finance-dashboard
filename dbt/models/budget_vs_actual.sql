-- Budget vs actual spend per user per category per month
-- Powers the budget status cards in the dashboard

{{ config(materialized='view') }}

SELECT
    b.user_id,
    b.month,
    b.category,
    b.monthly_limit,
    COALESCE(ms.total_spent, 0)                                         AS actual_spent,
    b.monthly_limit - COALESCE(ms.total_spent, 0)                       AS remaining,
    ROUND(COALESCE(ms.total_spent, 0) / NULLIF(b.monthly_limit, 0) * 100, 1) AS utilization_pct,
    CASE
        WHEN COALESCE(ms.total_spent, 0) > b.monthly_limit THEN TRUE
        ELSE FALSE
    END                                                                  AS over_budget
FROM {{ source('finance', 'budgets') }} b
LEFT JOIN {{ ref('monthly_spending') }} ms
    ON  b.user_id  = ms.user_id
    AND b.category = ms.category
    AND b.month    = ms.month::TEXT
