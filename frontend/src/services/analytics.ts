import axios from 'axios';
import type {
    OHLCData,
    YieldCurveResponse,
    CAPMResponse,
    RiskMetrics,
    RiskMetricsHistory,
    RiskMetricsHistoryResponse,
    TaskResponse,
    BatchTaskResponse
} from '../types/analytics';

const API_URL = 'http://localhost:8000/api/v1';

export const analyticsService = {
    getYieldCurve: async (date?: string): Promise<YieldCurveResponse> => {
        const response = await axios.get(`${API_URL}/analytics/yield-curve`, {
            params: { date }
        });
        return response.data;
    },

    getCAPM: async (ticker: string, rf?: number): Promise<CAPMResponse> => {
        const response = await axios.get(`${API_URL}/analytics/capm/${ticker}`, {
            params: { rf }
        });
        return response.data;
    },

    getOHLC: async (ticker: string, days: number = 30): Promise<OHLCData[]> => {
        const response = await axios.get(`${API_URL}/market-data/ohlc/${ticker}`, {
            params: { days }
        });
        return response.data;
    },

    runBacktest: async (weights: Record<string, number>, startDate: string, initialCapital: number = 10000) => {
        const response = await axios.post(`${API_URL}/backtest/run`, {
            weights,
            start_date: startDate,
            initial_capital: initialCapital
        });
        return response.data;
    },

    // ==================== Risk Metrics API ====================

    /**
     * Calculate risk metrics on-demand for an asset.
     * Returns beta, VaR(95%), and observation count.
     */
    getRiskMetrics: async (
        assetId: number,
        benchmarkId: number,
        lookbackDays: number = 365
    ): Promise<RiskMetrics> => {
        const response = await axios.get(`${API_URL}/analytics/risk/${assetId}`, {
            params: {
                benchmark_id: benchmarkId,
                lookback_days: lookbackDays
            }
        });
        return response.data;
    },

    /**
     * Get the latest stored risk metrics from database.
     * Faster than on-demand calculation.
     */
    getLatestRiskMetrics: async (assetId: number): Promise<RiskMetricsHistory> => {
        const response = await axios.get(`${API_URL}/analytics/risk/${assetId}/latest`);
        return response.data;
    },

    /**
     * Get historical risk metrics for trend analysis.
     */
    getRiskMetricsHistory: async (
        assetId: number,
        limit: number = 30
    ): Promise<RiskMetricsHistoryResponse> => {
        const response = await axios.get(`${API_URL}/analytics/risk/${assetId}/history`, {
            params: { limit }
        });
        return response.data;
    },

    /**
     * Trigger async risk calculation for a single asset.
     * Returns task ID for tracking.
     */
    triggerRiskCalculation: async (
        assetId: number,
        benchmarkId?: number,
        lookbackDays?: number
    ): Promise<TaskResponse> => {
        const response = await axios.post(
            `${API_URL}/analytics/risk/calculate/${assetId}`,
            null,
            { params: { benchmark_id: benchmarkId, lookback_days: lookbackDays } }
        );
        return response.data;
    },

    /**
     * Trigger async risk calculation for all assets.
     * Returns batch task info.
     */
    triggerBatchRiskCalculation: async (
        benchmarkId?: number,
        lookbackDays?: number,
        assetIds?: number[]
    ): Promise<BatchTaskResponse> => {
        const response = await axios.post(
            `${API_URL}/analytics/risk/calculate-all`,
            null,
            {
                params: {
                    benchmark_id: benchmarkId,
                    lookback_days: lookbackDays,
                    asset_ids: assetIds
                }
            }
        );
        return response.data;
    }
};
