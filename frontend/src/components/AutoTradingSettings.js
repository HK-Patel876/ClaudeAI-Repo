import React, { useState, useEffect } from 'react';
import {
  Power, Settings, DollarSign, TrendingUp, Shield, AlertTriangle,
  Check, X, Sliders, Activity, Zap, Clock, Target, BarChart2
} from 'lucide-react';
import api from '../services/api';
import soundService from '../services/soundService';

const AutoTradingSettings = ({ onSettingsChange }) => {
  const [settings, setSettings] = useState(null);
  const [isEnabled, setIsEnabled] = useState(false);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);

  // Local state for settings
  const [localSettings, setLocalSettings] = useState({
    min_confidence: 0.75,
    max_position_size: 0.1,
    max_daily_trades: 10,
    max_daily_loss: 0.05,
    stop_loss_pct: 0.02,
    take_profit_pct: 0.05,
    trading_hours_only: true,
    allow_short_selling: false,
    risk_level: 'moderate' // conservative, moderate, aggressive
  });

  useEffect(() => {
    loadSettings();
    loadStats();
    const interval = setInterval(loadStats, 10000); // Update stats every 10s
    return () => clearInterval(interval);
  }, []);

  const loadSettings = async () => {
    try {
      const response = await api.get('/settings');
      if (response.data.success) {
        const data = response.data.data;
        setSettings(data);
        setIsEnabled(data.trading_controls?.enable_auto_trading || false);

        // Load trading controls into local settings
        if (data.trading_controls) {
          setLocalSettings(prev => ({
            ...prev,
            min_confidence: data.ai_config?.min_confidence || prev.min_confidence,
            max_position_size: data.trading_controls.max_position_size || prev.max_position_size,
            max_daily_loss: data.trading_controls.max_daily_loss || prev.max_daily_loss,
            stop_loss_pct: data.trading_controls.stop_loss_pct || prev.stop_loss_pct
          }));
        }
      }
    } catch (error) {
      console.error('Error loading settings:', error);
    }
  };

  const loadStats = async () => {
    try {
      const [portfolioRes, ordersRes] = await Promise.all([
        api.get('/trading/portfolio'),
        api.get('/trading/orders?limit=100')
      ]);

      if (portfolioRes.data && ordersRes.data) {
        const portfolio = portfolioRes.data;
        const orders = ordersRes.data;

        // Calculate today's trades
        const today = new Date().toDateString();
        const todayTrades = orders.filter(order => {
          const orderDate = new Date(order.created_at).toDateString();
          return orderDate === today;
        });

        setStats({
          portfolio_value: portfolio.total_value,
          daily_pnl: portfolio.daily_pnl,
          today_trades: todayTrades.length,
          total_positions: portfolio.positions?.length || 0
        });
      }
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  const toggleAutoTrading = async () => {
    if (!isEnabled) {
      // Show confirmation before enabling
      const confirmed = window.confirm(
        '⚠️ Warning: You are about to enable automated trading.\n\n' +
        'The AI will execute trades automatically based on signals.\n\n' +
        'Make sure you:\n' +
        '1. Are in paper trading mode (recommended)\n' +
        '2. Have reviewed and understand the risk settings\n' +
        '3. Are comfortable with automated execution\n\n' +
        'Continue?'
      );

      if (!confirmed) return;
    }

    setLoading(true);
    try {
      const response = await api.put('/settings', {
        ...settings,
        trading_controls: {
          ...settings.trading_controls,
          enable_auto_trading: !isEnabled
        }
      });

      if (response.data.success) {
        setIsEnabled(!isEnabled);
        soundService.playTradeExecuted();
        onSettingsChange && onSettingsChange();
      }
    } catch (error) {
      console.error('Error toggling auto-trading:', error);
      soundService.playTradeFailed();
    } finally {
      setLoading(false);
    }
  };

  const updateSettings = async () => {
    setLoading(true);
    try {
      const response = await api.put('/settings', {
        ...settings,
        trading_controls: {
          ...settings.trading_controls,
          max_position_size: localSettings.max_position_size,
          max_daily_loss: localSettings.max_daily_loss,
          stop_loss_pct: localSettings.stop_loss_pct
        },
        ai_config: {
          ...settings.ai_config,
          min_confidence: localSettings.min_confidence
        }
      });

      if (response.data.success) {
        await loadSettings();
        soundService.playNewAnalysis();
      }
    } catch (error) {
      console.error('Error updating settings:', error);
      soundService.playTradeFailed();
    } finally {
      setLoading(false);
    }
  };

  const applyRiskPreset = (level) => {
    const presets = {
      conservative: {
        min_confidence: 0.85,
        max_position_size: 0.05,
        max_daily_trades: 5,
        max_daily_loss: 0.02,
        stop_loss_pct: 0.01,
        take_profit_pct: 0.03
      },
      moderate: {
        min_confidence: 0.75,
        max_position_size: 0.1,
        max_daily_trades: 10,
        max_daily_loss: 0.05,
        stop_loss_pct: 0.02,
        take_profit_pct: 0.05
      },
      aggressive: {
        min_confidence: 0.65,
        max_position_size: 0.15,
        max_daily_trades: 20,
        max_daily_loss: 0.1,
        stop_loss_pct: 0.03,
        take_profit_pct: 0.08
      }
    };

    setLocalSettings({
      ...localSettings,
      ...presets[level],
      risk_level: level
    });
    soundService.playTone(800, 100, 'sine');
  };

  return (
    <div className="auto-trading-settings">
      {/* Header with Master Toggle */}
      <div className="settings-header">
        <div className="header-left">
          <div className="header-icon-wrapper">
            <Zap className={`header-icon ${isEnabled ? 'enabled' : ''}`} size={28} />
          </div>
          <div className="header-info">
            <h2 className="settings-title">Automated Trading</h2>
            <p className="settings-subtitle">
              {isEnabled ? 'AI is actively executing trades' : 'AI trading is disabled'}
            </p>
          </div>
        </div>

        <button
          onClick={toggleAutoTrading}
          disabled={loading}
          className={`master-toggle ${isEnabled ? 'enabled' : ''} ${loading ? 'loading' : ''}`}
        >
          <Power size={20} />
          <span>{isEnabled ? 'Enabled' : 'Disabled'}</span>
        </button>
      </div>

      {/* Status Stats */}
      {stats && (
        <div className="status-stats">
          <div className="stat-box">
            <DollarSign size={18} className="stat-icon" />
            <div className="stat-content">
              <div className="stat-label">Portfolio Value</div>
              <div className="stat-value">${stats.portfolio_value?.toLocaleString() || '0'}</div>
            </div>
          </div>

          <div className={`stat-box ${stats.daily_pnl >= 0 ? 'positive' : 'negative'}`}>
            <TrendingUp size={18} className="stat-icon" />
            <div className="stat-content">
              <div className="stat-label">Daily P&L</div>
              <div className="stat-value">
                {stats.daily_pnl >= 0 ? '+' : ''}${stats.daily_pnl?.toFixed(2) || '0'}
              </div>
            </div>
          </div>

          <div className="stat-box">
            <Activity size={18} className="stat-icon" />
            <div className="stat-content">
              <div className="stat-label">Today's Trades</div>
              <div className="stat-value">{stats.today_trades} / {localSettings.max_daily_trades}</div>
            </div>
          </div>

          <div className="stat-box">
            <BarChart2 size={18} className="stat-icon" />
            <div className="stat-content">
              <div className="stat-label">Open Positions</div>
              <div className="stat-value">{stats.total_positions}</div>
            </div>
          </div>
        </div>
      )}

      {/* Warning Banner if Enabled */}
      {isEnabled && (
        <div className="warning-banner">
          <AlertTriangle size={18} />
          <span>Automated trading is active. Monitor your positions regularly.</span>
        </div>
      )}

      {/* Risk Level Presets */}
      <div className="risk-presets-section">
        <h3 className="section-title">
          <Shield size={18} />
          Risk Profile
        </h3>
        <div className="risk-presets">
          <button
            onClick={() => applyRiskPreset('conservative')}
            className={`risk-preset ${localSettings.risk_level === 'conservative' ? 'active' : ''}`}
          >
            <div className="preset-name">Conservative</div>
            <div className="preset-desc">Low risk, high confidence</div>
            <div className="preset-details">
              <span>• Min Confidence: 85%</span>
              <span>• Max Position: 5%</span>
              <span>• Stop Loss: 1%</span>
            </div>
          </button>

          <button
            onClick={() => applyRiskPreset('moderate')}
            className={`risk-preset ${localSettings.risk_level === 'moderate' ? 'active' : ''}`}
          >
            <div className="preset-name">Moderate</div>
            <div className="preset-desc">Balanced approach</div>
            <div className="preset-details">
              <span>• Min Confidence: 75%</span>
              <span>• Max Position: 10%</span>
              <span>• Stop Loss: 2%</span>
            </div>
          </button>

          <button
            onClick={() => applyRiskPreset('aggressive')}
            className={`risk-preset ${localSettings.risk_level === 'aggressive' ? 'active' : ''}`}
          >
            <div className="preset-name">Aggressive</div>
            <div className="preset-desc">Higher risk, more trades</div>
            <div className="preset-details">
              <span>• Min Confidence: 65%</span>
              <span>• Max Position: 15%</span>
              <span>• Stop Loss: 3%</span>
            </div>
          </button>
        </div>
      </div>

      {/* Detailed Settings */}
      <div className="detailed-settings">
        <h3 className="section-title">
          <Sliders size={18} />
          Fine-tune Settings
        </h3>

        <div className="settings-grid">
          <div className="setting-item">
            <label className="setting-label">
              Minimum Confidence
              <span className="setting-value">{(localSettings.min_confidence * 100).toFixed(0)}%</span>
            </label>
            <input
              type="range"
              min="0.5"
              max="0.95"
              step="0.05"
              value={localSettings.min_confidence}
              onChange={(e) => setLocalSettings({ ...localSettings, min_confidence: parseFloat(e.target.value) })}
              className="setting-slider"
            />
            <p className="setting-hint">Only execute trades with confidence above this threshold</p>
          </div>

          <div className="setting-item">
            <label className="setting-label">
              Max Position Size
              <span className="setting-value">{(localSettings.max_position_size * 100).toFixed(0)}%</span>
            </label>
            <input
              type="range"
              min="0.01"
              max="0.25"
              step="0.01"
              value={localSettings.max_position_size}
              onChange={(e) => setLocalSettings({ ...localSettings, max_position_size: parseFloat(e.target.value) })}
              className="setting-slider"
            />
            <p className="setting-hint">Maximum portfolio percentage per position</p>
          </div>

          <div className="setting-item">
            <label className="setting-label">
              Stop Loss
              <span className="setting-value">{(localSettings.stop_loss_pct * 100).toFixed(1)}%</span>
            </label>
            <input
              type="range"
              min="0.005"
              max="0.1"
              step="0.005"
              value={localSettings.stop_loss_pct}
              onChange={(e) => setLocalSettings({ ...localSettings, stop_loss_pct: parseFloat(e.target.value) })}
              className="setting-slider"
            />
            <p className="setting-hint">Automatic stop loss percentage</p>
          </div>

          <div className="setting-item">
            <label className="setting-label">
              Max Daily Loss
              <span className="setting-value">{(localSettings.max_daily_loss * 100).toFixed(0)}%</span>
            </label>
            <input
              type="range"
              min="0.01"
              max="0.2"
              step="0.01"
              value={localSettings.max_daily_loss}
              onChange={(e) => setLocalSettings({ ...localSettings, max_daily_loss: parseFloat(e.target.value) })}
              className="setting-slider"
            />
            <p className="setting-hint">Stop all trading if daily loss exceeds this</p>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="settings-actions">
        <button onClick={updateSettings} disabled={loading} className="save-btn">
          <Check size={18} />
          Save Settings
        </button>
      </div>

      <style jsx>{`
        .auto-trading-settings {
          background: rgba(30, 41, 59, 0.5);
          border-radius: 12px;
          border: 1px solid rgba(100, 116, 139, 0.2);
          padding: 24px;
          max-width: 1200px;
          margin: 0 auto;
        }

        .settings-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 24px;
          padding-bottom: 20px;
          border-bottom: 1px solid rgba(100, 116, 139, 0.2);
        }

        .header-left {
          display: flex;
          gap: 16px;
          align-items: center;
        }

        .header-icon-wrapper {
          padding: 12px;
          background: rgba(59, 130, 246, 0.1);
          border-radius: 12px;
          border: 1px solid rgba(59, 130, 246, 0.3);
        }

        .header-icon {
          color: #3b82f6;
          transition: all 0.3s ease;
        }

        .header-icon.enabled {
          color: #22c55e;
          animation: pulse 2s ease-in-out infinite;
        }

        .header-info {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .settings-title {
          font-size: 22px;
          font-weight: 700;
          margin: 0;
          color: #e2e8f0;
        }

        .settings-subtitle {
          font-size: 13px;
          color: #94a3b8;
          margin: 0;
        }

        .master-toggle {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 12px 24px;
          background: rgba(100, 116, 139, 0.2);
          border: 2px solid rgba(100, 116, 139, 0.3);
          border-radius: 10px;
          color: #94a3b8;
          font-weight: 600;
          font-size: 14px;
          cursor: pointer;
          transition: all 0.3s ease;
        }

        .master-toggle:hover:not(:disabled) {
          background: rgba(100, 116, 139, 0.3);
          transform: translateY(-2px);
        }

        .master-toggle.enabled {
          background: linear-gradient(135deg, rgba(34, 197, 94, 0.2) 0%, rgba(16, 185, 129, 0.2) 100%);
          border-color: rgba(34, 197, 94, 0.5);
          color: #22c55e;
          box-shadow: 0 0 20px rgba(34, 197, 94, 0.3);
        }

        .master-toggle:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .status-stats {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 16px;
          margin-bottom: 24px;
        }

        .stat-box {
          display: flex;
          gap: 12px;
          padding: 16px;
          background: rgba(15, 23, 42, 0.6);
          border-radius: 10px;
          border: 1px solid rgba(100, 116, 139, 0.2);
          transition: all 0.3s ease;
        }

        .stat-box:hover {
          border-color: rgba(59, 130, 246, 0.3);
          transform: translateY(-2px);
        }

        .stat-box.positive {
          border-color: rgba(34, 197, 94, 0.3);
        }

        .stat-box.negative {
          border-color: rgba(239, 68, 68, 0.3);
        }

        .stat-icon {
          color: #3b82f6;
        }

        .stat-box.positive .stat-icon {
          color: #22c55e;
        }

        .stat-box.negative .stat-icon {
          color: #ef4444;
        }

        .stat-content {
          flex: 1;
        }

        .stat-label {
          font-size: 12px;
          color: #94a3b8;
          margin-bottom: 4px;
        }

        .stat-value {
          font-size: 18px;
          font-weight: 700;
          color: #e2e8f0;
        }

        .stat-box.positive .stat-value {
          color: #22c55e;
        }

        .stat-box.negative .stat-value {
          color: #ef4444;
        }

        .warning-banner {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px 16px;
          background: rgba(245, 158, 11, 0.1);
          border: 1px solid rgba(245, 158, 11, 0.3);
          border-radius: 8px;
          color: #f59e0b;
          margin-bottom: 24px;
          animation: pulse 3s ease-in-out infinite;
        }

        .risk-presets-section {
          margin-bottom: 28px;
        }

        .section-title {
          display: flex;
          align-items: center;
          gap: 10px;
          font-size: 16px;
          font-weight: 600;
          color: #e2e8f0;
          margin-bottom: 16px;
        }

        .risk-presets {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
          gap: 16px;
        }

        .risk-preset {
          padding: 20px;
          background: rgba(15, 23, 42, 0.6);
          border: 2px solid rgba(100, 116, 139, 0.2);
          border-radius: 10px;
          cursor: pointer;
          transition: all 0.3s ease;
          text-align: left;
        }

        .risk-preset:hover {
          border-color: rgba(59, 130, 246, 0.4);
          transform: translateY(-3px);
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }

        .risk-preset.active {
          border-color: rgba(59, 130, 246, 0.6);
          background: rgba(59, 130, 246, 0.1);
          box-shadow: 0 0 20px rgba(59, 130, 246, 0.2);
        }

        .preset-name {
          font-size: 16px;
          font-weight: 700;
          color: #e2e8f0;
          margin-bottom: 6px;
        }

        .preset-desc {
          font-size: 13px;
          color: #94a3b8;
          margin-bottom: 12px;
        }

        .preset-details {
          display: flex;
          flex-direction: column;
          gap: 4px;
          font-size: 11px;
          color: #64748b;
        }

        .detailed-settings {
          margin-bottom: 24px;
        }

        .settings-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
          gap: 24px;
        }

        .setting-item {
          display: flex;
          flex-direction: column;
          gap: 10px;
        }

        .setting-label {
          display: flex;
          justify-content: space-between;
          align-items: center;
          font-size: 14px;
          color: #e2e8f0;
          font-weight: 500;
        }

        .setting-value {
          color: #3b82f6;
          font-weight: 700;
        }

        .setting-slider {
          width: 100%;
          height: 6px;
          border-radius: 3px;
          background: rgba(100, 116, 139, 0.3);
          outline: none;
          -webkit-appearance: none;
        }

        .setting-slider::-webkit-slider-thumb {
          -webkit-appearance: none;
          width: 16px;
          height: 16px;
          border-radius: 50%;
          background: #3b82f6;
          cursor: pointer;
        }

        .setting-slider::-moz-range-thumb {
          width: 16px;
          height: 16px;
          border-radius: 50%;
          background: #3b82f6;
          cursor: pointer;
          border: none;
        }

        .setting-hint {
          font-size: 12px;
          color: #64748b;
          margin: 0;
        }

        .settings-actions {
          display: flex;
          justify-content: flex-end;
          gap: 12px;
        }

        .save-btn {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px 32px;
          background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
          border: none;
          border-radius: 8px;
          color: white;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.3s ease;
        }

        .save-btn:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4);
        }

        .save-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        @keyframes pulse {
          0%, 100% {
            opacity: 1;
          }
          50% {
            opacity: 0.8;
          }
        }

        @media (max-width: 768px) {
          .settings-header {
            flex-direction: column;
            gap: 16px;
            align-items: flex-start;
          }

          .risk-presets {
            grid-template-columns: 1fr;
          }

          .settings-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
};

export default AutoTradingSettings;
