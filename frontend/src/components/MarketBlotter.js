import React from 'react';

function MarketBlotter({ marketData, onStockClick }) {
  const symbols = Object.keys(marketData || {});

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">📊 Live Market Blotter</h3>
        <span className="badge badge-success">Real-time</span>
      </div>
      
      {symbols.length > 0 ? (
        <table className="table">
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Price</th>
              <th>Change</th>
              <th>Volume</th>
              <th>Trend</th>
            </tr>
          </thead>
          <tbody>
            {symbols.map(symbol => {
              const data = marketData[symbol];
              const change = data.change_pct || 0;
              const isPositive = change >= 0;
              
              return (
                <tr 
                  key={symbol}
                  onClick={() => onStockClick && onStockClick(symbol)}
                  style={{ cursor: 'pointer' }}
                  title={`Click to view ${symbol} chart`}
                >
                  <td style={{ fontWeight: 600 }}>{symbol}</td>
                  <td>${data.price?.toFixed(2)}</td>
                  <td style={{ color: isPositive ? '#4ade80' : '#f87171' }}>
                    {isPositive ? '+' : ''}{change.toFixed(2)}%
                  </td>
                  <td>{(data.volume / 1000000).toFixed(2)}M</td>
                  <td>
                    <span style={{ fontSize: '20px' }}>
                      {isPositive ? '📈' : '📉'}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      ) : (
        <div className="empty-state">
          <div className="empty-state-icon">📊</div>
          <p>Waiting for market data...</p>
        </div>
      )}
    </div>
  );
}

export default MarketBlotter;
