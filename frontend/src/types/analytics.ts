export interface OHLCData {
    time: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
}

export interface YieldCurvePoint {
    ttm: number;
    yield: number;
}

export interface YieldCurveParams {
    beta0: number;
    beta1: number;
    beta2: number;
    lambda: number;
}

export interface YieldCurveResponse {
    parameters: YieldCurveParams;
    curve: YieldCurvePoint[];
    observed: YieldCurvePoint[];
}

export interface CAPMResponse {
    ticker: string;
    beta: number;
    expected_return: number;
    annualized_market_return: number;
    risk_free_rate: number;
    liquidity_premium: number;
    average_dollar_volume: number;
    r_squared: number;
}

// Risk Metrics Types
export interface RiskMetrics {
    beta: number;
    var_95: number;
    observation_count: number;
    calculation_date: string;
    asset_id: number;
    benchmark_id: number;
    lookback_days: number;
}

export interface RiskMetricsHistory {
    id: number;
    asset_id: number;
    benchmark_id: number;
    calculation_date: string;
    beta: number;
    var_95: number;
    var_99?: number;
    volatility?: number;
    sharpe_ratio?: number;
    sortino_ratio?: number;
    max_drawdown?: number;
    observation_count: number;
    lookback_days: number;
    calculation_status: string;
    error_message?: string;
    created_at: string;
}

export interface TaskResponse {
    status: string;
    task_id?: string;
    message: string;
}

export interface BatchTaskResponse {
    status: string;
    total_assets: number;
    message: string;
    tasks?: Array<{ asset_id: number; task_id: string }>;
}

export interface RiskMetricsHistoryResponse {
    asset_id: number;
    count: number;
    metrics: RiskMetricsHistory[];
}
