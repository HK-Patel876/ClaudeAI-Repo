import React, { useState, useEffect } from 'react';
import api from '../services/api';
import wsService from '../services/websocket';

function AgentLog() {
  const [analyses, setAnalyses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [liveAnalyses, setLiveAnalyses] = useState([]);

  useEffect(() => {
    loadAnalyses();
    const interval = setInterval(loadAnalyses, 10000);
    return () => clearInterval(interval);
  }, [filter]);

  useEffect(() => {
    const unsubscribe = wsService.subscribe('ai_analysis', (data) => {
      const analysis = data.data;
      
      if (analysis.agent_votes) {
        const formattedAnalyses = analysis.agent_votes.map(vote => ({
          symbol: analysis.symbol,
          timestamp: analysis.timestamp || new Date().toISOString(),
          agent_type: vote.agent,
          signal: vote.signal,
          confidence: vote.confidence,
          reasoning: vote.reasoning
        }));
        
        setLiveAnalyses(prev => [...formattedAnalyses, ...prev].slice(0, 50));
      } else {
        setLiveAnalyses(prev => [{
          symbol: analysis.symbol,
          timestamp: analysis.timestamp || new Date().toISOString(),
          agent_type: 'AI',
          signal: analysis.decision || 'HOLD',
          confidence: analysis.confidence || 0,
          reasoning: analysis.reasoning || 'Analysis completed'
        }, ...prev].slice(0, 50));
      }
    });

    return unsubscribe;
  }, []);

  const loadAnalyses = async () => {
    try {
      const params = filter !== 'all' ? `?agent_type=${filter}` : '';
      const response = await api.get(`/analyses${params}`);
      setAnalyses(response.data.data || []);
      setLoading(false);
    } catch (err) {
      console.error('Error loading analyses:', err);
      setLoading(false);
    }
  };

  const getSignalBadge = (signal) => {
    const badges = {
      'STRONG_BUY': 'badge-success',
      'BUY': 'badge-success',
      'HOLD': 'badge-warning',
      'SELL': 'badge-danger',
      'STRONG_SELL': 'badge-danger'
    };
    return badges[signal] || 'badge-info';
  };

  const getAgentIcon = (agentType) => {
    const icons = {
      'TECHNICAL': '📊',
      'NEWS': '📰',
      'FUNDAMENTAL': '💼',
      'RISK': '⚠️'
    };
    return icons[agentType] || '🤖';
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      second: '2-digit'
    });
  };

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">🤖 Live Agent Log</h3>
        <div className="agent-filter">
          <select value={filter} onChange={e => setFilter(e.target.value)}>
            <option value="all">All Agents</option>
            <option value="TECHNICAL">Technical</option>
            <option value="NEWS">News</option>
            <option value="FUNDAMENTAL">Fundamental</option>
            <option value="RISK">Risk</option>
          </select>
        </div>
      </div>

      <div className="agent-log-content">
        {loading && liveAnalyses.length === 0 ? (
          <div className="loading">Loading agent analyses...</div>
        ) : (liveAnalyses.length === 0 && analyses.length === 0) ? (
          <div className="empty-state">
            <p>No agent analyses yet</p>
            <p style={{ fontSize: '12px', color: '#94a3b8', marginTop: '10px' }}>
              AI analysis will appear here automatically
            </p>
          </div>
        ) : (
          <div className="timeline">
            {liveAnalyses.length > 0 && (
              <div style={{ 
                padding: '10px', 
                background: 'rgba(34, 197, 94, 0.1)', 
                borderRadius: '4px',
                marginBottom: '15px',
                fontSize: '12px',
                color: '#4ade80',
                textAlign: 'center'
              }}>
                ✓ Live AI Analysis Active ({liveAnalyses.length} recent)
              </div>
            )}
            {[...liveAnalyses, ...analyses].slice(0, 20).map((analysis, index) => {
              const isLive = index < liveAnalyses.length;
              return (
                <div 
                  key={analysis.id || `${analysis.symbol}-${index}`} 
                  className="timeline-item"
                  style={isLive ? { 
                    animation: 'slideIn 0.3s ease-out',
                    background: 'rgba(96, 165, 250, 0.05)'
                  } : {}}
                >
                  <div className="timeline-time">
                    {isLive && <span style={{ color: '#4ade80', marginRight: '5px' }}>●</span>}
                    {formatTimestamp(analysis.timestamp)}
                  </div>
                  <div className="timeline-content">
                    <div className="analysis-header">
                      <span className="agent-icon">{getAgentIcon(analysis.agent_type)}</span>
                      <strong>{analysis.symbol}</strong>
                      <span className={`badge ${getSignalBadge(analysis.signal)}`}>
                        {analysis.signal.replace('_', ' ')}
                      </span>
                      <span className="confidence">
                        {(analysis.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="analysis-reasoning">
                      {analysis.reasoning}
                    </div>
                    <div className="analysis-meta">
                      <span className="agent-type">{analysis.agent_type}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

export default AgentLog;
