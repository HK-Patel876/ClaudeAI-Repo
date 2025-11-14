import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_BASE || '/api/v1';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
});

export const tradingAPI = {
  getPortfolio: () => api.get('/trading/portfolio'),
  getPositions: () => api.get('/trading/positions'),
  getOrders: (limit = 50) => api.get(`/trading/orders?limit=${limit}`),
  analyzeSymbol: (symbol) => api.post(`/trading/analyze/${symbol}`),
  executeTrade: (symbol) => api.post(`/trading/execute/${symbol}`),
  cancelOrder: (orderId) => api.delete(`/trading/orders/${orderId}`),
};

export const dataAPI = {
  getMarketData: (symbol, timeframe = '1D', limit = 100) => 
    api.get(`/data/market/${symbol}?timeframe=${timeframe}&limit=${limit}`),
  getCurrentPrice: (symbol) => api.get(`/data/price/${symbol}`),
  getIndicators: (symbol) => api.get(`/data/indicators/${symbol}`),
  getNews: (symbol, limit = 10) => api.get(`/data/news/${symbol}?limit=${limit}`),
  getSnapshot: (symbols = 'AAPL,MSFT,GOOGL,TSLA,AMZN') => 
    api.get(`/data/snapshot?symbols=${symbols}`),
};

export const systemAPI = {
  health: () => api.get('/system/health'),
  getMetrics: () => api.get('/system/metrics'),
  getAlerts: () => api.get('/system/alerts'),
  getConfig: () => api.get('/system/config'),
  updateConfig: (config) => api.post('/system/config', config),
  getProviderStatus: () => api.get('/system/providers'),
};

export const settingsAPI = {
  getSettings: () => api.get('/settings'),
  updateSettings: (settings) => api.put('/settings', settings),
};

export const watchlistAPI = {
  getWatchlist: () => api.get('/watchlist'),
  addSymbol: (symbol, notes) => api.post('/watchlist', { symbol, notes }),
  removeSymbol: (symbol) => api.delete(`/watchlist/${symbol}`),
  getAlerts: (activeOnly = false) => api.get(`/alerts?active_only=${activeOnly}`),
  createAlert: (alert) => api.post('/alerts', alert),
  deleteAlert: (alertId) => api.delete(`/alerts/${alertId}`),
};

export const analysisAPI = {
  getAnalyses: (limit = 50, symbol = null, agentType = null) => {
    let url = `/analyses?limit=${limit}`;
    if (symbol) url += `&symbol=${symbol}`;
    if (agentType) url += `&agent_type=${agentType}`;
    return api.get(url);
  },
  getPerformance: (days = 30) => api.get(`/performance?days=${days}`),
};

export default api;
