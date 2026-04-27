-- Monthly spending totals per user per category
-- Materialized as a table for dashboard query performance

{{ config(materialized='table') }}

SELECT
    user_id,
    DATE_TRUNC('month', date)::DATE     AS month,
    category,
    COUNT(*)                            AS transaction_count,
    SUM(amount)                         AS total_spent,
    AVG(amount)                         AS avg_transaction,
    MAX(amount)                         AS largest_transaction
FROM {{ source('finance', 'transactions') }}
WHERE is_income = FALSE
GROUP BY 1, 2, 3
