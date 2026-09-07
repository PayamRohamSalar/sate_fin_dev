-- Payment series report for Persian year 1405
-- Run against the sate_db database (pgAdmin Query Tool)

-- 1) Full breakdown: every series recorded for 1405, with counts and totals
SELECT
    series,
    status,
    COUNT(*)                          AS num_payments,
    SUM(amount)                       AS total_amount,
    COUNT(DISTINCT contract_tracking_code) AS num_contracts
FROM payments
WHERE payment_year = 1405
  AND is_deleted = FALSE
GROUP BY series, status
ORDER BY series;

-- 2) Highest finalized series number in the standard "05-NN" sequence for 1405
SELECT
    MAX(CAST(SPLIT_PART(series, '-', 2) AS INT)) AS max_series_number,
    'series ' || LPAD(MAX(CAST(SPLIT_PART(series, '-', 2) AS INT))::TEXT, 2, '0') AS max_series_label
FROM payments
WHERE payment_year = 1405
  AND is_deleted = FALSE
  AND status = 'Final'
  AND series LIKE '05-%';

-- 3) Any series values for 1405 that do NOT follow the standard "05-NN" pattern
--    (flags anomalies / manually entered records outside the normal batch sequence)
SELECT
    series,
    status,
    COUNT(*) AS num_payments,
    SUM(amount) AS total_amount
FROM payments
WHERE payment_year = 1405
  AND is_deleted = FALSE
  AND series !~ '^05-[0-9]+$'
GROUP BY series, status
ORDER BY series;

-- 4) Overall totals for 1405 by status (Final vs Draft)
SELECT
    status,
    COUNT(*) AS num_payments,
    SUM(amount) AS total_amount,
    COUNT(DISTINCT contract_tracking_code) AS num_contracts
FROM payments
WHERE payment_year = 1405
  AND is_deleted = FALSE
GROUP BY status;
