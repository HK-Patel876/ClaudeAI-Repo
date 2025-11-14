import React, { useState } from 'react';
import { tradingAPI } from '../services/api';

function TradingPanel({ onTrade }) {
  const [symbol, setSymbol] = useState('AAPL');
  const [executing, setExecuting] = useState(false);
  const [result, setResult] = useState(null);

  const executeTrade = async () => {
    if (!symbol) return;
    
    setExecuting(true);
    setResult(null);
    
    try {
      const response = await tradingAPI.executeTrade(symbol);
      setResult(response.data);
      if (onTrade) onTrade();
    } catch (err) {
      setResult({
        status: 'error',
        reason: err.response?.data?.detail || 'Trade execution failed'
      });
    } finally {
      setExecuting(false);
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">⚡ Quick Trade</h3>
        <span className="badge badge-warning">Paper Trading</span>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <label style={{ 
          display: 'block',
          fontSize: '13px',
          fontWeight: 600,
          color: '#94a3b8',
          marginBottom: '8px'
        }}>
          Symbol
        </label>
        <input
          type="text"
          value={symbol}
          onChange={(e) => setSymbol(e.target.value.toUpperCase())}
          placeholder="Enter symbol (e.g., AAPL)"
          style={{
            width: '100%',
            padding: '12px',
            background: 'rgba(15, 23, 42, 0.5)',
            border: '1px solid rgba(148, 163, 184, 0.2)',
            borderRadius: '8px',
            color: '#f1f5f9',
            fontSize: '14px'
          }}
          onKeyPress={(e) => e.key === 'Enter' && executeTrade()}
        />
      </div>

      <button
        className="btn btn-primary"
        onClick={executeTrade}
        disabled={executing || !symbol}
        style={{
          width: '100%',
          padding: '14px',
          fontSize: '16px',
          fontWeight: 700
        }}
      >
        {executing ? '⏳ Analyzing & Executing...' : '🚀 Execute AI Trade'}
      </button>

      {result && (
        <div
          className="fade-in"
          style={{
            marginTop: '20px',
            padding: '15px',
            background: result.status === 'success' 
              ? 'rgba(74, 222, 128, 0.1)' 
              : result.status === 'rejected'
              ? 'rgba(251, 191, 36, 0.1)'
              : 'rgba(248, 113, 113, 0.1)',
            border: `1px solid ${
              result.status === 'success' 
                ? 'rgba(74, 222, 128, 0.3)' 
                : result.status === 'rejected'
                ? 'rgba(251, 191, 36, 0.3)'
                : 'rgba(248, 113, 113, 0.3)'
            }`,
            borderRadius: '8px'
          }}
        >
          <div style={{ fontWeight: 600, marginBottom: '8px' }}>
            {result.status === 'success' && '✅ Trade Executed Successfully'}
            {result.status === 'rejected' && '⚠️ Trade Rejected'}
            {result.status === 'skipped' && 'ℹ️ Trade Skipped'}
            {result.status === 'error' && '❌ Error'}
          </div>
          <div style={{ fontSize: '13px', color: '#cbd5e1' }}>
            {result.reason || 'Trade completed'}
          </div>
          {result.order && (
            <div style={{ marginTop: '10px', fontSize: '13px' }}>
              <div>Symbol: <strong>{result.order.symbol}</strong></div>
              <div>Side: <strong style={{ 
                color: result.order.side === 'buy' ? '#4ade80' : '#f87171'
              }}>{result.order.side?.toUpperCase()}</strong></div>
              <div>Quantity: <strong>{result.order.quantity}</strong></div>
              <div>Price: <strong>${result.order.filled_avg_price?.toFixed(2)}</strong></div>
            </div>
          )}
          {result.risks && result.risks.length > 0 && (
            <div style={{ marginTop: '10px' }}>
              <div style={{ fontSize: '12px', fontWeight: 600, marginBottom: '4px' }}>
                Risk Concerns:
              </div>
              <ul style={{ fontSize: '12px', marginLeft: '20px', color: '#cbd5e1' }}>
                {result.risks.map((risk, i) => (
                  <li key={i}>{risk}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      <div style={{ 
        marginTop: '20px',
        padding: '12px',
        background: 'rgba(96, 165, 250, 0.1)',
        border: '1px solid rgba(96, 165, 250, 0.2)',
        borderRadius: '8px',
        fontSize: '12px',
        color: '#cbd5e1'
      }}>
        <div style={{ fontWeight: 600, marginBottom: '4px' }}>ℹ️ How it works:</div>
        <ol style={{ marginLeft: '20px', lineHeight: '1.6' }}>
          <li>AI agents analyze market data, news, and technical indicators</li>
          <li>Multi-agent consensus determines trade recommendation</li>
          <li>Risk manager validates the trade</li>
          <li>Order executes automatically if approved</li>
        </ol>
      </div>
    </div>
  );
}

export default TradingPanel;
