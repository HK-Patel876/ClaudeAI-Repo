import React, { useState, useEffect } from 'react';
import { dataAPI } from '../services/api';

function NewsTicker() {
  const [news, setNews] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    loadNews();
    const interval = setInterval(loadNews, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (news.length > 0) {
      const interval = setInterval(() => {
        setCurrentIndex((prev) => (prev + 1) % news.length);
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [news]);

  const loadNews = async () => {
    try {
      const symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN'];
      const promises = symbols.map(symbol => dataAPI.getNews(symbol, 2));
      const results = await Promise.all(promises);
      const allNews = results.flatMap(r => r.data);
      setNews(allNews);
    } catch (err) {
      console.error('Error loading news:', err);
    }
  };

  const getSentimentColor = (score) => {
    if (score > 0.3) return '#4ade80';
    if (score < -0.3) return '#f87171';
    return '#94a3b8';
  };

  const getSentimentEmoji = (score) => {
    if (score > 0.5) return '🚀';
    if (score > 0.2) return '📈';
    if (score < -0.5) return '💥';
    if (score < -0.2) return '📉';
    return '📰';
  };

  if (news.length === 0) return null;

  const currentNews = news[currentIndex];

  return (
    <div className="card" style={{ 
      background: 'linear-gradient(135deg, rgba(96, 165, 250, 0.1), rgba(167, 139, 250, 0.1))',
      border: '1px solid rgba(96, 165, 250, 0.2)'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
        <div style={{
          fontSize: '32px',
          animation: 'fadeIn 0.5s ease-in'
        }}>
          {getSentimentEmoji(currentNews.sentiment_score || 0)}
        </div>
        
        <div style={{ flex: 1 }}>
          <div style={{ 
            fontSize: '16px', 
            fontWeight: 600, 
            marginBottom: '4px',
            animation: 'fadeIn 0.5s ease-in'
          }}>
            {currentNews.title}
          </div>
          <div style={{ 
            fontSize: '13px', 
            color: '#94a3b8',
            display: 'flex',
            gap: '15px',
            alignItems: 'center'
          }}>
            <span>{currentNews.source}</span>
            <span>•</span>
            <span>{new Date(currentNews.published_at).toLocaleTimeString()}</span>
            <span>•</span>
            <span style={{ 
              color: getSentimentColor(currentNews.sentiment_score || 0),
              fontWeight: 600
            }}>
              Sentiment: {currentNews.sentiment_score > 0 ? '+' : ''}
              {(currentNews.sentiment_score * 100)?.toFixed(0)}
            </span>
          </div>
        </div>

        <div style={{ 
          display: 'flex', 
          gap: '4px',
          alignItems: 'center'
        }}>
          {news.map((_, index) => (
            <div
              key={index}
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: index === currentIndex ? '#60a5fa' : 'rgba(148, 163, 184, 0.3)',
                transition: 'all 0.3s ease'
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

export default NewsTicker;
