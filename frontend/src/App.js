import React, { useState, useEffect } from 'react';
import './styles/App.css';
import Dashboard from './components/Dashboard';
import ErrorBoundary from './components/ErrorBoundary';
import wsService from './services/websocket';

function App() {
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    wsService.connect();

    const unsubscribe = wsService.subscribe('pong', () => {
      setConnected(true);
    });

    return () => {
      unsubscribe();
      wsService.disconnect();
    };
  }, []);

  return (
    <ErrorBoundary>
      <div className="app">
        <Dashboard connected={connected} />
      </div>
    </ErrorBoundary>
  );
}

export default App;
