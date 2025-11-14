import React from 'react';
import { tradingAPI } from '../services/api';

function OrdersGrid({ orders, onRefresh }) {
  const getStatusBadge = (status) => {
    const badges = {
      filled: 'badge-success',
      pending: 'badge-warning',
      open: 'badge-info',
      cancelled: 'badge-danger',
      rejected: 'badge-danger'
    };
    return badges[status] || 'badge-info';
  };

  const handleCancel = async (orderId) => {
    try {
      await tradingAPI.cancelOrder(orderId);
      onRefresh();
    } catch (err) {
      console.error('Error cancelling order:', err);
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">📋 Order History</h3>
        <span className="badge badge-info">{orders?.length || 0}</span>
      </div>

      {orders && orders.length > 0 ? (
        <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
          <table className="table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Symbol</th>
                <th>Side</th>
                <th>Qty</th>
                <th>Price</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((order, index) => (
                <tr key={index}>
                  <td style={{ fontSize: '12px' }}>
                    {new Date(order.created_at).toLocaleTimeString()}
                  </td>
                  <td style={{ fontWeight: 600 }}>{order.symbol}</td>
                  <td>
                    <span style={{ 
                      color: order.side === 'buy' ? '#4ade80' : '#f87171',
                      fontWeight: 600
                    }}>
                      {order.side?.toUpperCase()}
                    </span>
                  </td>
                  <td>{order.quantity}</td>
                  <td>${order.filled_avg_price?.toFixed(2) || order.price?.toFixed(2) || '-'}</td>
                  <td>
                    <span className={`badge ${getStatusBadge(order.status)}`}>
                      {order.status}
                    </span>
                  </td>
                  <td>
                    {(order.status === 'pending' || order.status === 'open') && (
                      <button
                        className="btn btn-danger"
                        style={{ padding: '4px 12px', fontSize: '12px' }}
                        onClick={() => handleCancel(order.id)}
                      >
                        Cancel
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="empty-state">
          <div className="empty-state-icon">📋</div>
          <p>No orders yet</p>
        </div>
      )}
    </div>
  );
}

export default OrdersGrid;
