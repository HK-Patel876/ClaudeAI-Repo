import React, { useState, useEffect } from 'react';
import './styles/App.css';
import Dashboard from './components/Dashboard';
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
    <div className="app">
      <Dashboard connected={connected} />
    </div>
  );
}

export default App;
