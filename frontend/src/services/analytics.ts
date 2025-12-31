import axios from 'axios';
import type { OHLCData, YieldCurveResponse, CAPMResponse } from '../types/analytics';

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
    }
};
