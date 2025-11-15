import React from 'react';

function MarketBlotter({ marketData, onStockClick }) {
  const symbols = Object.keys(marketData || {});

  return (
    <div className="card animate-fade-in-up card-hover">
      <div className="card-header">
        <h3 className="card-title">📊 Live Market Blotter</h3>
        <span className="badge badge-success animate-pulse">Real-time</span>
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
            {symbols.map((symbol, index) => {
              const data = marketData[symbol];
              const change = data.change_pct || 0;
              const isPositive = change >= 0;

              return (
                <tr
                  key={symbol}
                  onClick={() => onStockClick && onStockClick(symbol)}
                  className="stagger-item hover-lift"
                  style={{
                    cursor: 'pointer',
                    animationDelay: `${index * 0.05}s`,
                    transition: 'all 0.3s ease'
                  }}
                  title={`Click to view ${symbol} chart`}
                >
                  <td style={{ fontWeight: 600 }}>{symbol}</td>
                  <td className="transition-all">${data.price?.toFixed(2)}</td>
                  <td
                    style={{
                      color: isPositive ? '#4ade80' : '#f87171',
                      fontWeight: 600
                    }}
                    className="transition-all"
                  >
                    {isPositive ? '+' : ''}{change.toFixed(2)}%
                  </td>
                  <td className="transition-all">{(data.volume / 1000000).toFixed(2)}M</td>
                  <td>
                    <span
                      style={{ fontSize: '20px' }}
                      className={isPositive ? 'animate-bounce' : ''}
                    >
                      {isPositive ? '📈' : '📉'}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      ) : (
        <div className="empty-state animate-fade-in">
          <div className="empty-state-icon animate-pulse">📊</div>
          <p>Waiting for market data...</p>
        </div>
      )}
    </div>
  );
}

export default MarketBlotter;
