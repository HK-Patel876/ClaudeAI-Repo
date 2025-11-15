/**
 * Enhanced AI Trading Dashboard
 * Complete trading platform with backtesting, portfolio management, and AI signals
 */
import React, { useState, useEffect } from 'react';
import {
  Activity, TrendingUp, TrendingDown, DollarSign, Target, BarChart3,
  Settings, RefreshCw, Download, Upload, Play, Pause, ChevronDown,
  Bell, Moon, Sun, Zap, AlertCircle, Check, X, Eye, EyeOff,
  Filter, Search, ArrowUpDown, Calendar, Clock, Wallet, PieChart
} from 'lucide-react';
import LiveSignalsPanel from './LiveSignalsPanel';
import MultiTickerGrid from './MultiTickerGrid';
import BacktestingPanel from './BacktestingPanel';
import PortfolioChart from './PortfolioChart';
import MainChart from './MainChart/MainChart';
import TradingPanel from './TradingPanel';
import WatchlistManager from './WatchlistManager';
import AutoTradingSettings from './AutoTradingSettings';
import OptionsAnalytics from './OptionsAnalytics';
import aiSignalsService from '../services/aiSignals';
import { tradingAPI, systemAPI } from '../services/api';
import soundService from '../services/soundService';
import './EnhancedDashboard.css';

