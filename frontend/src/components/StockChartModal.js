import React, { useState, useEffect } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import axios from 'axios';
import './StockChartModal.css';

const StockChartModal = ({ symbol, isOpen, onClose }) => {
  const [chartData, setChartData] = useState([]);
  const [timeframe, setTimeframe] = useState('1D');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!isOpen || !symbol) return;
    
    const loadData = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await axios.get(`/api/v1/data/market/${symbol}`, {
          params: { timeframe, limit: 100 }
        });
        
        if (response.data && Array.isArray(response.data)) {
          const formatted = response.data.map(d => ({
            time: new Date(d.timestamp).toLocaleString('en-US', { 
              month: 'short', 
              day: 'numeric',
              hour: '2-digit',
              minute: '2-digit'
            }),
            price: parseFloat(d.close),
            volume: d.volume,
            open: parseFloat(d.open),
            high: parseFloat(d.high),
            low: parseFloat(d.low)
          }));
          
          setChartData(formatted);
        } else {
          setError('No data available for this symbol');
        }
      } catch (error) {
        console.error('Error loading chart:', error);
        setError('Failed to load chart data. Please try again.');
      }
      setLoading(false);
    };
    
    loadData();
  }, [symbol, timeframe, isOpen]);

  if (!isOpen) return null;

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className="modal-overlay" onClick={handleOverlayClick}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{symbol} Chart</h2>
          <button onClick={onClose} className="close-button">×</button>
        </div>
        
        <div className="timeframe-buttons">
          {['1D', '1W', '1M', '3M', '1Y'].map(tf => (
            <button 
              key={tf}
              className={timeframe === tf ? 'active' : ''}
              onClick={() => setTimeframe(tf)}
            >
              {tf}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="loading">Loading chart...</div>
        ) : error ? (
          <div className="error-state">{error}</div>
        ) : chartData.length === 0 ? (
          <div className="loading">No data available</div>
        ) : (
          <ResponsiveContainer width="100%" height={400}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis 
                dataKey="time" 
                stroke="#999"
                tick={{ fill: '#999', fontSize: 12 }}
              />
              <YAxis 
                stroke="#999"
                tick={{ fill: '#999', fontSize: 12 }}
                domain={['auto', 'auto']}
                tickFormatter={(value) => `$${value.toFixed(2)}`}
              />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1a1a1a', 
                  border: '1px solid #333',
                  borderRadius: '6px',
                  color: '#fff'
                }}
                labelStyle={{ color: '#999' }}
                formatter={(value) => [`$${value.toFixed(2)}`, 'Price']}
              />
              <Area 
                type="monotone" 
                dataKey="price" 
                stroke="#3b82f6" 
                strokeWidth={2}
                fillOpacity={1} 
                fill="url(#colorPrice)" 
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
};

export default StockChartModal;
