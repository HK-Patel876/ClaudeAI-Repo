import React, { useState, useEffect } from 'react';
import api from '../services/api';

function SettingsModal({ isOpen, onClose }) {
  const [activeTab, setActiveTab] = useState('data');
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadSettings();
    }
  }, [isOpen]);

  const loadSettings = async () => {
    setLoading(true);
    try {
      const response = await api.get('/settings');
      setSettings(response.data.data);
    } catch (err) {
      console.error('Error loading settings:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.put('/settings', settings);
      onClose();
    } catch (err) {
      console.error('Error saving settings:', err);
      alert('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const updateSetting = (category, key, value) => {
    setSettings(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [key]: value
      }
    }));
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content settings-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>⚙️ Settings</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="settings-tabs">
          <button
            className={`tab ${activeTab === 'data' ? 'active' : ''}`}
            onClick={() => setActiveTab('data')}
          >
            📊 Data & API
          </button>
          <button
            className={`tab ${activeTab === 'trading' ? 'active' : ''}`}
            onClick={() => setActiveTab('trading')}
          >
            💰 Trading Controls
          </button>
          <button
            className={`tab ${activeTab === 'ai' ? 'active' : ''}`}
            onClick={() => setActiveTab('ai')}
          >
            🤖 AI Config
          </button>
          <button
            className={`tab ${activeTab === 'display' ? 'active' : ''}`}
            onClick={() => setActiveTab('display')}
          >
            🎨 Display
          </button>
        </div>

        <div className="settings-body">
          {loading ? (
            <div className="loading">Loading settings...</div>
          ) : settings ? (
            <>
              {activeTab === 'data' && (
                <div className="settings-section">
                  <h3>Data & API Settings</h3>
                  <div className="form-group">
                    <label>Refresh Interval (seconds)</label>
                    <input
                      type="number"
                      value={settings.data_api?.refresh_interval || 10}
                      onChange={e => updateSetting('data_api', 'refresh_interval', parseInt(e.target.value))}
                      min="5"
                      max="60"
                    />
                  </div>

                  <h4 style={{ marginTop: '30px', marginBottom: '15px' }}>🔐 API Keys</h4>
                  
                  <div className="api-provider-section" style={{ marginBottom: '20px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
                      <strong>Alpaca Trading</strong>
                      {settings.data_api?.alpaca_api_key && (
                        <span style={{ color: '#4ade80' }}>✓ Active</span>
                      )}
                    </div>
                    <div className="form-group">
                      <label>API Key</label>
                      <input
                        type="password"
                        value={settings.data_api?.alpaca_api_key || ''}
                        onChange={e => updateSetting('data_api', 'alpaca_api_key', e.target.value)}
                        placeholder="Enter Alpaca API Key"
                      />
                    </div>
                    <div className="form-group">
                      <label>Secret Key</label>
                      <input
                        type="password"
                        value={settings.data_api?.alpaca_secret_key || ''}
                        onChange={e => updateSetting('data_api', 'alpaca_secret_key', e.target.value)}
                        placeholder="Enter Alpaca Secret Key"
                      />
                    </div>
                  </div>

                  <div className="api-provider-section" style={{ marginBottom: '20px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
                      <strong>Alpha Vantage</strong>
                      {settings.data_api?.alpha_vantage_api_key && (
                        <span style={{ color: '#4ade80' }}>✓ Active</span>
                      )}
                    </div>
                    <div className="form-group">
                      <label>API Key</label>
                      <input
                        type="password"
                        value={settings.data_api?.alpha_vantage_api_key || ''}
                        onChange={e => updateSetting('data_api', 'alpha_vantage_api_key', e.target.value)}
                        placeholder="Enter Alpha Vantage API Key"
                      />
                    </div>
                  </div>

                  <div className="api-provider-section" style={{ marginBottom: '20px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
                      <strong>Polygon.io</strong>
                      {settings.data_api?.polygon_api_key && (
                        <span style={{ color: '#4ade80' }}>✓ Active</span>
                      )}
                    </div>
                    <div className="form-group">
                      <label>API Key</label>
                      <input
                        type="password"
                        value={settings.data_api?.polygon_api_key || ''}
                        onChange={e => updateSetting('data_api', 'polygon_api_key', e.target.value)}
                        placeholder="Enter Polygon API Key"
                      />
                    </div>
                  </div>

                  <div className="api-provider-section" style={{ marginBottom: '20px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
                      <strong>Coinbase</strong>
                      {settings.data_api?.coinbase_api_key && (
                        <span style={{ color: '#4ade80' }}>✓ Active</span>
                      )}
                    </div>
                    <div className="form-group">
                      <label>API Key</label>
                      <input
                        type="password"
                        value={settings.data_api?.coinbase_api_key || ''}
                        onChange={e => updateSetting('data_api', 'coinbase_api_key', e.target.value)}
                        placeholder="Enter Coinbase API Key"
                      />
                    </div>
                    <div className="form-group">
                      <label>API Secret</label>
                      <input
                        type="password"
                        value={settings.data_api?.coinbase_api_secret || ''}
                        onChange={e => updateSetting('data_api', 'coinbase_api_secret', e.target.value)}
                        placeholder="Enter Coinbase API Secret"
                      />
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'trading' && (
                <div className="settings-section">
                  <h3>Trading Controls</h3>
                  
                  <div className="form-group" style={{ 
                    padding: '15px', 
                    background: 'rgba(251, 191, 36, 0.1)', 
                    borderRadius: '8px',
                    border: '1px solid rgba(251, 191, 36, 0.3)',
                    marginBottom: '20px'
                  }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '16px', fontWeight: 600 }}>
                      <input
                        type="checkbox"
                        checked={settings.trading_controls?.enable_auto_trading || false}
                        onChange={e => {
                          if (e.target.checked && !window.confirm(
                            '⚠️ WARNING: Enable Auto-Trading?\n\n' +
                            'This will allow the AI to automatically execute trades based on its analysis.\n\n' +
                            'Make sure:\n' +
                            '✓ Paper trading mode is enabled\n' +
                            '✓ Risk limits are properly configured\n' +
                            '✓ You understand the risks involved\n\n' +
                            'Do you want to continue?'
                          )) {
                            return;
                          }
                          updateSetting('trading_controls', 'enable_auto_trading', e.target.checked);
                        }}
                      />
                      🤖 Enable Auto-Trading
                    </label>
                    {settings.trading_controls?.enable_auto_trading && (
                      <div style={{ 
                        marginTop: '10px', 
                        padding: '10px', 
                        background: 'rgba(34, 197, 94, 0.1)',
                        borderRadius: '4px',
                        fontSize: '14px',
                        color: '#4ade80'
                      }}>
                        ✓ Auto-trading is ACTIVE - AI will execute trades automatically
                      </div>
                    )}
                  </div>

                  <div className="form-group">
                    <label>
                      <input
                        type="checkbox"
                        checked={settings.trading_controls?.paper_trading !== false}
                        onChange={e => updateSetting('trading_controls', 'paper_trading', e.target.checked)}
                      />
                      Paper Trading Mode
                    </label>
                  </div>
                  <div className="form-group">
                    <label>Max Position Size (%)</label>
                    <input
                      type="number"
                      value={(settings.trading_controls?.max_position_size || 0.1) * 100}
                      onChange={e => updateSetting('trading_controls', 'max_position_size', parseFloat(e.target.value) / 100)}
                      min="1"
                      max="50"
                      step="1"
                    />
                  </div>
                  <div className="form-group">
                    <label>Max Daily Loss (%)</label>
                    <input
                      type="number"
                      value={(settings.trading_controls?.max_daily_loss || 0.05) * 100}
                      onChange={e => updateSetting('trading_controls', 'max_daily_loss', parseFloat(e.target.value) / 100)}
                      min="1"
                      max="20"
                      step="1"
                    />
                  </div>
                  <div className="form-group">
                    <label>Stop Loss (%)</label>
                    <input
                      type="number"
                      value={(settings.trading_controls?.stop_loss_pct || 0.02) * 100}
                      onChange={e => updateSetting('trading_controls', 'stop_loss_pct', parseFloat(e.target.value) / 100)}
                      min="0.5"
                      max="10"
                      step="0.5"
                    />
                  </div>
                </div>
              )}

              {activeTab === 'ai' && (
                <div className="settings-section">
                  <h3>AI Configuration</h3>
                  <div className="form-group">
                    <label>Analysis Cadence (seconds)</label>
                    <input
                      type="number"
                      value={settings.ai_config?.analysis_cadence || 60}
                      onChange={e => updateSetting('ai_config', 'analysis_cadence', parseInt(e.target.value))}
                      min="30"
                      max="300"
                      step="30"
                    />
                  </div>
                  <h4>Agent Weights</h4>
                  <div className="form-group">
                    <label>Technical Agent</label>
                    <input
                      type="number"
                      value={settings.ai_config?.agent_weights?.technical || 1.0}
                      onChange={e => updateSetting('ai_config', 'agent_weights', {
                        ...settings.ai_config?.agent_weights,
                        technical: parseFloat(e.target.value)
                      })}
                      min="0"
                      max="3"
                      step="0.1"
                    />
                  </div>
                  <div className="form-group">
                    <label>News Agent</label>
                    <input
                      type="number"
                      value={settings.ai_config?.agent_weights?.news || 1.0}
                      onChange={e => updateSetting('ai_config', 'agent_weights', {
                        ...settings.ai_config?.agent_weights,
                        news: parseFloat(e.target.value)
                      })}
                      min="0"
                      max="3"
                      step="0.1"
                    />
                  </div>
                  <div className="form-group">
                    <label>Fundamental Agent</label>
                    <input
                      type="number"
                      value={settings.ai_config?.agent_weights?.fundamental || 1.0}
                      onChange={e => updateSetting('ai_config', 'agent_weights', {
                        ...settings.ai_config?.agent_weights,
                        fundamental: parseFloat(e.target.value)
                      })}
                      min="0"
                      max="3"
                      step="0.1"
                    />
                  </div>
                  <div className="form-group">
                    <label>Risk Agent</label>
                    <input
                      type="number"
                      value={settings.ai_config?.agent_weights?.risk || 1.5}
                      onChange={e => updateSetting('ai_config', 'agent_weights', {
                        ...settings.ai_config?.agent_weights,
                        risk: parseFloat(e.target.value)
                      })}
                      min="0"
                      max="3"
                      step="0.1"
                    />
                  </div>
                </div>
              )}

              {activeTab === 'display' && (
                <div className="settings-section">
                  <h3>Display Preferences</h3>
                  <div className="form-group">
                    <label>Theme</label>
                    <select
                      value={settings.display?.theme || 'dark'}
                      onChange={e => updateSetting('display', 'theme', e.target.value)}
                    >
                      <option value="dark">Dark</option>
                      <option value="light">Light</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Layout Density</label>
                    <select
                      value={settings.display?.layout_density || 'comfortable'}
                      onChange={e => updateSetting('display', 'layout_density', e.target.value)}
                    >
                      <option value="compact">Compact</option>
                      <option value="comfortable">Comfortable</option>
                      <option value="spacious">Spacious</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label>
                      <input
                        type="checkbox"
                        checked={settings.display?.show_news_ticker !== false}
                        onChange={e => updateSetting('display', 'show_news_ticker', e.target.checked)}
                      />
                      Show News Ticker
                    </label>
                  </div>
                </div>
              )}
            </>
          ) : null}
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
            {saving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default SettingsModal;
