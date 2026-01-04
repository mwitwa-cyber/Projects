-- ============================================================
-- Weekly Returns Continuous Aggregate for LuSE Risk Analytics
-- ============================================================

-- Fix Primary Key for TimescaleDB (must include time column)
ALTER TABLE market_prices DROP CONSTRAINT IF EXISTS market_prices_pkey CASCADE;
ALTER TABLE market_prices ADD PRIMARY KEY (id, valid_from);

-- Ensure market_prices is a hypertable (required for continuous aggregates)
-- This will migrate existing data if needed
SELECT create_hypertable('market_prices', 'valid_from', chunk_time_interval => INTERVAL '1 week', if_not_exists => TRUE, migrate_data => TRUE);

-- Drop existing view if it exists (for updates)
DROP MATERIALIZED VIEW IF EXISTS weekly_returns CASCADE;

-- Create Weekly OHLC + Returns Continuous Aggregate
-- Sourced from 'market_prices' (Bitemporal table)
-- Aggregates by Ticker (no JOINs allowed in continuous aggregates on some versions)
CREATE MATERIALIZED VIEW weekly_returns
WITH (timescaledb.continuous) AS
SELECT
    -- Time bucket: Weekly (starts Monday)
    time_bucket('1 week', valid_from) AS week_start,
    
    -- Asset identifier (Ticker string)
    security_ticker,
    
    -- Weekly OHLC prices (for charting)
    first(price, valid_from) AS open_price,
    max(price) AS high_price,
    min(price) AS low_price,
    last(price, valid_from) AS close_price,
    
    -- Trading activity metrics
    count(*) AS trading_days,
    sum(volume) AS total_volume,
    
    -- Week-end close for return calculation
    last(price, valid_from) AS week_close

FROM market_prices
WHERE transaction_to IS NULL  -- Only active records
GROUP BY time_bucket('1 week', valid_from), security_ticker
WITH NO DATA;

-- Refresh the materialized view with existing data
REFRESH MATERIALIZED VIEW weekly_returns;

