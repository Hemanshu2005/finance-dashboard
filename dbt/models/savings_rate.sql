-- Monthly savings rate per user
-- savings_rate = (income - expenses) / income

{{ config(materialized='view') }}

WITH income AS (
    SELECT
        user_id,
        DATE_TRUNC('month', date)::DATE AS month,
        SUM(amount)                     AS total_income
    FROM {{ source('finance', 'transactions') }}
    WHERE is_income = TRUE
    GROUP BY 1, 2
),
expenses AS (
    SELECT
        user_id,
        DATE_TRUNC('month', date)::DATE AS month,
        SUM(amount)                     AS total_expenses
    FROM {{ source('finance', 'transactions') }}
    WHERE is_income = FALSE
    GROUP BY 1, 2
)
SELECT
    i.user_id,
    i.month,
    i.total_income,
    COALESCE(e.total_expenses, 0)                               AS total_expenses,
    i.total_income - COALESCE(e.total_expenses, 0)              AS net_savings,
    ROUND(
        (i.total_income - COALESCE(e.total_expenses, 0))
        / NULLIF(i.total_income, 0) * 100, 2
    )                                                           AS savings_rate_pct
FROM income i
LEFT JOIN expenses e
    ON i.user_id = e.user_id AND i.month = e.month
