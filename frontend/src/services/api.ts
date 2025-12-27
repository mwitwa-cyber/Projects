import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8000/api/v1',
});

// ============ VALUATION ENDPOINTS ============
export const valuationAPI = {
    // Bond pricing
    bondPrice: async (payload: {
        face_value: number;
        coupon_rate: number;
        yield_rate: number;
        years_to_maturity: number;
        frequency?: number;
    }) => {
        const response = await api.post('/valuation/bond/price', payload);
        return response.data;
    },

    // YTM calculation
    bondYTM: async (payload: {
        face_value: number;
        coupon_rate: number;
        current_price: number;
        years_to_maturity: number;
        frequency?: number;
    }) => {
        const response = await api.post('/valuation/bond/ytm', payload);
        return response.data;
    },

    // DCF Valuation
    dcfValuation: async (payload: {
        initial_fcf: number;
        growth_rate: number;
        discount_rate: number;
        forecast_years: number;
        terminal_growth?: number;
    }) => {
        const response = await api.post('/valuation/equity/dcf', payload);
        return response.data;
    },

    // Annuity PV
    annuityPV: async (type: string, annuityPayment: number, rate: number, periods: number) => {
        const response = await api.get(`/valuation/annuity/${type}`, {
            params: { annuity_payment: annuityPayment, rate, periods }
        });
        return response.data;
    }
};

// ============ PORTFOLIO OPTIMIZATION ENDPOINTS ============
export const optimizationAPI = {
    // Portfolio optimization
    optimize: async (payload: {
        returns_data: Record<string, number[]>;
        objective: 'max_sharpe' | 'min_variance' | 'equal_weight';
        risk_free_rate: number;
        constraints?: Record<string, any>;
    }) => {
        const response = await api.post('/optimization/optimize', payload);
        return response.data;
    },

    // Efficient frontier
    efficientFrontier: async (payload: {
        returns_data: Record<string, number[]>;
        num_points?: number;
        risk_free_rate?: number;
    }) => {
        const response = await api.post('/optimization/efficient-frontier', payload);
        return response.data;
    },

    // Beta calculation
    calculateBeta: async (payload: {
        asset_returns: number[];
        market_returns: number[];
    }) => {
        const response = await api.post('/optimization/beta', payload);
        return response.data;
    }
};

// ============ RISK ANALYTICS ENDPOINTS ============
export const riskAPI = {
    // Value at Risk
    valueAtRisk: async (payload: {
        returns: number[];
        confidence_level: number;
        method: 'historical' | 'parametric' | 'monte_carlo';
    }) => {
        const response = await api.post('/optimization/risk/var', payload);
        return response.data;
    },

    // Conditional VaR
    conditionalVaR: async (payload: {
        returns: number[];
        confidence_level: number;
        method: 'historical' | 'parametric';
    }) => {
        const response = await api.post('/optimization/risk/cvar', payload);
        return response.data;
    }
};

// ============ HEALTH CHECK ============
export const healthCheck = async () => {
    try {
        const response = await axios.get('http://localhost:8000/');
        return response.data;
    } catch (error) {
        throw new Error('Backend is not responding');
    }
};

export default api;
