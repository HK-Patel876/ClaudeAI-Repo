import React from 'react';

function SystemMetrics({ metrics }) {
  if (!metrics) return null;

  const metricsData = [
    { label: 'Active Positions', value: metrics.active_positions, icon: '💼', color: '#60a5fa' },
    { label: 'Open Orders', value: metrics.open_orders, icon: '📋', color: '#a78bfa' },
    { label: 'Daily Trades', value: metrics.daily_trades, icon: '⚡', color: '#4ade80' },
    { label: 'Win Rate', value: `${(metrics.win_rate * 100).toFixed(1)}%`, icon: '🎯', color: '#fbbf24' },
  ];

  const systemData = [
    { label: 'CPU Usage', value: `${metrics.cpu_usage.toFixed(1)}%`, max: 100, color: '#60a5fa' },
    { label: 'Memory', value: `${metrics.memory_usage.toFixed(1)}%`, max: 100, color: '#a78bfa' },
    { label: 'API Latency', value: `${metrics.api_latency_ms.toFixed(1)}ms`, max: 100, color: '#4ade80' },
  ];

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">⚙️ System Metrics</h3>
        <span className="badge badge-success">Live</span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginBottom: '20px' }}>
        {metricsData.map((metric, index) => (
          <div
            key={index}
            style={{
              padding: '15px',
              background: 'rgba(15, 23, 42, 0.5)',
              borderRadius: '8px',
              border: '1px solid rgba(148, 163, 184, 0.1)'
            }}
          >
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '8px',
              marginBottom: '8px'
            }}>
              <span style={{ fontSize: '20px' }}>{metric.icon}</span>
              <span style={{ fontSize: '12px', color: '#94a3b8' }}>{metric.label}</span>
            </div>
            <div style={{ 
              fontSize: '24px', 
              fontWeight: 700,
              color: metric.color
            }}>
              {metric.value}
            </div>
          </div>
        ))}
      </div>

      <div style={{ marginTop: '20px' }}>
        <div style={{ 
          fontSize: '12px', 
          fontWeight: 600, 
          marginBottom: '15px',
          color: '#94a3b8',
          textTransform: 'uppercase',
          letterSpacing: '0.5px'
        }}>
          System Resources
        </div>
        {systemData.map((item, index) => (
          <div key={index} style={{ marginBottom: '15px' }}>
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between',
              marginBottom: '6px',
              fontSize: '13px'
            }}>
              <span>{item.label}</span>
              <span style={{ fontWeight: 600, color: item.color }}>{item.value}</span>
            </div>
            <div style={{ 
              background: 'rgba(148, 163, 184, 0.1)',
              height: '6px',
              borderRadius: '3px',
              overflow: 'hidden'
            }}>
              <div 
                style={{
                  background: item.color,
                  height: '100%',
                  width: `${Math.min((parseFloat(item.value) / item.max) * 100, 100)}%`,
                  transition: 'width 0.5s ease',
                  borderRadius: '3px'
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default SystemMetrics;
