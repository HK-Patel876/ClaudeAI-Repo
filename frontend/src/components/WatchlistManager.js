import React, { useState, useEffect } from 'react';
import {
  Plus, Trash2, Star, TrendingUp, TrendingDown, Bell, Eye,
  Search, Filter, Download, RefreshCw, BarChart3, AlertCircle, X
} from 'lucide-react';
import api from '../services/api';
import soundService from '../services/soundService';

const WatchlistManager = ({ onSymbolSelect }) => {
  const [watchlist, setWatchlist] = useState([]);
  const [prices, setPrices] = useState({});
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [newSymbol, setNewSymbol] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [showAlertModal, setShowAlertModal] = useState(false);
  const [selectedSymbol, setSelectedSymbol] = useState(null);
  const [sortBy, setSortBy] = useState('symbol'); // symbol, change, volume
  const [filterActive, setFilterActive] = useState('all'); // all, gainers, losers

  // Alert form state
  const [alertForm, setAlertForm] = useState({
    condition: 'ABOVE',
    threshold: '',
    message: ''
  });

  useEffect(() => {
    loadWatchlist();
    loadAlerts();
    const interval = setInterval(() => {
      loadPrices();
    }, 3000); // Update prices every 3 seconds
    return () => clearInterval(interval);
  }, []);

  const loadWatchlist = async () => {
    try {
      const response = await api.get('/watchlist');
      if (response.data.success) {
        setWatchlist(response.data.data);
        loadPrices();
      }
    } catch (error) {
      console.error('Error loading watchlist:', error);
    }
  };

  const loadPrices = async () => {
    if (watchlist.length === 0) return;

    try {
      const pricePromises = watchlist.map(item =>
        api.get(`/data/price/${item.symbol}`).catch(() => null)
      );

      const responses = await Promise.all(pricePromises);
      const priceData = {};

      responses.forEach((response, index) => {
        if (response?.data) {
          priceData[watchlist[index].symbol] = response.data;
        }
      });

      setPrices(priceData);
    } catch (error) {
      console.error('Error loading prices:', error);
    }
  };

  const loadAlerts = async () => {
    try {
      const response = await api.get('/alerts?active_only=true');
      if (response.data.success) {
        setAlerts(response.data.data);
      }
    } catch (error) {
      console.error('Error loading alerts:', error);
    }
  };

  const addSymbol = async () => {
    if (!newSymbol.trim()) return;

    setLoading(true);
    try {
      const response = await api.post('/watchlist', {
        symbol: newSymbol.toUpperCase().trim()
      });

      if (response.data.success) {
        setNewSymbol('');
        await loadWatchlist();
        soundService.playTradeExecuted();
      }
    } catch (error) {
      console.error('Error adding symbol:', error);
      soundService.playTradeFailed();
    } finally {
      setLoading(false);
    }
  };

  const removeSymbol = async (symbol) => {
    try {
      const response = await api.delete(`/watchlist/${symbol}`);
      if (response.data.success) {
        await loadWatchlist();
        soundService.playTone(400, 150, 'sine');
      }
    } catch (error) {
      console.error('Error removing symbol:', error);
    }
  };

  const createAlert = async () => {
    if (!selectedSymbol || !alertForm.threshold) return;

    try {
      const response = await api.post('/alerts', {
        symbol: selectedSymbol,
        alert_type: 'PRICE',
        condition: alertForm.condition,
        threshold: parseFloat(alertForm.threshold),
        message: alertForm.message
      });

      if (response.data.success) {
        setShowAlertModal(false);
        setAlertForm({ condition: 'ABOVE', threshold: '', message: '' });
        await loadAlerts();
        soundService.playNewAnalysis();
      }
    } catch (error) {
      console.error('Error creating alert:', error);
    }
  };

  const deleteAlert = async (alertId) => {
    try {
      await api.delete(`/alerts/${alertId}`);
      await loadAlerts();
      soundService.playTone(400, 150, 'sine');
    } catch (error) {
      console.error('Error deleting alert:', error);
    }
  };

  const exportWatchlist = () => {
    const data = watchlist.map(item => ({
      symbol: item.symbol,
      price: prices[item.symbol]?.price || 0,
      change: prices[item.symbol]?.change_pct || 0,
      notes: item.notes
    }));

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `watchlist-${Date.now()}.json`;
    a.click();
    soundService.playTradeExecuted();
  };

  const getFilteredAndSortedList = () => {
    let filtered = watchlist.filter(item =>
      item.symbol.toLowerCase().includes(searchTerm.toLowerCase())
    );

    // Apply filter
    if (filterActive === 'gainers') {
      filtered = filtered.filter(item => prices[item.symbol]?.change_pct > 0);
    } else if (filterActive === 'losers') {
      filtered = filtered.filter(item => prices[item.symbol]?.change_pct < 0);
    }

    // Apply sort
    filtered.sort((a, b) => {
      if (sortBy === 'symbol') {
        return a.symbol.localeCompare(b.symbol);
      } else if (sortBy === 'change') {
        const changeA = prices[a.symbol]?.change_pct || 0;
        const changeB = prices[b.symbol]?.change_pct || 0;
        return changeB - changeA;
      } else if (sortBy === 'volume') {
        const volA = prices[a.symbol]?.volume || 0;
        const volB = prices[b.symbol]?.volume || 0;
        return volB - volA;
      }
      return 0;
    });

    return filtered;
  };

  const filteredList = getFilteredAndSortedList();

  const getAlertCountForSymbol = (symbol) => {
    return alerts.filter(a => a.symbol === symbol && a.is_active).length;
  };

  return (
    <div className="watchlist-manager">
      {/* Header */}
      <div className="watchlist-header">
        <h2 className="watchlist-title">
          <Star className="title-icon" size={24} />
          Watchlist Manager
        </h2>

        <div className="header-actions">
          <button onClick={loadWatchlist} className="action-btn" title="Refresh">
            <RefreshCw size={18} />
          </button>
          <button onClick={exportWatchlist} className="action-btn" title="Export">
            <Download size={18} />
          </button>
          <span className="watchlist-count">{watchlist.length} symbols</span>
        </div>
      </div>

      {/* Add Symbol */}
      <div className="add-symbol-section">
        <div className="input-group">
          <input
            type="text"
            value={newSymbol}
            onChange={(e) => setNewSymbol(e.target.value.toUpperCase())}
            onKeyPress={(e) => e.key === 'Enter' && addSymbol()}
            placeholder="Enter symbol (e.g. AAPL, MSFT)"
            className="symbol-input"
          />
          <button
            onClick={addSymbol}
            disabled={loading || !newSymbol.trim()}
            className="add-btn"
          >
            <Plus size={20} />
            Add
          </button>
        </div>

        <div className="quick-add-chips">
          {['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META'].map(symbol => (
            <button
              key={symbol}
              onClick={() => {
                setNewSymbol(symbol);
                setTimeout(addSymbol, 100);
              }}
              className="quick-add-chip"
            >
              {symbol}
            </button>
          ))}
        </div>
      </div>

      {/* Search and Filters */}
      <div className="search-filter-section">
        <div className="search-box">
          <Search size={18} className="search-icon" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search symbols..."
            className="search-input"
          />
        </div>

        <div className="filter-buttons">
          <button
            onClick={() => setFilterActive('all')}
            className={`filter-btn ${filterActive === 'all' ? 'active' : ''}`}
          >
            All
          </button>
          <button
            onClick={() => setFilterActive('gainers')}
            className={`filter-btn ${filterActive === 'gainers' ? 'active' : ''}`}
          >
            <TrendingUp size={16} />
            Gainers
          </button>
          <button
            onClick={() => setFilterActive('losers')}
            className={`filter-btn ${filterActive === 'losers' ? 'active' : ''}`}
          >
            <TrendingDown size={16} />
            Losers
          </button>
        </div>

        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="sort-select"
        >
          <option value="symbol">Sort by Symbol</option>
          <option value="change">Sort by Change</option>
          <option value="volume">Sort by Volume</option>
        </select>
      </div>

      {/* Watchlist Items */}
      <div className="watchlist-items">
        {filteredList.length === 0 ? (
          <div className="empty-state">
            <Star size={48} className="empty-icon" />
            <p>No symbols in watchlist</p>
            <p className="empty-hint">Add symbols to track them here</p>
          </div>
        ) : (
          filteredList.map((item, index) => {
            const priceData = prices[item.symbol] || {};
            const change = priceData.change_pct || 0;
            const isPositive = change >= 0;
            const alertCount = getAlertCountForSymbol(item.symbol);

            return (
              <div
                key={item.id}
                className="watchlist-item hover-lift animate-fade-in-up"
                style={{ animationDelay: `${index * 0.05}s` }}
              >
                <div className="item-main">
                  <div className="item-symbol-section">
                    <span className="item-symbol">{item.symbol}</span>
                    {alertCount > 0 && (
                      <span className="alert-badge" title={`${alertCount} active alerts`}>
                        <Bell size={12} />
                        {alertCount}
                      </span>
                    )}
                  </div>

                  <div className="item-price-section">
                    <span className="item-price">
                      ${priceData.price?.toFixed(2) || '--'}
                    </span>
                    <span className={`item-change ${isPositive ? 'positive' : 'negative'}`}>
                      {isPositive ? '▲' : '▼'} {Math.abs(change).toFixed(2)}%
                    </span>
                  </div>
                </div>

                <div className="item-actions">
                  <button
                    onClick={() => onSymbolSelect && onSymbolSelect(item.symbol)}
                    className="item-action-btn"
                    title="View Chart"
                  >
                    <BarChart3 size={16} />
                  </button>
                  <button
                    onClick={() => {
                      setSelectedSymbol(item.symbol);
                      setShowAlertModal(true);
                    }}
                    className="item-action-btn"
                    title="Create Alert"
                  >
                    <Bell size={16} />
                  </button>
                  <button
                    onClick={() => removeSymbol(item.symbol)}
                    className="item-action-btn danger"
                    title="Remove"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Active Alerts Section */}
      {alerts.length > 0 && (
        <div className="alerts-section">
          <h3 className="alerts-title">
            <Bell size={18} />
            Active Alerts ({alerts.length})
          </h3>
          <div className="alerts-list">
            {alerts.map(alert => (
              <div key={alert.id} className="alert-item">
                <div className="alert-info">
                  <span className="alert-symbol">{alert.symbol}</span>
                  <span className="alert-condition">
                    Price {alert.condition.toLowerCase()} ${alert.threshold}
                  </span>
                </div>
                <button
                  onClick={() => deleteAlert(alert.id)}
                  className="alert-delete-btn"
                >
                  <X size={14} />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Alert Modal */}
      {showAlertModal && (
        <div className="modal-overlay" onClick={() => setShowAlertModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3 className="modal-title">Create Price Alert for {selectedSymbol}</h3>

            <div className="modal-form">
              <div className="form-group">
                <label>Condition</label>
                <select
                  value={alertForm.condition}
                  onChange={(e) => setAlertForm({ ...alertForm, condition: e.target.value })}
                  className="form-select"
                >
                  <option value="ABOVE">Price Above</option>
                  <option value="BELOW">Price Below</option>
                </select>
              </div>

              <div className="form-group">
                <label>Price Threshold</label>
                <input
                  type="number"
                  step="0.01"
                  value={alertForm.threshold}
                  onChange={(e) => setAlertForm({ ...alertForm, threshold: e.target.value })}
                  placeholder="Enter price"
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label>Message (Optional)</label>
                <input
                  type="text"
                  value={alertForm.message}
                  onChange={(e) => setAlertForm({ ...alertForm, message: e.target.value })}
                  placeholder="Custom alert message"
                  className="form-input"
                />
              </div>

              <div className="modal-actions">
                <button onClick={() => setShowAlertModal(false)} className="btn-cancel">
                  Cancel
                </button>
                <button onClick={createAlert} className="btn-primary">
                  Create Alert
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        .watchlist-manager {
          background: rgba(30, 41, 59, 0.5);
          border-radius: 12px;
          border: 1px solid rgba(100, 116, 139, 0.2);
          padding: 20px;
        }

        .watchlist-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }

        .watchlist-title {
          display: flex;
          align-items: center;
          gap: 12px;
          font-size: 20px;
          font-weight: 700;
          margin: 0;
        }

        .title-icon {
          color: #f59e0b;
        }

        .header-actions {
          display: flex;
          gap: 12px;
          align-items: center;
        }

        .action-btn {
          padding: 8px 12px;
          background: rgba(59, 130, 246, 0.1);
          border: 1px solid rgba(59, 130, 246, 0.3);
          border-radius: 8px;
          color: #3b82f6;
          cursor: pointer;
          transition: all 0.3s ease;
        }

        .action-btn:hover {
          background: rgba(59, 130, 246, 0.2);
        }

        .watchlist-count {
          padding: 6px 12px;
          background: rgba(139, 92, 246, 0.2);
          border-radius: 12px;
          font-size: 12px;
          color: #a78bfa;
          font-weight: 600;
        }

        .add-symbol-section {
          margin-bottom: 20px;
        }

        .input-group {
          display: flex;
          gap: 8px;
          margin-bottom: 12px;
        }

        .symbol-input {
          flex: 1;
          padding: 12px 16px;
          background: rgba(15, 23, 42, 0.6);
          border: 1px solid rgba(100, 116, 139, 0.3);
          border-radius: 8px;
          color: #e2e8f0;
          font-size: 14px;
        }

        .symbol-input:focus {
          outline: none;
          border-color: #3b82f6;
        }

        .add-btn {
          padding: 12px 24px;
          background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
          border: none;
          border-radius: 8px;
          color: white;
          font-weight: 600;
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: 6px;
          transition: all 0.3s ease;
        }

        .add-btn:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
        }

        .add-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .quick-add-chips {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
        }

        .quick-add-chip {
          padding: 6px 12px;
          background: rgba(100, 116, 139, 0.2);
          border: 1px solid rgba(100, 116, 139, 0.3);
          border-radius: 16px;
          color: #94a3b8;
          font-size: 12px;
          cursor: pointer;
          transition: all 0.3s ease;
        }

        .quick-add-chip:hover {
          background: rgba(59, 130, 246, 0.2);
          border-color: rgba(59, 130, 246, 0.4);
          color: #3b82f6;
        }

        .search-filter-section {
          display: flex;
          gap: 12px;
          margin-bottom: 20px;
          flex-wrap: wrap;
        }

        .search-box {
          flex: 1;
          min-width: 200px;
          position: relative;
        }

        .search-icon {
          position: absolute;
          left: 12px;
          top: 50%;
          transform: translateY(-50%);
          color: #64748b;
        }

        .search-input {
          width: 100%;
          padding: 10px 12px 10px 40px;
          background: rgba(15, 23, 42, 0.6);
          border: 1px solid rgba(100, 116, 139, 0.3);
          border-radius: 8px;
          color: #e2e8f0;
          font-size: 14px;
        }

        .search-input:focus {
          outline: none;
          border-color: #3b82f6;
        }

        .filter-buttons {
          display: flex;
          gap: 8px;
        }

        .filter-btn {
          padding: 10px 16px;
          background: rgba(100, 116, 139, 0.2);
          border: 1px solid rgba(100, 116, 139, 0.3);
          border-radius: 8px;
          color: #94a3b8;
          font-size: 13px;
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: 6px;
          transition: all 0.3s ease;
        }

        .filter-btn:hover {
          background: rgba(100, 116, 139, 0.3);
        }

        .filter-btn.active {
          background: rgba(59, 130, 246, 0.3);
          border-color: rgba(59, 130, 246, 0.5);
          color: #3b82f6;
        }

        .sort-select {
          padding: 10px 16px;
          background: rgba(15, 23, 42, 0.6);
          border: 1px solid rgba(100, 116, 139, 0.3);
          border-radius: 8px;
          color: #e2e8f0;
          font-size: 13px;
          cursor: pointer;
        }

        .watchlist-items {
          max-height: 500px;
          overflow-y: auto;
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .watchlist-items::-webkit-scrollbar {
          width: 6px;
        }

        .watchlist-items::-webkit-scrollbar-thumb {
          background: rgba(100, 116, 139, 0.3);
          border-radius: 3px;
        }

        .watchlist-item {
          padding: 16px;
          background: rgba(15, 23, 42, 0.6);
          border-radius: 10px;
          border: 1px solid rgba(100, 116, 139, 0.2);
          display: flex;
          justify-content: space-between;
          align-items: center;
          transition: all 0.3s ease;
        }

        .item-main {
          display: flex;
          gap: 24px;
          align-items: center;
          flex: 1;
        }

        .item-symbol-section {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .item-symbol {
          font-weight: 700;
          font-size: 16px;
          color: #e2e8f0;
        }

        .alert-badge {
          display: flex;
          align-items: center;
          gap: 4px;
          padding: 4px 8px;
          background: rgba(245, 158, 11, 0.2);
          border-radius: 12px;
          font-size: 11px;
          color: #f59e0b;
        }

        .item-price-section {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .item-price {
          font-weight: 600;
          font-size: 15px;
        }

        .item-change {
          font-size: 13px;
          font-weight: 600;
        }

        .item-change.positive {
          color: #22c55e;
        }

        .item-change.negative {
          color: #ef4444;
        }

        .item-actions {
          display: flex;
          gap: 8px;
        }

        .item-action-btn {
          padding: 8px;
          background: rgba(59, 130, 246, 0.1);
          border: 1px solid rgba(59, 130, 246, 0.3);
          border-radius: 6px;
          color: #3b82f6;
          cursor: pointer;
          transition: all 0.3s ease;
        }

        .item-action-btn:hover {
          background: rgba(59, 130, 246, 0.2);
          transform: translateY(-2px);
        }

        .item-action-btn.danger {
          background: rgba(239, 68, 68, 0.1);
          border-color: rgba(239, 68, 68, 0.3);
          color: #ef4444;
        }

        .item-action-btn.danger:hover {
          background: rgba(239, 68, 68, 0.2);
        }

        .empty-state {
          text-align: center;
          padding: 60px 20px;
          color: #64748b;
        }

        .empty-icon {
          color: #475569;
          margin-bottom: 16px;
        }

        .empty-hint {
          font-size: 14px;
          margin-top: 8px;
        }

        .alerts-section {
          margin-top: 24px;
          padding-top: 24px;
          border-top: 1px solid rgba(100, 116, 139, 0.2);
        }

        .alerts-title {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 16px;
          font-weight: 600;
          margin-bottom: 12px;
          color: #f59e0b;
        }

        .alerts-list {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .alert-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px;
          background: rgba(245, 158, 11, 0.1);
          border-radius: 8px;
          border: 1px solid rgba(245, 158, 11, 0.2);
        }

        .alert-info {
          display: flex;
          gap: 12px;
          align-items: center;
        }

        .alert-symbol {
          font-weight: 700;
          color: #f59e0b;
        }

        .alert-condition {
          font-size: 13px;
          color: #94a3b8;
        }

        .alert-delete-btn {
          padding: 6px;
          background: rgba(239, 68, 68, 0.2);
          border: none;
          border-radius: 4px;
          color: #ef4444;
          cursor: pointer;
          transition: all 0.3s ease;
        }

        .alert-delete-btn:hover {
          background: rgba(239, 68, 68, 0.3);
        }

        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.7);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }

        .modal-content {
          background: #1e293b;
          border-radius: 16px;
          padding: 24px;
          max-width: 450px;
          width: 90%;
          border: 1px solid rgba(100, 116, 139, 0.3);
        }

        .modal-title {
          font-size: 18px;
          font-weight: 700;
          margin-bottom: 20px;
          color: #e2e8f0;
        }

        .modal-form {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .form-group {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .form-group label {
          font-size: 13px;
          color: #94a3b8;
          font-weight: 500;
        }

        .form-input, .form-select {
          padding: 10px 14px;
          background: rgba(15, 23, 42, 0.6);
          border: 1px solid rgba(100, 116, 139, 0.3);
          border-radius: 8px;
          color: #e2e8f0;
          font-size: 14px;
        }

        .form-input:focus, .form-select:focus {
          outline: none;
          border-color: #3b82f6;
        }

        .modal-actions {
          display: flex;
          gap: 12px;
          margin-top: 8px;
        }

        .btn-cancel {
          flex: 1;
          padding: 10px 20px;
          background: rgba(100, 116, 139, 0.2);
          border: 1px solid rgba(100, 116, 139, 0.3);
          border-radius: 8px;
          color: #94a3b8;
          cursor: pointer;
          font-weight: 500;
        }

        .btn-primary {
          flex: 1;
          padding: 10px 20px;
          background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
          border: none;
          border-radius: 8px;
          color: white;
          cursor: pointer;
          font-weight: 600;
        }

        .btn-primary:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
        }
      `}</style>
    </div>
  );
};

export default WatchlistManager;
