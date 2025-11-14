import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

function PortfolioChart({ portfolio }) {
  // Generate demo historical data
  const historicalData = [];
  const startValue = 100000;
  let currentValue = startValue;
  
  for (let i = 0; i < 30; i++) {
    const change = (Math.random() - 0.48) * 1000;
    currentValue += change;
    historicalData.push({
      day: `Day ${i + 1}`,
      value: currentValue,
      pnl: currentValue - startValue
    });
  }

  // Prepare pie chart data
  const positionData = portfolio?.positions?.map((pos, index) => ({
    name: pos.symbol,
    value: pos.market_value,
    fill: ['#60a5fa', '#a78bfa', '#4ade80', '#fbbf24', '#f87171'][index % 5]
  })) || [];

  if (portfolio?.cash > 0) {
    positionData.push({
      name: 'Cash',
      value: portfolio.cash,
      fill: '#94a3b8'
    });
  }

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">📈 Portfolio Performance</h3>
        <div style={{ display: 'flex', gap: '10px' }}>
          <span className="badge badge-info">30 Days</span>
          <span className="badge badge-success">
            {portfolio?.total_pnl >= 0 ? '+' : ''}
            {((portfolio?.total_pnl / 100000) * 100)?.toFixed(2)}%
          </span>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px' }}>
        <div>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={historicalData}>
              <defs>
                <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#60a5fa" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#60a5fa" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" />
              <XAxis dataKey="day" stroke="#94a3b8" fontSize={12} />
              <YAxis stroke="#94a3b8" fontSize={12} />
              <Tooltip 
                contentStyle={{ 
                  background: 'rgba(30, 41, 59, 0.95)', 
                  border: '1px solid rgba(148, 163, 184, 0.2)',
                  borderRadius: '8px',
                  color: '#f1f5f9'
                }}
              />
              <Area 
                type="monotone" 
                dataKey="value" 
                stroke="#60a5fa" 
                strokeWidth={2}
                fill="url(#colorValue)" 
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div>
          <div style={{ marginBottom: '10px', fontSize: '14px', color: '#94a3b8', fontWeight: 600 }}>
            Asset Allocation
          </div>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={positionData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={2}
                dataKey="value"
              >
                {positionData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{ 
                  background: 'rgba(30, 41, 59, 0.95)', 
                  border: '1px solid rgba(148, 163, 184, 0.2)',
                  borderRadius: '8px',
                  color: '#f1f5f9'
                }}
                formatter={(value) => `$${value.toLocaleString()}`}
              />
            </PieChart>
          </ResponsiveContainer>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '10px' }}>
            {positionData.map((item, index) => (
              <div key={index} style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px' }}>
                <div style={{ width: '12px', height: '12px', borderRadius: '3px', background: item.fill }} />
                <span>{item.name}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default PortfolioChart;
