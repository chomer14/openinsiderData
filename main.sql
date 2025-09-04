SELECT DISTINCT t.company_id, t.id AS transaction_id
FROM transactions_gold t
JOIN insiders_gold i 
    ON i.id = t.insider_id
JOIN companies_gold c 
    ON c.id = t.company_id
JOIN transactions_titles_gold tt 
    ON tt.transaction_id = t.id AND tt.insider_id = i.id
WHERE t.is_purchase = 1
  AND EXISTS (
        -- Check that both CEO and CFO invested in same company within 30 days
        SELECT 1
        FROM transactions_gold t2
        JOIN transactions_titles_gold tt2 
            ON tt2.transaction_id = t2.id AND tt2.insider_id = t2.insider_id
        WHERE t2.company_id = t.company_id
          AND t2.is_purchase = 1
          AND ABS(t2.trade_date - t.trade_date) <= 30*24*60*60  -- 30 days in seconds
          AND tt2.title IN ('CEO', 'CFO')
        GROUP BY t2.company_id
        HAVING COUNT(DISTINCT tt2.title) = 2
  )
  AND EXISTS (
        -- Ensure more than 1 insider bought within 30 days
        SELECT 1
        FROM transactions_gold t3
        WHERE t3.company_id = t.company_id
          AND t3.is_purchase = 1
          AND ABS(t3.trade_date - t.trade_date) <= 30*24*60*60
        GROUP BY t3.company_id
        HAVING COUNT(DISTINCT t3.insider_id) > 1
  )
  AND EXISTS (
        -- Ensure at least one transaction > 50k in that window
        SELECT 1
        FROM transactions_gold t4
        WHERE t4.company_id = t.company_id
          AND t4.is_purchase = 1
          AND ABS(t4.trade_date - t.trade_date) <= 30*24*60*60
          AND t4.value > 50000
  );
