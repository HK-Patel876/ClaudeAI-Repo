/**
 * Multi-Ticker Grid - Real-time market overview with AI signals
 * Compact table view for monitoring multiple symbols
 */
import React, { useState, useEffect, useCallback } from 'react';
import aiSignalsService from '../services/aiSignals';
import './MultiTickerGrid.css';

const MultiTickerGrid = ({ onSymbolClick }) => {
  const [tickers, setTickers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // all, stocks, crypto, indices
  const [sortColumn, setSortColumn] = useState('confidence');
  const [sortDirection, setSortDirection] = useState('desc');

  // Fetch ticker data
  const fetchTickers = useCallback(async () => {
    try {
      const data = await aiSignalsService.getWatchlistSignals();
      if (data.success) {
        setTickers(data.signals);
      }
      setLoading(false);
    } catch (error) {
      console.error('Error fetching tickers:', error);
      setLoading(false);
    }
  }, []);

  // Auto-refresh every 1 second
  useEffect(() => {
    fetchTickers();
    const interval = setInterval(fetchTickers, 1000);
    return () => clearInterval(interval);
  }, [fetchTickers]);

  // Filter tickers
  const filteredTickers = tickers.filter(ticker => {
    if (filter === 'all') return true;
    if (filter === 'stocks') return ticker.asset_type === 'stock';
    if (filter === 'crypto') return ticker.asset_type === 'crypto';
    if (filter === 'indices') return ticker.asset_type === 'index';
    return true;
  });

  // Sort tickers
  const sortedTickers = [...filteredTickers].sort((a, b) => {
    let aVal, bVal;

    switch (sortColumn) {
      case 'symbol':
        aVal = a.symbol;
        bVal = b.symbol;
        break;
      case 'price':
        aVal = a.current_price;
        bVal = b.current_price;
        break;
      case 'change':
        aVal = a.predicted_change_pct;
        bVal = b.predicted_change_pct;
        break;
      case 'confidence':
        aVal = a.confidence;
        bVal = b.confidence;
        break;
      case 'signal':
        const signalOrder = { 'STRONG_BUY': 5, 'BUY': 4, 'NEUTRAL': 3, 'SELL': 2, 'STRONG_SELL': 1 };
        aVal = signalOrder[a.signal] || 0;
        bVal = signalOrder[b.signal] || 0;
        break;
      default:
        aVal = a.confidence;
        bVal = b.confidence;
    }

    if (typeof aVal === 'string') {
      return sortDirection === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    }

    return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
  });

  const handleSort = (column) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(column);
      setSortDirection('desc');
    }
  };

  const getSignalColor = (signal) => {
    const colors = {
      'STRONG_BUY': '#00ff88',
      'BUY': '#4ade80',
      'NEUTRAL': '#94a3b8',
      'SELL': '#f87171',
      'STRONG_SELL': '#ff3366'
    };
    return colors[signal] || '#94a3b8';
  };

  const getSignalBadge = (signal) => {
    const badges = {
      'STRONG_BUY': 'S-BUY',
      'BUY': 'BUY',
      'NEUTRAL': 'HOLD',
      'SELL': 'SELL',
      'STRONG_SELL': 'S-SELL'
    };
    return badges[signal] || 'HOLD';
  };

  if (loading) {
    return (
      <div className="multi-ticker-grid">
        <div className="grid-header">
          <h2>Market Overview</h2>
        </div>
        <div className="loading-state">
          <div className="spinner-small"></div>
          <p>Loading market data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="multi-ticker-grid">
      <div className="grid-header">
        <h2>Market Overview</h2>
        <div className="grid-controls">
          <div className="filter-tabs">
            <button
              className={`tab ${filter === 'all' ? 'active' : ''}`}
              onClick={() => setFilter('all')}
            >
              All ({tickers.length})
            </button>
            <button
              className={`tab ${filter === 'stocks' ? 'active' : ''}`}
              onClick={() => setFilter('stocks')}
            >
              Stocks
            </button>
            <button
              className={`tab ${filter === 'crypto' ? 'active' : ''}`}
              onClick={() => setFilter('crypto')}
            >
              Crypto
            </button>
            <button
              className={`tab ${filter === 'indices' ? 'active' : ''}`}
              onClick={() => setFilter('indices')}
            >
              Indices
            </button>
          </div>
        </div>
      </div>

      <div className="ticker-table-container">
        <table className="ticker-table">
          <thead>
            <tr>
              <th onClick={() => handleSort('symbol')} className="sortable">
                Symbol {sortColumn === 'symbol' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('price')} className="sortable">
                Price {sortColumn === 'price' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('change')} className="sortable">
                Predicted {sortColumn === 'change' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('signal')} className="sortable">
                Signal {sortColumn === 'signal' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('confidence')} className="sortable">
                Confidence {sortColumn === 'confidence' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th>Scores</th>
              <th>Trade Plan</th>
            </tr>
          </thead>
          <tbody>
            {sortedTickers.map((ticker, index) => (
              <tr
                key={`${ticker.symbol}-${index}`}
                className="ticker-row"
                onClick={() => onSymbolClick && onSymbolClick(ticker.symbol)}
              >
                <td className="symbol-cell">
                  <span className="symbol-name">{ticker.symbol}</span>
                  <span className="asset-type">{ticker.asset_type}</span>
                </td>
                <td className="price-cell">
                  ${ticker.current_price.toFixed(2)}
                </td>
                <td className={`change-cell ${ticker.predicted_change_pct >= 0 ? 'positive' : 'negative'}`}>
                  {ticker.predicted_change_pct >= 0 ? '+' : ''}
                  {ticker.predicted_change_pct.toFixed(2)}%
                </td>
                <td className="signal-cell">
                  <span
                    className="signal-badge"
                    style={{ backgroundColor: getSignalColor(ticker.signal) }}
                  >
                    {getSignalBadge(ticker.signal)}
                  </span>
                </td>
                <td className="confidence-cell">
                  <div className="confidence-mini-bar">
                    <div
                      className="confidence-mini-fill"
                      style={{
                        width: `${ticker.confidence * 100}%`,
                        backgroundColor: getSignalColor(ticker.signal)
                      }}
                    />
                  </div>
                  <span className="confidence-text">{(ticker.confidence * 100).toFixed(0)}%</span>
                </td>
                <td className="scores-cell">
                  <div className="mini-scores">
                    <div className="mini-score">
                      <span className="mini-score-label">T</span>
                      <span className="mini-score-value">{(ticker.scores.technical * 100).toFixed(0)}</span>
                    </div>
                    <div className="mini-score">
                      <span className="mini-score-label">M</span>
                      <span className="mini-score-value">{(ticker.scores.ml * 100).toFixed(0)}</span>
                    </div>
                    <div className="mini-score">
                      <span className="mini-score-label">N</span>
                      <span className="mini-score-value">{(ticker.scores.neural * 100).toFixed(0)}</span>
                    </div>
                  </div>
                </td>
                <td className="plan-cell">
                  <div className="mini-plan">
                    <span className="plan-entry">${ticker.trade_plan.entry.toFixed(2)}</span>
                    <span className="plan-divider">→</span>
                    <span className="plan-tp">${ticker.trade_plan.take_profit.toFixed(2)}</span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {sortedTickers.length === 0 && (
        <div className="no-data">
          <p>No tickers match the current filter</p>
        </div>
      )}
    </div>
  );
};

export default MultiTickerGrid;