const EnhancedDashboard = () => {
  // State Management
  const [performance, setPerformance] = useState(null);
  const [topOpportunities, setTopOpportunities] = useState([]);
  const [portfolio, setPortfolio] = useState(null);
  const [positions, setPositions] = useState([]);
  const [orders, setOrders] = useState([]);
  const [selectedSymbol, setSelectedSymbol] = useState('AAPL');
  const [activeView, setActiveView] = useState('signals'); // signals, grid, backtest, portfolio, trading
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [darkMode, setDarkMode] = useState(true);
  const [showNotifications, setShowNotifications] = useState(true);
  const [filterMinConfidence, setFilterMinConfidence] = useState(0.7);
  const [showFilters, setShowFilters] = useState(false);
  const [isLive, setIsLive] = useState(true);

  // Fetch all dashboard data
  const loadDashboardData = async () => {
    try {
      const [perfRes, oppRes, portfolioRes, positionsRes, ordersRes] = await Promise.all([
        aiSignalsService.getPerformance(),
        aiSignalsService.getTopOpportunities(10, filterMinConfidence),
        tradingAPI.getPortfolio(),
        tradingAPI.getPositions(),
        tradingAPI.getOrders(20)
      ]);

      if (perfRes?.success) setPerformance(perfRes.performance);
      if (oppRes?.success) setTopOpportunities(oppRes.opportunities);
      if (portfolioRes?.data) setPortfolio(portfolioRes.data);
      if (positionsRes?.data) setPositions(positionsRes.data);
      if (ordersRes?.data) setOrders(ordersRes.data);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    }
  };

  // Auto-refresh data
  useEffect(() => {
    loadDashboardData();

    if (autoRefresh) {
      const interval = setInterval(loadDashboardData, 5000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, filterMinConfidence]);

  const handleSymbolClick = (symbol) => {
    setSelectedSymbol(symbol);
    soundService.playAlert();
  };

  const handleViewChange = (view) => {
    setActiveView(view);
    soundService.playTone(600, 100, 'sine');
  };

  const toggleAutoRefresh = () => {
    setAutoRefresh(!autoRefresh);
    soundService.playTone(800, 100, 'sine');
  };

  const exportData = () => {
    const data = {
      performance,
      portfolio,
      positions,
      timestamp: new Date().toISOString()
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `trading-data-${Date.now()}.json`;
    a.click();
    soundService.playTradeExecuted();
  };

  return (
    <div className={`enhanced-dashboard ${darkMode ? 'dark' : 'light'} animate-fade-in`}>
      {/* Main Header with Controls */}
      <div className="dashboard-header animate-slide-in-down">
        <div className="header-left">
          <h1 className="dashboard-title">
            <Activity className="title-icon animate-pulse" size={32} />
            <span className="title-gradient">AI Trading</span> Command Center
          </h1>

          <div className="quick-stats">
            <div className="status-badge">
              <div className={`status-dot ${isLive ? 'live' : 'paused'} animate-pulse`}></div>
              <span>{isLive ? 'Live' : 'Paused'}</span>
            </div>

            {portfolio && (
              <>
                <div className="quick-stat">
                  <Wallet size={16} />
                  <span className="stat-value">${portfolio.total_value?.toLocaleString() || '0'}</span>
                </div>
                <div className={`quick-stat ${portfolio.daily_pnl >= 0 ? 'positive' : 'negative'}`}>
                  {portfolio.daily_pnl >= 0 ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                  <span className="stat-value">
                    {portfolio.daily_pnl >= 0 ? '+' : ''}${portfolio.daily_pnl?.toFixed(2) || '0'}
                  </span>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Performance Metrics */}
        {performance && (
          <div className="performance-metrics animate-fade-in stagger-item">
            <div className="metric-card hover-lift animate-scale-in">
              <div className="metric-label">Accuracy</div>
              <div className="metric-value accuracy">
                {(performance.overall_accuracy * 100).toFixed(1)}%
              </div>
              <div className="metric-trend">↑ 2.3%</div>
            </div>
            <div className="metric-card hover-lift animate-scale-in animate-delay-1">
              <div className="metric-label">Win Rate</div>
              <div className="metric-value win-rate">
                {(performance.win_rate * 100).toFixed(1)}%
              </div>
              <div className="metric-trend">↑ 1.8%</div>
            </div>
            <div className="metric-card hover-lift animate-scale-in animate-delay-2">
              <div className="metric-label">Avg Return</div>
              <div className="metric-value return">
                +{performance.average_return_pct.toFixed(2)}%
              </div>
              <div className="metric-trend">↑ 0.5%</div>
            </div>
            <div className="metric-card hover-lift animate-scale-in animate-delay-3">
              <div className="metric-label">Sharpe</div>
              <div className="metric-value sharpe">
                {performance.sharpe_ratio.toFixed(2)}
              </div>
              <div className="metric-trend">→ 0.0%</div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="header-actions">
          <button
            onClick={toggleAutoRefresh}
            className={`action-btn ${autoRefresh ? 'active' : ''} hover-lift`}
            title={autoRefresh ? 'Pause Auto-Refresh' : 'Enable Auto-Refresh'}
          >
            {autoRefresh ? <Pause size={18} /> : <Play size={18} />}
          </button>

          <button
            onClick={loadDashboardData}
            className="action-btn hover-lift"
            title="Refresh Data"
          >
            <RefreshCw size={18} className="refresh-icon" />
          </button>

          <button
            onClick={exportData}
            className="action-btn hover-lift"
            title="Export Data"
          >
            <Download size={18} />
          </button>

          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`action-btn ${showFilters ? 'active' : ''} hover-lift`}
            title="Filters"
          >
            <Filter size={18} />
          </button>

          <button
            onClick={() => {
              const enabled = soundService.toggle();
              soundService.playTone(enabled ? 800 : 400, 100, 'sine');
            }}
            className={`action-btn ${soundService.isEnabled() ? 'active' : ''} hover-lift`}
            title="Toggle Sound"
          >
            <Bell size={18} />
          </button>

          <button
            onClick={() => {
              setDarkMode(!darkMode);
              soundService.playTone(600, 100, 'sine');
            }}
            className="action-btn hover-lift"
            title="Toggle Theme"
          >
            {darkMode ? <Sun size={18} /> : <Moon size={18} />}
          </button>
        </div>
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <div className="filters-panel animate-slide-down">
          <div className="filter-group">
            <label>Min Confidence:</label>
            <input
              type="range"
              min="0.5"
              max="0.95"
              step="0.05"
              value={filterMinConfidence}
              onChange={(e) => setFilterMinConfidence(parseFloat(e.target.value))}
            />
            <span>{(filterMinConfidence * 100).toFixed(0)}%</span>
          </div>

          <div className="filter-group">
            <label>Signal Types:</label>
            <div className="filter-chips">
              <button className="filter-chip active">STRONG_BUY</button>
              <button className="filter-chip active">BUY</button>
              <button className="filter-chip">HOLD</button>
              <button className="filter-chip active">SELL</button>
              <button className="filter-chip active">STRONG_SELL</button>
            </div>
          </div>
        </div>
      )}

      {/* Top Opportunities Banner */}
      {topOpportunities.length > 0 && (
        <div className="opportunities-banner animate-fade-in-up">
          <div className="banner-header">
            <Zap className="banner-icon animate-pulse" size={20} />
            <span className="banner-title">Top AI Opportunities</span>
            <span className="banner-count">{topOpportunities.length} signals</span>
          </div>
          <div className="opportunities-scroll">
            {topOpportunities.map((opp, index) => (
              <div
                key={`${opp.symbol}-${index}`}
                className="opportunity-chip hover-lift animate-scale-in"
                style={{ animationDelay: `${index * 0.05}s` }}
                onClick={() => handleSymbolClick(opp.symbol)}
              >
                <span className="opp-symbol">{opp.symbol}</span>
                <span className={`opp-signal ${opp.signal.includes('BUY') ? 'buy' : 'sell'}`}>
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

      {/* Navigation Tabs */}
      <div className="view-tabs animate-fade-in">
        <button
          className={`tab-btn ${activeView === 'signals' ? 'active' : ''} hover-lift`}
          onClick={() => handleViewChange('signals')}
        >
          <Zap size={18} />
          <span>Live Signals</span>
          {topOpportunities.length > 0 && (
            <span className="tab-badge">{topOpportunities.length}</span>
          )}
        </button>

        <button
          className={`tab-btn ${activeView === 'grid' ? 'active' : ''} hover-lift`}
          onClick={() => handleViewChange('grid')}
        >
          <BarChart3 size={18} />
          <span>Market Grid</span>
        </button>

        <button
          className={`tab-btn ${activeView === 'chart' ? 'active' : ''} hover-lift`}
          onClick={() => handleViewChange('chart')}
        >
          <TrendingUp size={18} />
          <span>Chart</span>
        </button>

        <button
          className={`tab-btn ${activeView === 'trading' ? 'active' : ''} hover-lift`}
          onClick={() => handleViewChange('trading')}
        >
          <Activity size={18} />
          <span>Trading</span>
        </button>

        <button
          className={`tab-btn ${activeView === 'portfolio' ? 'active' : ''} hover-lift`}
          onClick={() => handleViewChange('portfolio')}
        >
          <PieChart size={18} />
          <span>Portfolio</span>
          {positions.length > 0 && (
            <span className="tab-badge">{positions.length}</span>
          )}
        </button>

        <button
          className={`tab-btn ${activeView === 'backtest' ? 'active' : ''} hover-lift`}
          onClick={() => handleViewChange('backtest')}
        >
          <Clock size={18} />
          <span>Backtesting</span>
        </button>

        <button
          className={`tab-btn ${activeView === 'watchlist' ? 'active' : ''} hover-lift`}
          onClick={() => handleViewChange('watchlist')}
        >
          <Target size={18} />
          <span>Watchlist</span>
        </button>

        <button
          className={`tab-btn ${activeView === 'autotrading' ? 'active' : ''} hover-lift`}
          onClick={() => handleViewChange('autotrading')}
        >
          <Zap size={18} />
          <span>Auto-Trading</span>
        </button>

        <button
          className={`tab-btn ${activeView === 'options' ? 'active' : ''} hover-lift`}
          onClick={() => handleViewChange('options')}
        >
          <DollarSign size={18} />
          <span>Options</span>
        </button>
      </div>

      {/* Main Content Area */}
      <div className="dashboard-main-content">
        {activeView === 'signals' && (
          <div className="content-view animate-fade-in">
            <LiveSignalsPanel />
          </div>
        )}

        {activeView === 'grid' && (
          <div className="content-view animate-fade-in">
            <MultiTickerGrid onSymbolClick={handleSymbolClick} />
          </div>
        )}

        {activeView === 'chart' && (
          <div className="content-view animate-fade-in">
            <div className="chart-container">
              <MainChart initialSymbol={selectedSymbol} />
            </div>
          </div>
        )}

        {activeView === 'trading' && (
          <div className="content-view animate-fade-in">
            <div className="trading-grid">
              <div className="trading-section">
                <TradingPanel onTrade={loadDashboardData} />
              </div>
              <div className="trading-section">
                <div className="section-header">
                  <h3>Recent Orders</h3>
                  <button className="btn-sm hover-lift">View All</button>
                </div>
                <div className="orders-list">
                  {orders.slice(0, 5).map((order, idx) => (
                    <div key={order.id || idx} className="order-item hover-lift">
                      <div className="order-symbol">{order.symbol}</div>
                      <div className={`order-side ${order.side}`}>{order.side}</div>
                      <div className="order-qty">{order.quantity} shares</div>
                      <div className="order-price">${order.price?.toFixed(2)}</div>
                      <div className={`order-status ${order.status}`}>{order.status}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeView === 'portfolio' && (
          <div className="content-view animate-fade-in">
            <div className="portfolio-grid">
              <div className="portfolio-section">
                <PortfolioChart portfolio={portfolio} />
              </div>
              <div className="portfolio-section">
                <div className="section-header">
                  <h3>Active Positions</h3>
                  <span className="position-count">{positions.length}</span>
                </div>
                <div className="positions-grid">
                  {positions.map((pos, idx) => (
                    <div key={pos.symbol || idx} className="position-card hover-lift">
                      <div className="position-header">
                        <span className="position-symbol">{pos.symbol}</span>
                        <span className={`position-pnl ${pos.unrealized_pnl >= 0 ? 'positive' : 'negative'}`}>
                          {pos.unrealized_pnl >= 0 ? '+' : ''}${pos.unrealized_pnl?.toFixed(2)}
                        </span>
                      </div>
                      <div className="position-details">
                        <div className="detail-item">
                          <span className="detail-label">Qty:</span>
                          <span className="detail-value">{pos.quantity}</span>
                        </div>
                        <div className="detail-item">
                          <span className="detail-label">Avg:</span>
                          <span className="detail-value">${pos.avg_price?.toFixed(2)}</span>
                        </div>
                        <div className="detail-item">
                          <span className="detail-label">Current:</span>
                          <span className="detail-value">${pos.current_price?.toFixed(2)}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeView === 'backtest' && (
          <div className="content-view animate-fade-in">
            <BacktestingPanel />
          </div>
        )}

        {activeView === 'watchlist' && (
          <div className="content-view animate-fade-in">
            <WatchlistManager onSymbolSelect={handleSymbolClick} />
          </div>
        )}

        {activeView === 'autotrading' && (
          <div className="content-view animate-fade-in">
            <AutoTradingSettings onSettingsChange={loadDashboardData} />
          </div>
        )}

        {activeView === 'options' && (
          <div className="content-view animate-fade-in">
            <OptionsAnalytics defaultSymbol={selectedSymbol} />
          </div>
        )}
      </div>

      {/* Footer with System Info */}
      <div className="dashboard-footer animate-fade-in">
        <div className="footer-left">
          <div className="footer-stat">
            <span className="footer-label">Analysis Speed:</span>
            <span className="footer-value">Sub-second</span>
          </div>
          <div className="footer-stat">
            <span className="footer-label">AI Models:</span>
            <span className="footer-value">5 Active</span>
          </div>
          <div className="footer-stat">
            <span className="footer-label">Indicators:</span>
            <span className="footer-value">75+</span>
          </div>
          <div className="footer-stat">
            <span className="footer-label">Assets:</span>
            <span className="footer-value">Multi-class</span>
          </div>
        </div>
        <div className="footer-center">
          Powered by Advanced AI & Machine Learning
        </div>
        <div className="footer-right">
          <button className="footer-link hover-brightness">Documentation</button>
          <button className="footer-link hover-brightness">API</button>
          <button className="footer-link hover-brightness">Support</button>
        </div>
      </div>
    </div>
  );
};

export default EnhancedDashboard;
