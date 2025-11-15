import React, { useState, useEffect } from 'react';
import { tradingAPI, systemAPI, dataAPI } from '../services/api';
import wsService from '../services/websocket';
import MarketBlotter from './MarketBlotter';
import AgentInsights from './AgentInsights';
import PortfolioChart from './PortfolioChart';
import PositionsGrid from './PositionsGrid';
import OrdersGrid from './OrdersGrid';
import NewsTicker from './NewsTicker';
import SystemMetrics from './SystemMetrics';
import TradingPanel from './TradingPanel';
import DataSourceIndicator from './DataSourceIndicator';
import SettingsModal from './SettingsModal';
import WatchlistPanel from './WatchlistPanel';
import PerformanceAnalytics from './PerformanceAnalytics';
import AgentLog from './AgentLog';
import MainChart from './MainChart/MainChart';
import BacktestingPanel from './BacktestingPanel';

function Dashboard({ connected }) {
  const [portfolio, setPortfolio] = useState(null);
  const [positions, setPositions] = useState([]);
  const [orders, setOrders] = useState([]);
  const [marketData, setMarketData] = useState({});
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showSettings, setShowSettings] = useState(false);
  const [selectedStock, setSelectedStock] = useState(null);

  useEffect(() => {
    loadDashboardData();
    const interval = setInterval(loadDashboardData, 10000); // Refresh every 10s
    
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const unsubscribeMarket = wsService.subscribe('market_update', (data) => {
      setMarketData(data.data);
    });

    const unsubscribeAI = wsService.subscribe('ai_analysis', (data) => {
      console.log('AI Analysis received:', data.data);
    });

    const unsubscribeAutoTrade = wsService.subscribe('auto_trade', (data) => {
      console.log('Auto-trade executed:', data.data);
      loadDashboardData();
    });

    return () => {
      unsubscribeMarket();
      unsubscribeAI();
      unsubscribeAutoTrade();
    };
  }, []);

  const loadDashboardData = async () => {
    try {
      const [portfolioRes, positionsRes, ordersRes, metricsRes, snapshotRes] = await Promise.all([
        tradingAPI.getPortfolio(),
        tradingAPI.getPositions(),
        tradingAPI.getOrders(50),
        systemAPI.getMetrics(),
        dataAPI.getSnapshot()
      ]);

      setPortfolio(portfolioRes.data);
      setPositions(positionsRes.data);
      setOrders(ordersRes.data);
      setMetrics(metricsRes.data);
      setMarketData(snapshotRes.data);
      setLoading(false);
    } catch (err) {
      console.error('Error loading dashboard data:', err);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="dashboard">
        <div className="loading">
          <div className="spinner"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard fade-in">
      {/* Header */}
      <div className="header">
        <div className="header-left">
          <h1>🤖 AI Trading System</h1>
          <p>Multi-Agent Autonomous Trading Platform</p>
        </div>
        
        <div className="header-stats">
          <div className="stat">
            <div className="stat-label">Portfolio Value</div>
            <div className="stat-value">
              ${portfolio?.total_value?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}
            </div>
          </div>
          <div className="stat">
            <div className="stat-label">Total P&L</div>
            <div className={`stat-value ${portfolio?.total_pnl >= 0 ? 'positive' : 'negative'}`}>
              {portfolio?.total_pnl >= 0 ? '+' : ''}
              ${portfolio?.total_pnl?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}
            </div>
          </div>
          <div className="stat">
            <div className="stat-label">Daily P&L</div>
            <div className={`stat-value ${portfolio?.daily_pnl >= 0 ? 'positive' : 'negative'}`}>
              {portfolio?.daily_pnl >= 0 ? '+' : ''}
              ${portfolio?.daily_pnl?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button className="settings-btn" onClick={() => setShowSettings(true)} title="Settings">
            ⚙️
          </button>
          <DataSourceIndicator />
          <div className="status-indicator">
            <div className="status-dot"></div>
            <span>{connected ? 'Live' : 'Offline'}</span>
          </div>
        </div>
      </div>

      <SettingsModal isOpen={showSettings} onClose={() => setShowSettings(false)} />

      {/* Main Grid */}
      <div className="grid">
        {/* Live News Ticker */}
        <div className="col-span-12">
          <NewsTicker />
        </div>

        {/* TradingView-Style Chart - Full width, primary feature */}
        <div className="col-span-12" style={{ minHeight: '650px' }}>
          <MainChart initialSymbol={selectedStock || 'AAPL'} />
        </div>

        {/* Side Panel - 4 columns */}
        <div className="col-span-4 side-panel">
          <div className="side-panel-content">
            <SystemMetrics metrics={metrics} />
            <TradingPanel onTrade={loadDashboardData} />
            <AgentInsights />
          </div>
        </div>

        {/* Market Blotter - Now 8 columns */}
        <div className="col-span-8">
          <MarketBlotter 
            marketData={marketData} 
            onStockClick={(symbol) => setSelectedStock(symbol)}
          />
        </div>

        {/* Watchlist & Alerts */}
        <div className="col-span-4">
          <WatchlistPanel />
        </div>

        {/* Performance Analytics */}
        <div className="col-span-6">
          <PerformanceAnalytics />
        </div>

        {/* Live Agent Log */}
        <div className="col-span-6">
          <AgentLog />
        </div>

        {/* Portfolio Chart */}
        <div className="col-span-12">
          <PortfolioChart portfolio={portfolio} />
        </div>

        {/* Backtesting Panel */}
        <div className="col-span-12">
          <BacktestingPanel />
        </div>

        {/* Positions Grid */}
        <div className="col-span-6">
          <PositionsGrid positions={positions} />
        </div>

        {/* Orders Grid */}
        <div className="col-span-6">
          <OrdersGrid orders={orders} onRefresh={loadDashboardData} />
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
