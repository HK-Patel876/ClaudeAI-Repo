/**
 * Live Signals Panel - Real-time AI Trading Signals
 * Displays live buy/sell signals with confidence scores
 */
import React, { useState, useEffect, useCallback } from 'react';
import aiSignalsService from '../services/aiSignals';
import './LiveSignalsPanel.css';

const LiveSignalsPanel = () => {
  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // all, buy, sell, strong
  const [sortBy, setSortBy] = useState('confidence'); // confidence, change, symbol

  // Fetch live signals
  const fetchSignals = useCallback(async () => {
    try {
      const data = await aiSignalsService.getLiveSignals();
      if (data.success) {
        setSignals(data.signals);
      }
      setLoading(false);
    } catch (error) {
      console.error('Error fetching signals:', error);
      setLoading(false);
    }
  }, []);

  // Auto-refresh every 2 seconds
  useEffect(() => {
    fetchSignals();
    const interval = setInterval(fetchSignals, 2000);
    return () => clearInterval(interval);
  }, [fetchSignals]);

  // Filter signals
  const filteredSignals = signals.filter(signal => {
    if (filter === 'all') return true;
    if (filter === 'buy') return signal.signal.includes('BUY');
    if (filter === 'sell') return signal.signal.includes('SELL');
    if (filter === 'strong') return signal.signal.includes('STRONG');
    return true;
  });

  // Sort signals
  const sortedSignals = [...filteredSignals].sort((a, b) => {
    if (sortBy === 'confidence') return b.confidence - a.confidence;
    if (sortBy === 'change') return Math.abs(b.predicted_change_pct) - Math.abs(a.predicted_change_pct);
    if (sortBy === 'symbol') return a.symbol.localeCompare(b.symbol);
    return 0;
  });

  const getSignalColor = (signal) => {
    if (signal === 'STRONG_BUY') return '#00ff88';
    if (signal === 'BUY') return '#4ade80';
    if (signal === 'NEUTRAL') return '#94a3b8';
    if (signal === 'SELL') return '#f87171';
    if (signal === 'STRONG_SELL') return '#ff3366';
    return '#94a3b8';
  };

  const getSignalIcon = (signal) => {
    if (signal.includes('BUY')) return '▲';
    if (signal.includes('SELL')) return '▼';
    return '●';
  };

  const getAssetTypeColor = (assetType) => {
    const colors = {
      'stock': '#3b82f6',
      'crypto': '#f59e0b',
      'index': '#8b5cf6',
      'forex': '#10b981'
    };
    return colors[assetType] || '#6b7280';
  };

  if (loading) {
    return (
      <div className="live-signals-panel">
        <div className="panel-header">
          <h2>Live AI Signals</h2>
        </div>
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading signals...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="live-signals-panel">
      <div className="panel-header">
        <div className="header-left">
          <h2>Live AI Signals</h2>
          <span className="signal-count">{sortedSignals.length} Active</span>
        </div>
        <div className="header-controls">
          <select value={filter} onChange={(e) => setFilter(e.target.value)} className="filter-select">
            <option value="all">All Signals</option>
            <option value="buy">Buy Signals</option>
            <option value="sell">Sell Signals</option>
            <option value="strong">Strong Signals</option>
          </select>
          <select value={sortBy} onChange={(e) => setSortBy(e.target.value)} className="sort-select">
            <option value="confidence">Sort by Confidence</option>
            <option value="change">Sort by Change %</option>
            <option value="symbol">Sort by Symbol</option>
          </select>
        </div>
      </div>

      <div className="signals-grid">
        {sortedSignals.map((signal, index) => (
          <div
            key={`${signal.symbol}-${index}`}
            className="signal-card"
            style={{ '--signal-color': getSignalColor(signal.signal) }}
          >
            <div className="signal-header">
              <div className="symbol-info">
                <span className="symbol-text">{signal.symbol}</span>
                <span
                  className="asset-badge"
                  style={{ backgroundColor: getAssetTypeColor(signal.asset_type) }}
                >
                  {signal.asset_type}
                </span>
              </div>
              <div className="signal-indicator" style={{ color: getSignalColor(signal.signal) }}>
                <span className="signal-icon">{getSignalIcon(signal.signal)}</span>
                <span className="signal-label">{signal.signal.replace('_', ' ')}</span>
              </div>
            </div>

            <div className="signal-metrics">
              <div className="metric">
                <span className="metric-label">Price</span>
                <span className="metric-value">${signal.current_price.toFixed(2)}</span>
              </div>
              <div className="metric">
                <span className="metric-label">Predicted</span>
                <span
                  className="metric-value"
                  style={{ color: signal.predicted_change_pct > 0 ? '#4ade80' : '#f87171' }}
                >
                  {signal.predicted_change_pct > 0 ? '+' : ''}
                  {signal.predicted_change_pct.toFixed(2)}%
                </span>
              </div>
            </div>

            <div className="confidence-bar-container">
              <div className="confidence-label">
                <span>Confidence</span>
                <span className="confidence-value">{(signal.confidence * 100).toFixed(0)}%</span>
              </div>
              <div className="confidence-bar">
                <div
                  className="confidence-fill"
                  style={{
                    width: `${signal.confidence * 100}%`,
                    backgroundColor: getSignalColor(signal.signal)
                  }}
                />
              </div>
            </div>

            <div className="score-bars">
              <div className="score-bar">
                <span className="score-label">Tech</span>
                <div className="score-progress">
                  <div
                    className="score-fill"
                    style={{ width: `${Math.abs(signal.scores.technical) * 100}%` }}
                  />
                </div>
                <span className="score-value">{(signal.scores.technical * 100).toFixed(0)}</span>
              </div>
              <div className="score-bar">
                <span className="score-label">ML</span>
                <div className="score-progress">
                  <div
                    className="score-fill"
                    style={{ width: `${Math.abs(signal.scores.ml) * 100}%` }}
                  />
                </div>
                <span className="score-value">{(signal.scores.ml * 100).toFixed(0)}</span>
              </div>
              <div className="score-bar">
                <span className="score-label">Neural</span>
                <div className="score-progress">
                  <div
                    className="score-fill"
                    style={{ width: `${Math.abs(signal.scores.neural) * 100}%` }}
                  />
                </div>
                <span className="score-value">{(signal.scores.neural * 100).toFixed(0)}</span>
              </div>
            </div>

            <div className="trade-plan">
              <div className="plan-item">
                <span className="plan-label">Entry:</span>
                <span className="plan-value">${signal.trade_plan.entry.toFixed(2)}</span>
              </div>
              <div className="plan-item">
                <span className="plan-label">SL:</span>
                <span className="plan-value stop-loss">${signal.trade_plan.stop_loss.toFixed(2)}</span>
              </div>
              <div className="plan-item">
                <span className="plan-label">TP:</span>
                <span className="plan-value take-profit">${signal.trade_plan.take_profit.toFixed(2)}</span>
              </div>
              <div className="plan-item">
                <span className="plan-label">R:R:</span>
                <span className="plan-value">{signal.trade_plan.risk_reward_ratio.toFixed(2)}</span>
              </div>
            </div>

            <div className="signal-footer">
              <span className="signal-age">
                {signal.age_seconds < 60
                  ? `${Math.floor(signal.age_seconds)}s ago`
                  : `${Math.floor(signal.age_seconds / 60)}m ago`}
              </span>
              <span className="risk-badge" style={{
                backgroundColor: signal.scores.risk < 0.3 ? '#4ade80' :
                  signal.scores.risk < 0.6 ? '#f59e0b' : '#f87171'
              }}>
                Risk: {(signal.scores.risk * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        ))}
      </div>

      {sortedSignals.length === 0 && (
        <div className="no-signals">
          <p>No signals match the current filter</p>
        </div>
      )}
    </div>
  );
};

export default LiveSignalsPanel;
