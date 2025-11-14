import React from 'react';

function PositionsGrid({ positions }) {
  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">💼 Active Positions</h3>
        <span className="badge badge-info">{positions?.length || 0}</span>
      </div>

      {positions && positions.length > 0 ? (
        <table className="table">
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Qty</th>
              <th>Avg Price</th>
              <th>Current</th>
              <th>P&L</th>
              <th>Value</th>
            </tr>
          </thead>
          <tbody>
            {positions.map((position, index) => {
              const pnlPercent = ((position.current_price - position.avg_entry_price) / position.avg_entry_price) * 100;
              const isProfit = position.unrealized_pnl >= 0;
              
              return (
                <tr key={index}>
                  <td style={{ fontWeight: 600 }}>{position.symbol}</td>
                  <td>{position.quantity}</td>
                  <td>${position.avg_entry_price?.toFixed(2)}</td>
                  <td>${position.current_price?.toFixed(2)}</td>
                  <td style={{ color: isProfit ? '#4ade80' : '#f87171' }}>
                    {isProfit ? '+' : ''}${position.unrealized_pnl?.toFixed(2)}
                    <div style={{ fontSize: '11px', opacity: 0.8 }}>
                      ({isProfit ? '+' : ''}{pnlPercent.toFixed(2)}%)
                    </div>
                  </td>
                  <td>${position.market_value?.toFixed(2)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      ) : (
        <div className="empty-state">
          <div className="empty-state-icon">💼</div>
          <p>No active positions</p>
        </div>
      )}
    </div>
  );
}

export default PositionsGrid;