-- Add automatic refresh policy
-- Refreshes every hour, looking back 4 weeks for late data
SELECT add_continuous_aggregate_policy('weekly_returns',
    start_offset => INTERVAL '4 weeks',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- Create index for fast lookups by ticker
CREATE INDEX IF NOT EXISTS idx_weekly_returns_ticker 
ON weekly_returns (security_ticker, week_start DESC);


-- ============================================================
-- Function: Calculate Weekly Log Returns
-- ============================================================
-- Returns weekly observations with log returns for risk calculations
-- Handles forward-fill for weeks with no trading (LOCF)

CREATE OR REPLACE FUNCTION get_weekly_observations(
    p_asset_id INTEGER,
    p_benchmark_id INTEGER,
    p_lookback_weeks INTEGER DEFAULT 52
)
RETURNS TABLE (
    week_start DATE,
    asset_close NUMERIC,
    benchmark_close NUMERIC,
    asset_log_return NUMERIC,
    benchmark_log_return NUMERIC
) AS $$
DECLARE
    v_asset_ticker VARCHAR;
    v_benchmark_ticker VARCHAR;
BEGIN
    -- unique lookup for tickers
    SELECT ticker INTO v_asset_ticker FROM securities WHERE id = p_asset_id;
    SELECT ticker INTO v_benchmark_ticker FROM securities WHERE id = p_benchmark_id;

    IF v_asset_ticker IS NULL OR v_benchmark_ticker IS NULL THEN
        RAISE EXCEPTION 'Asset or Benchmark ID not found';
    END IF;

    RETURN QUERY
    WITH 
    -- Generate complete week series for the lookback period
    week_series AS (
        SELECT generate_series(
            date_trunc('week', CURRENT_DATE - (p_lookback_weeks || ' weeks')::INTERVAL)::DATE,
            date_trunc('week', CURRENT_DATE)::DATE,
            '1 week'::INTERVAL
        )::DATE AS week_start
    ),
    
    -- Get asset weekly closes using Ticker
    asset_weekly AS (
        SELECT 
            w.week_start,
            wr.close_price
        FROM week_series w
        LEFT JOIN weekly_returns wr 
            ON w.week_start = wr.week_start::DATE 
            AND wr.security_ticker = v_asset_ticker
    ),
    
    -- Get benchmark weekly closes using Ticker
    benchmark_weekly AS (
        SELECT 
            w.week_start,
            wr.close_price
        FROM week_series w
        LEFT JOIN weekly_returns wr 
            ON w.week_start = wr.week_start::DATE 
            AND wr.security_ticker = v_benchmark_ticker
    ),
    
    -- Join and forward-fill missing values (LOCF)
    combined AS (
        SELECT 
            a.week_start,
            -- Forward-fill asset price (Last Observation Carried Forward)
            COALESCE(
                a.close_price, 
                LAG(a.close_price) OVER (ORDER BY a.week_start)
            ) AS asset_close,
            -- Forward-fill benchmark price
            COALESCE(
                b.close_price,
                LAG(b.close_price) OVER (ORDER BY b.week_start)
            ) AS benchmark_close
        FROM asset_weekly a
        JOIN benchmark_weekly b ON a.week_start = b.week_start
    ),
    
    -- Calculate log returns
    with_returns AS (
        SELECT
            combined.week_start,
            combined.asset_close::NUMERIC,
            combined.benchmark_close::NUMERIC,
            -- Log return: ln(P_t / P_t-1)
            LN(combined.asset_close / NULLIF(LAG(combined.asset_close) OVER (ORDER BY combined.week_start), 0))::NUMERIC AS asset_log_return,
            LN(combined.benchmark_close / NULLIF(LAG(combined.benchmark_close) OVER (ORDER BY combined.week_start), 0))::NUMERIC AS benchmark_log_return
        FROM combined
        WHERE combined.asset_close IS NOT NULL 
          AND combined.benchmark_close IS NOT NULL
    )
    
    SELECT 
        wr.week_start,
        wr.asset_close,
        wr.benchmark_close,
        wr.asset_log_return,
        wr.benchmark_log_return
    FROM with_returns wr
    WHERE wr.asset_log_return IS NOT NULL 
      AND wr.benchmark_log_return IS NOT NULL
    ORDER BY wr.week_start;
END;
$$ LANGUAGE plpgsql;


-- ============================================================
-- Function: Calculate Beta from Weekly Returns
-- ============================================================
-- Calculates beta directly in PostgreSQL for performance

CREATE OR REPLACE FUNCTION calculate_beta_sql(
    p_asset_id INTEGER,
    p_benchmark_id INTEGER,
    p_lookback_weeks INTEGER DEFAULT 52
)
RETURNS TABLE (
    beta NUMERIC,
    correlation NUMERIC,
    observation_count INTEGER,
    asset_volatility NUMERIC,
    benchmark_volatility NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    WITH returns AS (
        SELECT 
            asset_log_return,
            benchmark_log_return
        FROM get_weekly_observations(p_asset_id, p_benchmark_id, p_lookback_weeks)
    )
    SELECT
        -- Beta = Covariance / Variance(benchmark)
        ROUND(
            (COVAR_SAMP(r.asset_log_return, r.benchmark_log_return) / 
            NULLIF(VAR_SAMP(r.benchmark_log_return), 0))::NUMERIC,
            4
        ) AS beta,
        
        -- Correlation coefficient
        ROUND(CORR(r.asset_log_return, r.benchmark_log_return)::NUMERIC, 4) AS correlation,
        
        -- Observation count
        COUNT(*)::INTEGER AS observation_count,
        
        -- Asset weekly volatility (annualized)
        ROUND((STDDEV_SAMP(r.asset_log_return) * SQRT(52))::NUMERIC, 4) AS asset_volatility,
        
        -- Benchmark weekly volatility (annualized)
        ROUND((STDDEV_SAMP(r.benchmark_log_return) * SQRT(52))::NUMERIC, 4) AS benchmark_volatility
        
    FROM returns r;
END;
$$ LANGUAGE plpgsql;


-- ============================================================
-- Function: Calculate VaR from Weekly Returns  
-- ============================================================
-- Historical VaR at 95% confidence level

CREATE OR REPLACE FUNCTION calculate_var_sql(
    p_asset_id INTEGER,
    p_lookback_weeks INTEGER DEFAULT 52,
    p_confidence NUMERIC DEFAULT 0.95
)
RETURNS TABLE (
    var_95 NUMERIC,
    cvar_95 NUMERIC,
    observation_count INTEGER,
    min_return NUMERIC,
    max_return NUMERIC
) AS $$
DECLARE
    v_percentile NUMERIC;
BEGIN
    -- Calculate the percentile rank (e.g., 5% for 95% VaR)
    v_percentile := 1 - p_confidence;
    
    RETURN QUERY
    WITH returns AS (
        SELECT asset_log_return
        FROM get_weekly_observations(p_asset_id, p_asset_id, p_lookback_weeks)
    ),
    stats AS (
        SELECT 
            PERCENTILE_CONT(v_percentile) WITHIN GROUP (ORDER BY asset_log_return) as var_threshold,
            COUNT(*) as total_obs,
            MIN(asset_log_return) as min_ret,
            MAX(asset_log_return) as max_ret
        FROM returns
    )
    SELECT
        -- VaR (as positive percentage usually, but kept as return sign here)
        ROUND((s.var_threshold * 100)::NUMERIC, 4) AS var_95,
        
        -- CVaR: Average of returns below or equal to VaR threshold
        ROUND((AVG(r.asset_log_return) * 100)::NUMERIC, 4) AS cvar_95,
        
        s.total_obs::INTEGER AS observation_count,
        ROUND((s.min_ret * 100)::NUMERIC, 4) AS min_return,
        ROUND((s.max_ret * 100)::NUMERIC, 4) AS max_return
        
    FROM returns r, stats s
    WHERE r.asset_log_return <= s.var_threshold
    GROUP BY s.var_threshold, s.total_obs, s.min_ret, s.max_ret;
END;
$$ LANGUAGE plpgsql;


-- ============================================================
-- Quick test query (run after applying migration)
-- ============================================================
-- SELECT * FROM get_weekly_observations(1, 2, 52) LIMIT 10;
-- SELECT * FROM calculate_beta_sql(1, 2, 52);
-- SELECT * FROM calculate_var_sql(1, 52, 0.95);
