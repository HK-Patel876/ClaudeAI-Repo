import React, { useState, useEffect } from 'react';
import { tradingAPI } from '../services/api';
import wsService from '../services/websocket';

function AgentInsights() {
  const [symbol, setSymbol] = useState('AAPL');
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [latestAnalysis, setLatestAnalysis] = useState(null);

  useEffect(() => {
    const unsubscribe = wsService.subscribe('ai_analysis', (data) => {
      setLatestAnalysis(data.data);
      
      if (data.data.symbol === symbol || !symbol) {
        const formattedAnalysis = {
          symbol: data.data.symbol,
          decision: data.data.decision?.toLowerCase() || 'hold',
          confidence: data.data.confidence || 0,
          agent_votes: data.data.agent_votes || [],
          risk_assessment: data.data.risk_assessment
        };
        setAnalysis(formattedAnalysis);
      }
    });

    return unsubscribe;
  }, [symbol]);

  const analyzeSymbol = async () => {
    if (!symbol) return;
    
    setLoading(true);
    try {
      const response = await tradingAPI.analyzeSymbol(symbol);
      setAnalysis(response.data);
    } catch (err) {
      console.error('Error analyzing symbol:', err);
    } finally {
      setLoading(false);
    }
  };

  const getSignalBadge = (signal) => {
    const badges = {
      strong_buy: 'badge-success',
      buy: 'badge-success',
      hold: 'badge-info',
      sell: 'badge-danger',
      strong_sell: 'badge-danger'
    };
    return badges[signal] || 'badge-info';
  };

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">🧠 AI Agent Insights</h3>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          {latestAnalysis && (
            <span className="badge badge-success" style={{ fontSize: '11px' }}>
              ● Live
            </span>
          )}
          <span className="badge badge-info">Multi-Agent</span>
        </div>
      </div>

      <div style={{ marginBottom: '20px', display: 'flex', gap: '10px' }}>
        <input
          type="text"
          value={symbol}
          onChange={(e) => setSymbol(e.target.value.toUpperCase())}
          placeholder="Enter symbol (e.g., AAPL)"
          style={{
            flex: 1,
            padding: '10px',
            background: 'rgba(15, 23, 42, 0.5)',
            border: '1px solid rgba(148, 163, 184, 0.2)',
            borderRadius: '8px',
            color: '#f1f5f9',
            fontSize: '14px'
          }}
          onKeyPress={(e) => e.key === 'Enter' && analyzeSymbol()}
        />
        <button 
          className="btn btn-primary"
          onClick={analyzeSymbol}
          disabled={loading}
        >
          {loading ? 'Analyzing...' : 'Analyze'}
        </button>
      </div>

      {analysis && (
        <div className="fade-in">
          <div style={{ 
            padding: '15px', 
            background: 'rgba(96, 165, 250, 0.1)', 
            borderRadius: '8px',
            marginBottom: '20px',
            border: '1px solid rgba(96, 165, 250, 0.2)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: '24px', fontWeight: 700 }}>{analysis.symbol}</div>
                <div style={{ color: '#94a3b8', fontSize: '14px' }}>
                  Decision: <span className={`badge ${getSignalBadge(analysis.decision)}`}>
                    {analysis.decision?.toUpperCase()}
                  </span>
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ color: '#94a3b8', fontSize: '12px' }}>Confidence</div>
                <div style={{ fontSize: '28px', fontWeight: 700, color: '#60a5fa' }}>
                  {(analysis.confidence * 100).toFixed(0)}%
                </div>
              </div>
            </div>
          </div>

          <div style={{ marginTop: '20px' }}>
            <div style={{ 
              fontSize: '14px', 
              fontWeight: 600, 
              marginBottom: '10px',
              color: '#94a3b8',
              textTransform: 'uppercase',
              letterSpacing: '0.5px'
            }}>
              Agent Votes
            </div>
            {analysis.agent_votes?.map((vote, index) => (
              <div 
                key={index}
                style={{
                  padding: '12px',
                  background: 'rgba(15, 23, 42, 0.5)',
                  borderRadius: '8px',
                  marginBottom: '10px',
                  border: '1px solid rgba(148, 163, 184, 0.1)'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span style={{ fontWeight: 600, textTransform: 'capitalize' }}>
                    {vote.agent === 'technical' && '📊'} 
                    {vote.agent === 'news' && '📰'} 
                    {vote.agent === 'fundamental' && '📈'} 
                    {vote.agent === 'risk' && '⚠️'} 
                    {' '}{vote.agent} Analyst
                  </span>
                  <span 
                    className={`badge ${getSignalBadge(vote.signal)}`}
                    style={{ fontSize: '11px' }}
                  >
                    {vote.signal?.replace('_', ' ').toUpperCase()}
                  </span>
                </div>
                <div style={{ fontSize: '13px', color: '#cbd5e1', marginBottom: '8px' }}>
                  {vote.reasoning}
                </div>
                <div style={{ 
                  background: 'rgba(96, 165, 250, 0.1)',
                  height: '4px',
                  borderRadius: '2px',
                  overflow: 'hidden'
                }}>
                  <div 
                    style={{
                      background: '#60a5fa',
                      height: '100%',
                      width: `${vote.confidence * 100}%`,
                      transition: 'width 0.5s ease'
                    }}
                  />
                </div>
                <div style={{ fontSize: '11px', color: '#64748b', marginTop: '4px' }}>
                  Confidence: {(vote.confidence * 100).toFixed(0)}%
                </div>
              </div>
            ))}
          </div>

          {analysis.risk_check && (
            <div style={{ marginTop: '20px' }}>
              <div style={{ 
                fontSize: '14px', 
                fontWeight: 600, 
                marginBottom: '10px',
                color: '#94a3b8',
                textTransform: 'uppercase',
                letterSpacing: '0.5px'
              }}>
                Risk Assessment
              </div>
              <div style={{
                padding: '12px',
                background: analysis.risk_check.approved 
                  ? 'rgba(74, 222, 128, 0.1)' 
                  : 'rgba(248, 113, 113, 0.1)',
                border: `1px solid ${analysis.risk_check.approved ? 'rgba(74, 222, 128, 0.3)' : 'rgba(248, 113, 113, 0.3)'}`,
                borderRadius: '8px'
              }}>
                <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px' }}>
                  {analysis.risk_check.approved ? '✅ Trade Approved' : '⛔ Trade Rejected'}
                </div>
                {analysis.risk_check.risks?.length > 0 && (
                  <ul style={{ fontSize: '13px', color: '#cbd5e1', marginLeft: '20px' }}>
                    {analysis.risk_check.risks.map((risk, i) => (
                      <li key={i}>{risk}</li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default AgentInsights;
