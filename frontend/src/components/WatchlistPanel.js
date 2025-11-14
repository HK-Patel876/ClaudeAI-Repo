import React, { useState, useEffect } from 'react';
import api from '../services/api';

function WatchlistPanel() {
  const [watchlist, setWatchlist] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [newSymbol, setNewSymbol] = useState('');
  const [showAlertForm, setShowAlertForm] = useState(false);
  const [newAlert, setNewAlert] = useState({
    symbol: '',
    condition: 'ABOVE',
    threshold: 0
  });

  useEffect(() => {
    loadWatchlist();
    loadAlerts();
  }, []);

  const loadWatchlist = async () => {
    try {
      const response = await api.get('/watchlist');
      setWatchlist(response.data.data || []);
    } catch (err) {
      console.error('Error loading watchlist:', err);
    }
  };

  const loadAlerts = async () => {
    try {
      const response = await api.get('/alerts');
      setAlerts(response.data.data || []);
    } catch (err) {
      console.error('Error loading alerts:', err);
    }
  };

  const addToWatchlist = async (e) => {
    e.preventDefault();
    if (!newSymbol.trim()) return;

    try {
      await api.post('/watchlist', { symbol: newSymbol.toUpperCase() });
      setNewSymbol('');
      loadWatchlist();
    } catch (err) {
      console.error('Error adding to watchlist:', err);
    }
  };

  const removeFromWatchlist = async (symbol) => {
    try {
      await api.delete(`/watchlist/${symbol}`);
      loadWatchlist();
    } catch (err) {
      console.error('Error removing from watchlist:', err);
    }
  };

  const createAlert = async (e) => {
    e.preventDefault();
    try {
      await api.post('/alerts', newAlert);
      setNewAlert({ symbol: '', condition: 'ABOVE', threshold: 0 });
      setShowAlertForm(false);
      loadAlerts();
    } catch (err) {
      console.error('Error creating alert:', err);
    }
  };

  const deleteAlert = async (alertId) => {
    try {
      await api.delete(`/alerts/${alertId}`);
      loadAlerts();
    } catch (err) {
      console.error('Error deleting alert:', err);
    }
  };

  const triggeredAlerts = alerts.filter(a => a.triggered_at);
  const activeAlerts = alerts.filter(a => a.is_active);

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">📋 Watchlist & Alerts</h3>
      </div>

      <div className="watchlist-content">
        <div className="watchlist-section">
          <h4>Watchlist</h4>
          <form onSubmit={addToWatchlist} className="add-symbol-form">
            <input
              type="text"
              placeholder="Add symbol (e.g., AAPL)"
              value={newSymbol}
              onChange={e => setNewSymbol(e.target.value)}
              className="symbol-input"
            />
            <button type="submit" className="btn btn-sm btn-primary">Add</button>
          </form>
          
          <div className="watchlist-items">
            {watchlist.length === 0 ? (
              <p className="empty-message">No symbols in watchlist</p>
            ) : (
              watchlist.map(item => (
                <div key={item.id} className="watchlist-item">
                  <span className="symbol-name">{item.symbol}</span>
                  <button
                    onClick={() => removeFromWatchlist(item.symbol)}
                    className="remove-btn"
                  >
                    ×
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="alerts-section">
          <div className="section-header">
            <h4>Alerts</h4>
            <button
              className="btn btn-sm btn-primary"
              onClick={() => setShowAlertForm(!showAlertForm)}
            >
              + New Alert
            </button>
          </div>

          {showAlertForm && (
            <form onSubmit={createAlert} className="alert-form">
              <input
                type="text"
                placeholder="Symbol"
                value={newAlert.symbol}
                onChange={e => setNewAlert({...newAlert, symbol: e.target.value.toUpperCase()})}
                required
              />
              <select
                value={newAlert.condition}
                onChange={e => setNewAlert({...newAlert, condition: e.target.value})}
              >
                <option value="ABOVE">Above</option>
                <option value="BELOW">Below</option>
              </select>
              <input
                type="number"
                placeholder="Price"
                value={newAlert.threshold}
                onChange={e => setNewAlert({...newAlert, threshold: parseFloat(e.target.value)})}
                step="0.01"
                required
              />
              <button type="submit" className="btn btn-sm btn-primary">Create</button>
            </form>
          )}

          {triggeredAlerts.length > 0 && (
            <div className="triggered-alerts">
              <h5>🔔 Triggered</h5>
              {triggeredAlerts.map(alert => (
                <div key={alert.id} className="alert-item triggered">
                  <div className="alert-info">
                    <strong>{alert.symbol}</strong>
                    <span>{alert.condition} ${alert.threshold}</span>
                  </div>
                  <button onClick={() => deleteAlert(alert.id)} className="remove-btn">×</button>
                </div>
              ))}
            </div>
          )}

          <div className="active-alerts">
            <h5>Active Alerts</h5>
            {activeAlerts.length === 0 ? (
              <p className="empty-message">No active alerts</p>
            ) : (
              activeAlerts.map(alert => (
                <div key={alert.id} className="alert-item">
                  <div className="alert-info">
                    <strong>{alert.symbol}</strong>
                    <span>{alert.condition} ${alert.threshold}</span>
                  </div>
                  <button onClick={() => deleteAlert(alert.id)} className="remove-btn">×</button>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default WatchlistPanel;
