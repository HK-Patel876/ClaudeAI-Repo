/**
 * New Modern Dashboard - TradingView Style
 * Complete redesign with AI-powered real-time signals
 */
import React, { useState, useEffect } from 'react';
import LiveSignalsPanel from './LiveSignalsPanel';
import MultiTickerGrid from './MultiTickerGrid';
import aiSignalsService from '../services/aiSignals';
import './NewDashboard.css';

const NewDashboard = () => {
  const [performance, setPerformance] = useState(null);
  const [topOpportunities, setTopOpportunities] = useState([]);
  const [selectedSymbol, setSelectedSymbol] = useState(null);
  const [view, setView] = useState('signals'); // signals, grid, both

  // Fetch performance metrics
  useEffect(() => {
    const fetchPerformance = async () => {
      const data = await aiSignalsService.getPerformance();
      if (data && data.success) {
        setPerformance(data.performance);
      }
    };

    fetchPerformance();
    const interval = setInterval(fetchPerformance, 30000); // Every 30s
    return () => clearInterval(interval);
  }, []);

  // Fetch top opportunities
  useEffect(() => {
    const fetchOpportunities = async () => {
      const data = await aiSignalsService.getTopOpportunities(5, 0.7);
      if (data && data.success) {
        setTopOpportunities(data.opportunities);
      }
    };

    fetchOpportunities();
    const interval = setInterval(fetchOpportunities, 5000); // Every 5s
    return () => clearInterval(interval);
  }, []);

  const handleSymbolClick = (symbol) => {
    setSelectedSymbol(symbol);
    // In a full implementation, this would open a detailed view or chart
    console.log('Selected symbol:', symbol);
  };

  return (
    <div className="new-dashboard">
      {/* Top Bar with Performance Metrics */}
      <div className="dashboard-topbar">
        <div className="topbar-left">
          <h1 className="dashboard-title">
            <span className="title-gradient">AI Trading</span> Command Center
          </h1>
          <div className="status-indicator">
            <span className="status-dot"></span>
            <span className="status-text">Live</span>
          </div>
        </div>

        {performance && (
          <div className="performance-stats">
            <div className="stat-card">
              <span className="stat-label">Accuracy</span>
              <span className="stat-value accuracy">
                {(performance.overall_accuracy * 100).toFixed(1)}%
              </span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Win Rate</span>
              <span className="stat-value win-rate">
                {(performance.win_rate * 100).toFixed(1)}%
              </span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Avg Return</span>
              <span className="stat-value return">
                +{performance.average_return_pct.toFixed(2)}%
              </span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Sharpe</span>
              <span className="stat-value sharpe">
                {performance.sharpe_ratio.toFixed(2)}
              </span>
            </div>
          </div>
        )}

        <div className="view-controls">
          <button
            className={`view-btn ${view === 'signals' ? 'active' : ''}`}
            onClick={() => setView('signals')}
            title="Signal Cards View"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <rect x="1" y="1" width="6" height="6" rx="1"/>
              <rect x="9" y="1" width="6" height="6" rx="1"/>
              <rect x="1" y="9" width="6" height="6" rx="1"/>
              <rect x="9" y="9" width="6" height="6" rx="1"/>
            </svg>
          </button>
          <button
            className={`view-btn ${view === 'grid' ? 'active' : ''}`}
            onClick={() => setView('grid')}
            title="Table Grid View"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <rect x="1" y="2" width="14" height="2" rx="0.5"/>
              <rect x="1" y="6" width="14" height="2" rx="0.5"/>
              <rect x="1" y="10" width="14" height="2" rx="0.5"/>
            </svg>
          </button>
          <button
            className={`view-btn ${view === 'both' ? 'active' : ''}`}
            onClick={() => setView('both')}
            title="Split View"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <rect x="1" y="1" width="6" height="14" rx="1"/>
              <rect x="9" y="1" width="6" height="14" rx="1"/>
            </svg>
          </button>
        </div>
      </div>

      {/* Top Opportunities Banner */}
      {topOpportunities.length > 0 && (
        <div className="opportunities-banner">
          <div className="banner-header">
            <span className="banner-icon">⚡</span>
            <span className="banner-title">Top Opportunities</span>
          </div>
          <div className="opportunities-scroll">
            {topOpportunities.map((opp, index) => (
              <div
                key={`${opp.symbol}-${index}`}
                className="opportunity-chip"
                onClick={() => handleSymbolClick(opp.symbol)}
              >
                <span className="opp-symbol">{opp.symbol}</span>
                <span className="opp-signal" style={{
                  color: opp.signal.includes('BUY') ? '#00ff88' : '#ff3366'
                }}>
                  {opp.signal.replace('_', ' ')}
                </span>
                <span className="opp-confidence">
                  {(opp.confidence * 100).toFixed(0)}%
                </span>
                <span className={`opp-change ${opp.predicted_change_pct >= 0 ? 'positive' : 'negative'}`}>
                  {opp.predicted_change_pct >= 0 ? '+' : ''}
                  {opp.predicted_change_pct.toFixed(1)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className={`dashboard-content view-${view}`}>
        {(view === 'signals' || view === 'both') && (
          <div className="content-panel signals-panel">
            <LiveSignalsPanel />
          </div>
        )}

        {(view === 'grid' || view === 'both') && (
          <div className="content-panel grid-panel">
            <MultiTickerGrid onSymbolClick={handleSymbolClick} />
          </div>
        )}
      </div>

      {/* Footer Stats */}
      <div className="dashboard-footer">
        <div className="footer-stats">
          <span className="footer-stat">
            <span className="footer-label">Real-time Analysis</span>
            <span className="footer-value">Sub-second</span>
          </span>
          <span className="footer-divider">•</span>
          <span className="footer-stat">
            <span className="footer-label">AI Models</span>
            <span className="footer-value">5 Active</span>
          </span>
          <span className="footer-divider">•</span>
          <span className="footer-stat">
            <span className="footer-label">Indicators</span>
            <span className="footer-value">40+</span>
          </span>
          <span className="footer-divider">•</span>
          <span className="footer-stat">
            <span className="footer-label">Assets</span>
            <span className="footer-value">Multi-class</span>
          </span>
        </div>
        <div className="footer-branding">
          Powered by Advanced AI & Machine Learning
        </div>
      </div>
    </div>
  );
};

export default NewDashboard;
