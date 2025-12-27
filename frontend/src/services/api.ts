import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8000/api/v1',
});

export const getPrice = async (ticker: string, date: string) => {
    const response = await api.get(`/market-data/prices/${ticker}`, { params: { date } });
    return response.data;
};

export const getSecurities = async () => {
    const response = await api.get('/market-data/securities');
    return response.data;
};

export default api;
