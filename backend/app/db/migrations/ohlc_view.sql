-- Drop existing Primary Key constraint on 'id' if it exists (constraint name usually market_prices_pkey)
ALTER TABLE market_prices DROP CONSTRAINT IF EXISTS market_prices_pkey;

-- Add new composite Primary Key covering the time partitioning column
ALTER TABLE market_prices ADD PRIMARY KEY (id, valid_from);

-- Convert market_prices to hypertable
SELECT create_hypertable('market_prices', 'valid_from', if_not_exists => TRUE, migrate_data => TRUE);

-- Create Continuous Aggregate View for 1-minute OHLC
CREATE MATERIALIZED VIEW ohlc_1min
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 minute', valid_from) AS bucket,
    security_ticker,
    first(price, valid_from) AS open,
    max(price) AS high,
    min(price) AS low,
    last(price, valid_from) AS close,
    sum(volume) AS volume
FROM market_prices
WHERE transaction_to IS NULL
GROUP BY bucket, security_ticker;

-- Add automatic refresh policy
SELECT add_continuous_aggregate_policy('ohlc_1min',
    start_offset => INTERVAL '1 day',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 minute');
