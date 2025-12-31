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
