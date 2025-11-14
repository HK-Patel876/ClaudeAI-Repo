import React, { useState, useEffect } from 'react';
import api from '../services/api';

function PerformanceAnalytics() {
  const [performance, setPerformance] = useState(null);
  const [loading, setLoading] = useState(true);
  const [timeframe, setTimeframe] = useState(30);

  useEffect(() => {
    loadPerformance();
  }, [timeframe]);

  const loadPerformance = async () => {
    setLoading(true);
    try {
      const response = await api.get(`/performance?days=${timeframe}`);
      setPerformance(response.data.data);
    } catch (err) {
      console.error('Error loading performance:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">📈 Performance Analytics</h3>
        </div>
        <div className="loading">Loading...</div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">📈 Performance Analytics</h3>
        <div className="timeframe-selector">
          <button
            className={`btn btn-sm ${timeframe === 7 ? 'active' : ''}`}
            onClick={() => setTimeframe(7)}
          >
            7D
          </button>
          <button
            className={`btn btn-sm ${timeframe === 30 ? 'active' : ''}`}
            onClick={() => setTimeframe(30)}
          >
            30D
          </button>
          <button
            className={`btn btn-sm ${timeframe === 90 ? 'active' : ''}`}
            onClick={() => setTimeframe(90)}
          >
            90D
          </button>
        </div>
      </div>

      <div className="performance-content">
        {performance && performance.total_trades > 0 ? (
          <>
            <div className="performance-metrics">
              <div className="metric-card">
                <div className="metric-label">Total Trades</div>
                <div className="metric-value">{performance.total_trades}</div>
              </div>
              <div className="metric-card">
                <div className="metric-label">Win Rate</div>
                <div className="metric-value">{performance.win_rate}%</div>
              </div>
              <div className="metric-card">
                <div className="metric-label">Total P&L</div>
                <div className={`metric-value ${performance.total_pnl >= 0 ? 'positive' : 'negative'}`}>
                  ${performance.total_pnl.toLocaleString()}
                </div>
              </div>
              <div className="metric-card">
                <div className="metric-label">Sharpe Ratio</div>
                <div className="metric-value">{performance.sharpe_ratio}</div>
              </div>
              <div className="metric-card">
                <div className="metric-label">Max Drawdown</div>
                <div className="metric-value negative">{performance.max_drawdown}%</div>
              </div>
            </div>

            <div className="cumulative-chart">
              <h4>Cumulative Returns</h4>
              <div className="simple-chart">
                {performance.cumulative_returns && performance.cumulative_returns.length > 0 ? (
                  <svg width="100%" height="200" viewBox="0 0 600 200">
                    {performance.cumulative_returns.map((point, i) => {
                      if (i === 0) return null;
                      const prevPoint = performance.cumulative_returns[i - 1];
                      const x1 = (i - 1) * (600 / performance.cumulative_returns.length);
                      const x2 = i * (600 / performance.cumulative_returns.length);
                      const maxVal = Math.max(...performance.cumulative_returns.map(p => Math.abs(p.value)));
                      const y1 = 100 - (prevPoint.value / (maxVal || 1)) * 80;
                      const y2 = 100 - (point.value / (maxVal || 1)) * 80;
                      return (
                        <line
                          key={i}
                          x1={x1}
                          y1={y1}
                          x2={x2}
                          y2={y2}
                          stroke="#60a5fa"
                          strokeWidth="2"
                        />
                      );
                    })}
                    <line x1="0" y1="100" x2="600" y2="100" stroke="#64748b" strokeWidth="1" strokeDasharray="5,5" />
                  </svg>
                ) : (
                  <p className="empty-message">No returns data available</p>
                )}
              </div>
            </div>
          </>
        ) : (
          <div className="empty-state">
            <p>No trading history available for the selected period</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default PerformanceAnalytics;
