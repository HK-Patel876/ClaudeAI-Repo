import React, { useState, useEffect } from 'react';
import { systemAPI } from '../services/api';

function DataSourceIndicator() {
  const [providers, setProviders] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadProviderStatus();
    const interval = setInterval(loadProviderStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadProviderStatus = async () => {
    try {
      const response = await systemAPI.getProviderStatus();
      setProviders(response.data);
      setLoading(false);
    } catch (err) {
      console.error('Error loading provider status:', err);
      setLoading(false);
    }
  };

  if (loading) {
    return null;
  }

  const providerLabels = {
    alpaca: 'Alpaca',
    alpha_vantage: 'Alpha Vantage',
    polygon: 'Polygon.io',
    coinbase: 'Coinbase',
    yfinance: 'yfinance'
  };

  const providerStatus = providers?.providers || {};
  const activeCount = providers?.active_count || 0;

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      padding: '8px 12px',
      background: 'rgba(15, 23, 42, 0.5)',
      borderRadius: '8px',
      border: '1px solid rgba(148, 163, 184, 0.2)'
    }}>
      <div style={{
        fontSize: '12px',
        fontWeight: 600,
        color: '#94a3b8',
        marginRight: '4px'
      }}>
        Data Sources:
      </div>
      
      {Object.entries(providerStatus).map(([key, info]) => (
        <div
          key={key}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            padding: '4px 8px',
            background: info.active ? 'rgba(74, 222, 128, 0.1)' : 'rgba(100, 116, 139, 0.1)',
            border: `1px solid ${info.active ? 'rgba(74, 222, 128, 0.3)' : 'rgba(100, 116, 139, 0.2)'}`,
            borderRadius: '4px',
            fontSize: '11px',
            fontWeight: 500
          }}
        >
          <div style={{
            width: '6px',
            height: '6px',
            borderRadius: '50%',
            background: info.active ? '#4ade80' : '#64748b'
          }} />
          <span style={{ color: info.active ? '#4ade80' : '#94a3b8' }}>
            {providerLabels[key] || key}
          </span>
        </div>
      ))}
      
      {activeCount === 0 && (
        <div style={{
          fontSize: '11px',
          color: '#fbbf24',
          fontWeight: 500,
          padding: '4px 8px',
          background: 'rgba(251, 191, 36, 0.1)',
          borderRadius: '4px',
          border: '1px solid rgba(251, 191, 36, 0.2)'
        }}>
          ⚠️ Using demo data
        </div>
      )}
    </div>
  );
}

export default DataSourceIndicator;
