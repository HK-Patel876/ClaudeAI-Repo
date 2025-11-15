/**
 * AI Signals Service
 * Real-time AI trading signals API client
 */
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || '';

class AISignalsService {
  /**
   * Get all live trading signals
   */
  async getLiveSignals() {
    try {
      const response = await axios.get(`${API_BASE}/api/v1/signals/live`);
      return response.data;
    } catch (error) {
      console.error('Error fetching live signals:', error);
      return { success: false, signals: [] };
    }
  }

  /**
   * Get AI signal for specific symbol
   */
  async getSignalForSymbol(symbol) {
    try {
      const response = await axios.get(`${API_BASE}/api/v1/signals/${symbol}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching signal for ${symbol}:`, error);
      return null;
    }
  }

  /**
   * Get top trading opportunities
   */
  async getTopOpportunities(limit = 10, minConfidence = 0.6, assetType = null) {
    try {
      const params = { limit, min_confidence: minConfidence };
      if (assetType) params.asset_type = assetType;

      const response = await axios.get(`${API_BASE}/api/v1/signals/top-opportunities`, { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching top opportunities:', error);
      return { success: false, opportunities: [] };
    }
  }

  /**
   * Analyze multiple symbols in batch
   */
  async analyzeBatch(symbols) {
    try {
      const response = await axios.post(`${API_BASE}/api/v1/signals/analyze-batch`, symbols);
      return response.data;
    } catch (error) {
      console.error('Error in batch analysis:', error);
      return { success: false, signals: [] };
    }
  }

  /**
   * Get AI system performance metrics
   */
  async getPerformance() {
    try {
      const response = await axios.get(`${API_BASE}/api/v1/signals/performance`);
      return response.data;
    } catch (error) {
      console.error('Error fetching performance:', error);
      return null;
    }
  }

  /**
   * Get watchlist signals
   */
  async getWatchlistSignals() {
    try {
      const response = await axios.get(`${API_BASE}/api/v1/signals/watchlist`);
      return response.data;
    } catch (error) {
      console.error('Error fetching watchlist signals:', error);
      return { success: false, signals: [] };
    }
  }

  /**
   * Get supported asset types and symbols
   */
  async getAssetTypes() {
    try {
      const response = await axios.get(`${API_BASE}/api/v1/signals/asset-types`);
      return response.data;
    } catch (error) {
      console.error('Error fetching asset types:', error);
      return { success: false, asset_types: {} };
    }
  }
}

export default new AISignalsService();
