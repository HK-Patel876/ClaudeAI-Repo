import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Calculator,
  BarChart3,
  Target,
  Activity,
  DollarSign,
  Clock,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Info,
  RefreshCw,
  Settings
} from 'lucide-react';
import api from '../services/api';
import soundService from '../services/soundService';

const OptionsAnalytics = ({ defaultSymbol = 'AAPL' }) => {
  // State management
  const [symbol, setSymbol] = useState(defaultSymbol);
  const [optionsChain, setOptionsChain] = useState([]);
  const [selectedOption, setSelectedOption] = useState(null);
  const [selectedExpiry, setSelectedExpiry] = useState(null);
  const [expirationDates, setExpirationDates] = useState([]);
  const [greeks, setGreeks] = useState(null);
  const [strategy, setStrategy] = useState('single');
  const [strategyLegs, setStrategyLegs] = useState([]);
  const [currentPrice, setCurrentPrice] = useState(0);
  const [loading, setLoading] = useState(false);
  const [view, setView] = useState('chain'); // chain, greeks, strategy, calculator
  const [calculatorInputs, setCalculatorInputs] = useState({
    strike: 150,
    spot: 150,
    volatility: 0.25,
    riskFreeRate: 0.05,
    timeToExpiry: 30,
    optionType: 'call'
  });

  // Predefined strategies
  const strategies = [
    { id: 'single', name: 'Single Option', description: 'Buy or sell a single option' },
    { id: 'covered_call', name: 'Covered Call', description: 'Long stock + Short call' },
    { id: 'protective_put', name: 'Protective Put', description: 'Long stock + Long put' },
    { id: 'bull_call_spread', name: 'Bull Call Spread', description: 'Long lower strike call + Short higher strike call' },
    { id: 'bear_put_spread', name: 'Bear Put Spread', description: 'Long higher strike put + Short lower strike put' },
    { id: 'long_straddle', name: 'Long Straddle', description: 'Long call + Long put at same strike' },
    { id: 'long_strangle', name: 'Long Strangle', description: 'Long OTM call + Long OTM put' },
    { id: 'iron_condor', name: 'Iron Condor', description: 'Bull put spread + Bear call spread' },
    { id: 'butterfly', name: 'Butterfly Spread', description: 'Buy 1 low strike, Sell 2 mid strike, Buy 1 high strike' }
  ];

  // Load current price
  useEffect(() => {
    loadCurrentPrice();
    const interval = setInterval(loadCurrentPrice, 5000);
    return () => clearInterval(interval);
  }, [symbol]);

  // Load options chain
  useEffect(() => {
    if (symbol) {
      loadOptionsChain();
    }
  }, [symbol, selectedExpiry]);

  const loadCurrentPrice = async () => {
    try {
      const response = await api.get(`/data/price/${symbol}`);
      if (response.data && response.data.price) {
        setCurrentPrice(response.data.price);
        setCalculatorInputs(prev => ({ ...prev, spot: response.data.price }));
      }
    } catch (error) {
      console.error('Error loading current price:', error);
    }
  };

  const loadOptionsChain = async () => {
    setLoading(true);
    try {
      // Simulated options chain data (in production, this would come from your API)
      const mockChain = generateMockOptionsChain(currentPrice, selectedExpiry);
      setOptionsChain(mockChain);

      // Generate expiration dates
      const expirations = generateExpirationDates();
      setExpirationDates(expirations);

      if (!selectedExpiry && expirations.length > 0) {
        setSelectedExpiry(expirations[0]);
      }
    } catch (error) {
      console.error('Error loading options chain:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateExpirationDates = () => {
    const dates = [];
    const today = new Date();

    // Weekly expirations for next 4 weeks
    for (let i = 1; i <= 4; i++) {
      const date = new Date(today);
      date.setDate(date.getDate() + (i * 7));
      dates.push(formatDate(date));
    }

    // Monthly expirations for next 6 months
    for (let i = 1; i <= 6; i++) {
      const date = new Date(today);
      date.setMonth(date.getMonth() + i);
      date.setDate(15); // 3rd Friday approximation
      dates.push(formatDate(date));
    }

    return dates;
  };

  const formatDate = (date) => {
    return date.toISOString().split('T')[0];
  };

  const generateMockOptionsChain = (spot, expiry) => {
    if (!spot || spot === 0) spot = 150;

    const chain = [];
    const strikes = [];

    // Generate strikes around current price
    const step = spot > 100 ? 5 : spot > 50 ? 2.5 : 1;
    for (let i = -10; i <= 10; i++) {
      strikes.push(Math.round((spot + (i * step)) * 100) / 100);
    }

    const daysToExpiry = expiry ? calculateDaysToExpiry(expiry) : 30;
    const timeToExpiry = daysToExpiry / 365;

    strikes.forEach(strike => {
      const isITM_Call = spot > strike;
      const isITM_Put = spot < strike;

      // Black-Scholes approximation for demo
      const call = calculateOptionPrice(spot, strike, timeToExpiry, 0.25, 0.05, 'call');
      const put = calculateOptionPrice(spot, strike, timeToExpiry, 0.25, 0.05, 'put');

      chain.push({
        strike: strike,
        call: {
          bid: call.price * 0.98,
          ask: call.price * 1.02,
          last: call.price,
          volume: Math.floor(Math.random() * 1000),
          openInterest: Math.floor(Math.random() * 5000),
          impliedVolatility: 0.25 + (Math.random() * 0.1 - 0.05),
          delta: call.greeks.delta,
          gamma: call.greeks.gamma,
          theta: call.greeks.theta,
          vega: call.greeks.vega,
          rho: call.greeks.rho,
          inTheMoney: isITM_Call
        },
        put: {
          bid: put.price * 0.98,
          ask: put.price * 1.02,
          last: put.price,
          volume: Math.floor(Math.random() * 1000),
          openInterest: Math.floor(Math.random() * 5000),
          impliedVolatility: 0.25 + (Math.random() * 0.1 - 0.05),
          delta: put.greeks.delta,
          gamma: put.greeks.gamma,
          theta: put.greeks.theta,
          vega: put.greeks.vega,
          rho: put.greeks.rho,
          inTheMoney: isITM_Put
        }
      });
    });

    return chain;
  };

  const calculateDaysToExpiry = (expiryDate) => {
    const today = new Date();
    const expiry = new Date(expiryDate);
    const diffTime = expiry - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return Math.max(1, diffDays);
  };

  // Black-Scholes option pricing (simplified)
  const calculateOptionPrice = (S, K, T, sigma, r, type) => {
    if (T <= 0) T = 0.001;

    const d1 = (Math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * Math.sqrt(T));
    const d2 = d1 - sigma * Math.sqrt(T);

    const normCDF = (x) => {
      const t = 1 / (1 + 0.2316419 * Math.abs(x));
      const d = 0.3989423 * Math.exp(-x * x / 2);
      const prob = d * t * (0.3193815 + t * (-0.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274))));
      return x > 0 ? 1 - prob : prob;
    };

    const normPDF = (x) => {
      return Math.exp(-0.5 * x * x) / Math.sqrt(2 * Math.PI);
    };

    let price, delta, gamma, theta, vega, rho;

    if (type === 'call') {
      price = S * normCDF(d1) - K * Math.exp(-r * T) * normCDF(d2);
      delta = normCDF(d1);
      gamma = normPDF(d1) / (S * sigma * Math.sqrt(T));
      theta = -(S * normPDF(d1) * sigma) / (2 * Math.sqrt(T)) - r * K * Math.exp(-r * T) * normCDF(d2);
      vega = S * normPDF(d1) * Math.sqrt(T);
      rho = K * T * Math.exp(-r * T) * normCDF(d2);
    } else {
      price = K * Math.exp(-r * T) * normCDF(-d2) - S * normCDF(-d1);
      delta = -normCDF(-d1);
      gamma = normPDF(d1) / (S * sigma * Math.sqrt(T));
      theta = -(S * normPDF(d1) * sigma) / (2 * Math.sqrt(T)) + r * K * Math.exp(-r * T) * normCDF(-d2);
      vega = S * normPDF(d1) * Math.sqrt(T);
      rho = -K * T * Math.exp(-r * T) * normCDF(-d2);
    }

    return {
      price: Math.max(0, price),
      greeks: {
        delta: delta,
        gamma: gamma,
        theta: theta / 365, // Per day
        vega: vega / 100, // Per 1% change in volatility
        rho: rho / 100 // Per 1% change in interest rate
      }
    };
  };

  const selectOption = (strike, type) => {
    const option = optionsChain.find(o => o.strike === strike);
    if (option) {
      const selected = {
        symbol: symbol,
        strike: strike,
        type: type,
        expiry: selectedExpiry,
        ...option[type]
      };
      setSelectedOption(selected);
      setGreeks(option[type]);
      soundService.playClick();
    }
  };

  const addToStrategy = (strike, type, action) => {
    const option = optionsChain.find(o => o.strike === strike);
    if (option) {
      const leg = {
        id: Date.now(),
        symbol: symbol,
        strike: strike,
        type: type,
        action: action, // buy or sell
        expiry: selectedExpiry,
        quantity: 1,
        price: option[type].last,
        ...option[type]
      };
      setStrategyLegs([...strategyLegs, leg]);
      soundService.playTradeExecuted();
    }
  };

  const removeStrategyLeg = (id) => {
    setStrategyLegs(strategyLegs.filter(leg => leg.id !== id));
  };

  const calculateStrategyPnL = () => {
    if (strategyLegs.length === 0) return [];

    const pnlData = [];
    const minStrike = Math.min(...strategyLegs.map(l => l.strike));
    const maxStrike = Math.max(...strategyLegs.map(l => l.strike));
    const range = maxStrike - minStrike;
    const step = range / 50;

    for (let price = minStrike - range * 0.2; price <= maxStrike + range * 0.2; price += step) {
      let totalPnL = 0;

      strategyLegs.forEach(leg => {
        let legPnL = 0;

        if (leg.type === 'call') {
          const intrinsic = Math.max(0, price - leg.strike);
          legPnL = intrinsic - leg.price;
        } else {
          const intrinsic = Math.max(0, leg.strike - price);
          legPnL = intrinsic - leg.price;
        }

        legPnL *= leg.quantity * 100; // Contract multiplier
        if (leg.action === 'sell') legPnL *= -1;

        totalPnL += legPnL;
      });

      pnlData.push({ price: price, pnl: totalPnL });
    }

    return pnlData;
  };

  const calculateGreeksFromInputs = () => {
    const { strike, spot, volatility, riskFreeRate, timeToExpiry, optionType } = calculatorInputs;
    const T = timeToExpiry / 365;
    const result = calculateOptionPrice(spot, strike, T, volatility, riskFreeRate, optionType);
    return { price: result.price, ...result.greeks };
  };

  const applyStrategy = (strategyId) => {
    setStrategy(strategyId);
    setStrategyLegs([]);

    // Pre-populate strategy legs based on strategy type
    if (!currentPrice) return;

    const atm = Math.round(currentPrice / 5) * 5;

    switch (strategyId) {
      case 'covered_call':
        addToStrategy(atm + 5, 'call', 'sell');
        break;
      case 'protective_put':
        addToStrategy(atm - 5, 'put', 'buy');
        break;
      case 'bull_call_spread':
        addToStrategy(atm, 'call', 'buy');
        addToStrategy(atm + 10, 'call', 'sell');
        break;
      case 'bear_put_spread':
        addToStrategy(atm, 'put', 'buy');
        addToStrategy(atm - 10, 'put', 'sell');
        break;
      case 'long_straddle':
        addToStrategy(atm, 'call', 'buy');
        addToStrategy(atm, 'put', 'buy');
        break;
      case 'long_strangle':
        addToStrategy(atm + 5, 'call', 'buy');
        addToStrategy(atm - 5, 'put', 'buy');
        break;
      case 'iron_condor':
        addToStrategy(atm - 10, 'put', 'buy');
        addToStrategy(atm - 5, 'put', 'sell');
        addToStrategy(atm + 5, 'call', 'sell');
        addToStrategy(atm + 10, 'call', 'buy');
        break;
      case 'butterfly':
        addToStrategy(atm - 5, 'call', 'buy');
        addToStrategy(atm, 'call', 'sell');
        addToStrategy(atm, 'call', 'sell');
        addToStrategy(atm + 5, 'call', 'buy');
        break;
      default:
        break;
    }
  };

  const pnlData = calculateStrategyPnL();
  const calculatedGreeks = view === 'calculator' ? calculateGreeksFromInputs() : null;

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.headerLeft}>
          <Activity size={24} style={{ color: '#00d4ff' }} />
          <h2 style={styles.title}>Options Analytics</h2>
        </div>

        <div style={styles.headerRight}>
          <input
            type="text"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            placeholder="Symbol"
            style={styles.symbolInput}
            maxLength={10}
          />

          <select
            value={selectedExpiry || ''}
            onChange={(e) => setSelectedExpiry(e.target.value)}
            style={styles.expirySelect}
          >
            <option value="">Select Expiry</option>
            {expirationDates.map(date => (
              <option key={date} value={date}>
                {new Date(date).toLocaleDateString()} ({calculateDaysToExpiry(date)}d)
              </option>
            ))}
          </select>

          <button onClick={loadOptionsChain} style={styles.refreshBtn}>
            <RefreshCw size={18} />
          </button>
        </div>
      </div>

      {/* Current Price Banner */}
      <div style={styles.priceBanner}>
        <div>
          <span style={styles.priceLabel}>{symbol} Current Price:</span>
          <span style={styles.priceValue}>${currentPrice.toFixed(2)}</span>
        </div>
        {selectedExpiry && (
          <div>
            <span style={styles.priceLabel}>Days to Expiry:</span>
            <span style={styles.priceValue}>{calculateDaysToExpiry(selectedExpiry)}</span>
          </div>
        )}
      </div>

      {/* View Tabs */}
      <div style={styles.tabs}>
        <button
          style={{...styles.tab, ...(view === 'chain' ? styles.tabActive : {})}}
          onClick={() => setView('chain')}
        >
          <BarChart3 size={18} />
          <span>Options Chain</span>
        </button>
        <button
          style={{...styles.tab, ...(view === 'greeks' ? styles.tabActive : {})}}
          onClick={() => setView('greeks')}
        >
          <TrendingUp size={18} />
          <span>Greeks Analysis</span>
        </button>
        <button
          style={{...styles.tab, ...(view === 'strategy' ? styles.tabActive : {})}}
          onClick={() => setView('strategy')}
        >
          <Target size={18} />
          <span>Strategy Builder</span>
        </button>
        <button
          style={{...styles.tab, ...(view === 'calculator' ? styles.tabActive : {})}}
          onClick={() => setView('calculator')}
        >
          <Calculator size={18} />
          <span>Greeks Calculator</span>
        </button>
      </div>

      {/* Content Area */}
      <div style={styles.content}>
        {/* Options Chain View */}
        {view === 'chain' && (
          <div style={styles.chainView}>
            <div style={styles.chainHeader}>
              <div style={styles.chainHeaderSection}>
                <h3 style={styles.chainTitle}>CALLS</h3>
              </div>
              <div style={styles.chainHeaderSection}>
                <h3 style={styles.chainTitle}>STRIKE</h3>
              </div>
              <div style={styles.chainHeaderSection}>
                <h3 style={styles.chainTitle}>PUTS</h3>
              </div>
            </div>

            <div style={styles.chainTable}>
              {loading ? (
                <div style={styles.loading}>Loading options chain...</div>
              ) : (
                optionsChain.map((option, index) => (
                  <div
                    key={index}
                    style={{
                      ...styles.chainRow,
                      ...(Math.abs(option.strike - currentPrice) < 5 ? styles.atmRow : {})
                    }}
                  >
                    {/* Call Side */}
                    <div
                      style={{...styles.chainCell, ...styles.callCell}}
                      onClick={() => selectOption(option.strike, 'call')}
                    >
                      <div style={styles.optionDetails}>
                        <div style={styles.optionPrices}>
                          <span style={styles.bid}>{option.call.bid.toFixed(2)}</span>
                          <span style={styles.last}>{option.call.last.toFixed(2)}</span>
                          <span style={styles.ask}>{option.call.ask.toFixed(2)}</span>
                        </div>
                        <div style={styles.optionMeta}>
                          <span>Vol: {option.call.volume}</span>
                          <span>IV: {(option.call.impliedVolatility * 100).toFixed(1)}%</span>
                          <span>Δ: {option.call.delta.toFixed(3)}</span>
                        </div>
                      </div>
                      {option.call.inTheMoney && <div style={styles.itmBadge}>ITM</div>}
                    </div>

                    {/* Strike */}
                    <div style={styles.strikeCell}>
                      <span style={styles.strikePrice}>${option.strike.toFixed(2)}</span>
                    </div>

                    {/* Put Side */}
                    <div
                      style={{...styles.chainCell, ...styles.putCell}}
                      onClick={() => selectOption(option.strike, 'put')}
                    >
                      <div style={styles.optionDetails}>
                        <div style={styles.optionPrices}>
                          <span style={styles.bid}>{option.put.bid.toFixed(2)}</span>
                          <span style={styles.last}>{option.put.last.toFixed(2)}</span>
                          <span style={styles.ask}>{option.put.ask.toFixed(2)}</span>
                        </div>
                        <div style={styles.optionMeta}>
                          <span>Vol: {option.put.volume}</span>
                          <span>IV: {(option.put.impliedVolatility * 100).toFixed(1)}%</span>
                          <span>Δ: {option.put.delta.toFixed(3)}</span>
                        </div>
                      </div>
                      {option.put.inTheMoney && <div style={styles.itmBadge}>ITM</div>}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* Greeks Analysis View */}
        {view === 'greeks' && (
          <div style={styles.greeksView}>
            {selectedOption ? (
              <>
                <div style={styles.selectedOption}>
                  <h3 style={styles.sectionTitle}>
                    {symbol} ${selectedOption.strike} {selectedOption.type.toUpperCase()}
                  </h3>
                  <p style={styles.expiryText}>Expires: {new Date(selectedOption.expiry).toLocaleDateString()}</p>
                </div>

                <div style={styles.greeksGrid}>
                  <div style={styles.greekCard}>
                    <div style={styles.greekHeader}>
                      <TrendingUp size={20} style={{ color: '#00d4ff' }} />
                      <span style={styles.greekName}>Delta (Δ)</span>
                    </div>
                    <div style={styles.greekValue}>{selectedOption.delta.toFixed(4)}</div>
                    <div style={styles.greekDescription}>
                      Price change per $1 move in underlying
                    </div>
                  </div>

                  <div style={styles.greekCard}>
                    <div style={styles.greekHeader}>
                      <Activity size={20} style={{ color: '#ff00ff' }} />
                      <span style={styles.greekName}>Gamma (Γ)</span>
                    </div>
                    <div style={styles.greekValue}>{selectedOption.gamma.toFixed(4)}</div>
                    <div style={styles.greekDescription}>
                      Delta change per $1 move in underlying
                    </div>
                  </div>

                  <div style={styles.greekCard}>
                    <div style={styles.greekHeader}>
                      <Clock size={20} style={{ color: '#ff6b00' }} />
                      <span style={styles.greekName}>Theta (Θ)</span>
                    </div>
                    <div style={styles.greekValue}>{selectedOption.theta.toFixed(4)}</div>
                    <div style={styles.greekDescription}>
                      Price decay per day
                    </div>
                  </div>

                  <div style={styles.greekCard}>
                    <div style={styles.greekHeader}>
                      <BarChart3 size={20} style={{ color: '#00ff88' }} />
                      <span style={styles.greekName}>Vega (ν)</span>
                    </div>
                    <div style={styles.greekValue}>{selectedOption.vega.toFixed(4)}</div>
                    <div style={styles.greekDescription}>
                      Price change per 1% volatility change
                    </div>
                  </div>

                  <div style={styles.greekCard}>
                    <div style={styles.greekHeader}>
                      <DollarSign size={20} style={{ color: '#ffdd00' }} />
                      <span style={styles.greekName}>Rho (ρ)</span>
                    </div>
                    <div style={styles.greekValue}>{selectedOption.rho.toFixed(4)}</div>
                    <div style={styles.greekDescription}>
                      Price change per 1% interest rate change
                    </div>
                  </div>

                  <div style={styles.greekCard}>
                    <div style={styles.greekHeader}>
                      <Info size={20} style={{ color: '#ffffff' }} />
                      <span style={styles.greekName}>Implied Volatility</span>
                    </div>
                    <div style={styles.greekValue}>
                      {(selectedOption.impliedVolatility * 100).toFixed(2)}%
                    </div>
                    <div style={styles.greekDescription}>
                      Market's expectation of volatility
                    </div>
                  </div>
                </div>

                <div style={styles.optionInfo}>
                  <div style={styles.infoRow}>
                    <span>Last Price:</span>
                    <span style={styles.infoValue}>${selectedOption.last.toFixed(2)}</span>
                  </div>
                  <div style={styles.infoRow}>
                    <span>Bid/Ask:</span>
                    <span style={styles.infoValue}>
                      ${selectedOption.bid.toFixed(2)} / ${selectedOption.ask.toFixed(2)}
                    </span>
                  </div>
                  <div style={styles.infoRow}>
                    <span>Volume:</span>
                    <span style={styles.infoValue}>{selectedOption.volume.toLocaleString()}</span>
                  </div>
                  <div style={styles.infoRow}>
                    <span>Open Interest:</span>
                    <span style={styles.infoValue}>{selectedOption.openInterest.toLocaleString()}</span>
                  </div>
                  <div style={styles.infoRow}>
                    <span>Status:</span>
                    <span style={{
                      ...styles.infoValue,
                      color: selectedOption.inTheMoney ? '#00ff88' : '#ff6b6b'
                    }}>
                      {selectedOption.inTheMoney ? 'In The Money' : 'Out of The Money'}
                    </span>
                  </div>
                </div>
              </>
            ) : (
              <div style={styles.emptyState}>
                <Info size={48} style={{ color: '#666', marginBottom: '20px' }} />
                <p>Select an option from the chain to view Greeks analysis</p>
              </div>
            )}
          </div>
        )}

        {/* Strategy Builder View */}
        {view === 'strategy' && (
          <div style={styles.strategyView}>
            <div style={styles.strategySelector}>
              <h3 style={styles.sectionTitle}>Select Strategy</h3>
              <div style={styles.strategyGrid}>
                {strategies.map(strat => (
                  <button
                    key={strat.id}
                    style={{
                      ...styles.strategyCard,
                      ...(strategy === strat.id ? styles.strategyCardActive : {})
                    }}
                    onClick={() => applyStrategy(strat.id)}
                  >
                    <div style={styles.strategyName}>{strat.name}</div>
                    <div style={styles.strategyDescription}>{strat.description}</div>
                  </button>
                ))}
              </div>
            </div>

            <div style={styles.strategyLegs}>
              <div style={styles.legsHeader}>
                <h3 style={styles.sectionTitle}>Strategy Legs</h3>
                <button style={styles.clearBtn} onClick={() => setStrategyLegs([])}>
                  Clear All
                </button>
              </div>

              {strategyLegs.length === 0 ? (
                <div style={styles.emptyLegs}>
                  <p>No strategy legs added. Select a strategy above or add legs manually from the options chain.</p>
                </div>
              ) : (
                <div style={styles.legsList}>
                  {strategyLegs.map(leg => (
                    <div key={leg.id} style={styles.legItem}>
                      <div style={styles.legInfo}>
                        <span style={{
                          ...styles.legAction,
                          color: leg.action === 'buy' ? '#00ff88' : '#ff6b6b'
                        }}>
                          {leg.action.toUpperCase()}
                        </span>
                        <span style={styles.legType}>{leg.type.toUpperCase()}</span>
                        <span style={styles.legStrike}>${leg.strike}</span>
                        <span style={styles.legPrice}>@ ${leg.price.toFixed(2)}</span>
                      </div>
                      <button
                        style={styles.removeLegBtn}
                        onClick={() => removeStrategyLeg(leg.id)}
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {strategyLegs.length > 0 && (
              <div style={styles.pnlDiagram}>
                <h3 style={styles.sectionTitle}>Profit/Loss Diagram</h3>
                <div style={styles.chartContainer}>
                  <svg width="100%" height="300" style={styles.svg}>
                    {/* Grid lines */}
                    <line x1="0" y1="150" x2="100%" y2="150" stroke="#333" strokeWidth="1" />

                    {/* P&L curve */}
                    {pnlData.length > 1 && (
                      <polyline
                        points={pnlData.map((point, i) => {
                          const x = (i / (pnlData.length - 1)) * 100;
                          const y = 150 - (point.pnl / 50);
                          return `${x}%,${y}`;
                        }).join(' ')}
                        fill="none"
                        stroke="#00d4ff"
                        strokeWidth="2"
                      />
                    )}

                    {/* Current price line */}
                    {pnlData.length > 0 && (
                      <line
                        x1={`${((currentPrice - pnlData[0].price) / (pnlData[pnlData.length - 1].price - pnlData[0].price)) * 100}%`}
                        y1="0"
                        x2={`${((currentPrice - pnlData[0].price) / (pnlData[pnlData.length - 1].price - pnlData[0].price)) * 100}%`}
                        y2="300"
                        stroke="#ffdd00"
                        strokeWidth="2"
                        strokeDasharray="5,5"
                      />
                    )}
                  </svg>

                  <div style={styles.chartLabels}>
                    <div style={styles.chartLabel}>
                      Max Profit: <span style={{ color: '#00ff88' }}>
                        ${Math.max(...pnlData.map(p => p.pnl)).toFixed(2)}
                      </span>
                    </div>
                    <div style={styles.chartLabel}>
                      Max Loss: <span style={{ color: '#ff6b6b' }}>
                        ${Math.min(...pnlData.map(p => p.pnl)).toFixed(2)}
                      </span>
                    </div>
                    <div style={styles.chartLabel}>
                      Current P&L: <span style={{ color: '#00d4ff' }}>
                        ${pnlData.find(p => Math.abs(p.price - currentPrice) < 1)?.pnl.toFixed(2) || '0.00'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Greeks Calculator View */}
        {view === 'calculator' && (
          <div style={styles.calculatorView}>
            <h3 style={styles.sectionTitle}>Black-Scholes Greeks Calculator</h3>

            <div style={styles.calculatorInputs}>
              <div style={styles.inputGroup}>
                <label style={styles.inputLabel}>Option Type</label>
                <select
                  value={calculatorInputs.optionType}
                  onChange={(e) => setCalculatorInputs({...calculatorInputs, optionType: e.target.value})}
                  style={styles.select}
                >
                  <option value="call">Call</option>
                  <option value="put">Put</option>
                </select>
              </div>

              <div style={styles.inputGroup}>
                <label style={styles.inputLabel}>Spot Price ($)</label>
                <input
                  type="number"
                  value={calculatorInputs.spot}
                  onChange={(e) => setCalculatorInputs({...calculatorInputs, spot: parseFloat(e.target.value) || 0})}
                  style={styles.input}
                  step="0.01"
                />
              </div>

              <div style={styles.inputGroup}>
                <label style={styles.inputLabel}>Strike Price ($)</label>
                <input
                  type="number"
                  value={calculatorInputs.strike}
                  onChange={(e) => setCalculatorInputs({...calculatorInputs, strike: parseFloat(e.target.value) || 0})}
                  style={styles.input}
                  step="0.01"
                />
              </div>

              <div style={styles.inputGroup}>
                <label style={styles.inputLabel}>Time to Expiry (days)</label>
                <input
                  type="number"
                  value={calculatorInputs.timeToExpiry}
                  onChange={(e) => setCalculatorInputs({...calculatorInputs, timeToExpiry: parseFloat(e.target.value) || 1})}
                  style={styles.input}
                  min="1"
                />
              </div>

              <div style={styles.inputGroup}>
                <label style={styles.inputLabel}>Volatility (σ)</label>
                <input
                  type="number"
                  value={calculatorInputs.volatility}
                  onChange={(e) => setCalculatorInputs({...calculatorInputs, volatility: parseFloat(e.target.value) || 0.01})}
                  style={styles.input}
                  step="0.01"
                  min="0.01"
                  max="2"
                />
              </div>

              <div style={styles.inputGroup}>
                <label style={styles.inputLabel}>Risk-Free Rate</label>
                <input
                  type="number"
                  value={calculatorInputs.riskFreeRate}
                  onChange={(e) => setCalculatorInputs({...calculatorInputs, riskFreeRate: parseFloat(e.target.value) || 0})}
                  style={styles.input}
                  step="0.01"
                  min="0"
                />
              </div>
            </div>

            {calculatedGreeks && (
              <div style={styles.calculatorResults}>
                <div style={styles.resultCard}>
                  <div style={styles.resultLabel}>Option Price</div>
                  <div style={styles.resultValue}>${calculatedGreeks.price.toFixed(4)}</div>
                </div>

                <div style={styles.resultCard}>
                  <div style={styles.resultLabel}>Delta (Δ)</div>
                  <div style={styles.resultValue}>{calculatedGreeks.delta.toFixed(4)}</div>
                </div>

                <div style={styles.resultCard}>
                  <div style={styles.resultLabel}>Gamma (Γ)</div>
                  <div style={styles.resultValue}>{calculatedGreeks.gamma.toFixed(6)}</div>
                </div>

                <div style={styles.resultCard}>
                  <div style={styles.resultLabel}>Theta (Θ)</div>
                  <div style={styles.resultValue}>{calculatedGreeks.theta.toFixed(6)}</div>
                </div>

                <div style={styles.resultCard}>
                  <div style={styles.resultLabel}>Vega (ν)</div>
                  <div style={styles.resultValue}>{calculatedGreeks.vega.toFixed(6)}</div>
                </div>

                <div style={styles.resultCard}>
                  <div style={styles.resultLabel}>Rho (ρ)</div>
                  <div style={styles.resultValue}>{calculatedGreeks.rho.toFixed(6)}</div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

const styles = {
  container: {
    padding: '20px',
    background: 'linear-gradient(135deg, rgba(0, 0, 0, 0.95) 0%, rgba(20, 20, 40, 0.95) 100%)',
    borderRadius: '16px',
    border: '1px solid rgba(0, 212, 255, 0.2)',
    minHeight: '600px'
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '20px',
    paddingBottom: '15px',
    borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
  },
  headerLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px'
  },
  headerRight: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px'
  },
  title: {
    margin: 0,
    fontSize: '24px',
    fontWeight: 'bold',
    background: 'linear-gradient(135deg, #00d4ff 0%, #ff00ff 100%)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent'
  },
  symbolInput: {
    padding: '8px 12px',
    background: 'rgba(0, 0, 0, 0.3)',
    border: '1px solid rgba(0, 212, 255, 0.3)',
    borderRadius: '8px',
    color: 'white',
    fontSize: '14px',
    width: '100px'
  },
  expirySelect: {
    padding: '8px 12px',
    background: 'rgba(0, 0, 0, 0.3)',
    border: '1px solid rgba(0, 212, 255, 0.3)',
    borderRadius: '8px',
    color: 'white',
    fontSize: '14px',
    minWidth: '200px'
  },
  refreshBtn: {
    padding: '8px 12px',
    background: 'rgba(0, 212, 255, 0.2)',
    border: '1px solid rgba(0, 212, 255, 0.3)',
    borderRadius: '8px',
    color: '#00d4ff',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    display: 'flex',
    alignItems: 'center'
  },
  priceBanner: {
    display: 'flex',
    justifyContent: 'space-around',
    padding: '15px',
    background: 'rgba(0, 212, 255, 0.1)',
    borderRadius: '8px',
    marginBottom: '20px',
    border: '1px solid rgba(0, 212, 255, 0.2)'
  },
  priceLabel: {
    color: '#aaa',
    marginRight: '10px',
    fontSize: '14px'
  },
  priceValue: {
    color: '#00d4ff',
    fontSize: '18px',
    fontWeight: 'bold'
  },
  tabs: {
    display: 'flex',
    gap: '10px',
    marginBottom: '20px',
    borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
    paddingBottom: '10px'
  },
  tab: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '10px 20px',
    background: 'rgba(255, 255, 255, 0.05)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '8px',
    color: '#aaa',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    fontSize: '14px'
  },
  tabActive: {
    background: 'linear-gradient(135deg, rgba(0, 212, 255, 0.2) 0%, rgba(255, 0, 255, 0.2) 100%)',
    border: '1px solid rgba(0, 212, 255, 0.5)',
    color: '#00d4ff'
  },
  content: {
    minHeight: '400px'
  },
  chainView: {
    width: '100%'
  },
  chainHeader: {
    display: 'grid',
    gridTemplateColumns: '1fr auto 1fr',
    gap: '10px',
    marginBottom: '15px',
    padding: '10px',
    background: 'rgba(0, 0, 0, 0.3)',
    borderRadius: '8px'
  },
  chainHeaderSection: {
    textAlign: 'center'
  },
  chainTitle: {
    margin: 0,
    fontSize: '14px',
    fontWeight: 'bold',
    color: '#00d4ff'
  },
  chainTable: {
    maxHeight: '500px',
    overflowY: 'auto'
  },
  chainRow: {
    display: 'grid',
    gridTemplateColumns: '1fr auto 1fr',
    gap: '10px',
    marginBottom: '8px',
    transition: 'all 0.3s ease'
  },
  atmRow: {
    background: 'rgba(255, 221, 0, 0.1)',
    borderRadius: '8px',
    padding: '4px'
  },
  chainCell: {
    padding: '12px',
    borderRadius: '8px',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    position: 'relative'
  },
  callCell: {
    background: 'rgba(0, 255, 136, 0.1)',
    border: '1px solid rgba(0, 255, 136, 0.2)'
  },
  putCell: {
    background: 'rgba(255, 107, 107, 0.1)',
    border: '1px solid rgba(255, 107, 107, 0.2)'
  },
  strikeCell: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '12px',
    background: 'rgba(0, 0, 0, 0.3)',
    borderRadius: '8px',
    minWidth: '80px'
  },
  strikePrice: {
    fontSize: '16px',
    fontWeight: 'bold',
    color: 'white'
  },
  optionDetails: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px'
  },
  optionPrices: {
    display: 'flex',
    gap: '10px',
    fontSize: '14px'
  },
  bid: {
    color: '#ff6b6b'
  },
  last: {
    color: 'white',
    fontWeight: 'bold'
  },
  ask: {
    color: '#00ff88'
  },
  optionMeta: {
    display: 'flex',
    gap: '12px',
    fontSize: '11px',
    color: '#aaa'
  },
  itmBadge: {
    position: 'absolute',
    top: '4px',
    right: '4px',
    padding: '2px 6px',
    background: 'rgba(255, 221, 0, 0.3)',
    border: '1px solid rgba(255, 221, 0, 0.5)',
    borderRadius: '4px',
    fontSize: '10px',
    color: '#ffdd00',
    fontWeight: 'bold'
  },
  loading: {
    textAlign: 'center',
    padding: '40px',
    color: '#aaa',
    fontSize: '16px'
  },
  greeksView: {
    padding: '20px'
  },
  selectedOption: {
    marginBottom: '30px',
    textAlign: 'center'
  },
  sectionTitle: {
    margin: '0 0 10px 0',
    fontSize: '20px',
    fontWeight: 'bold',
    color: '#00d4ff'
  },
  expiryText: {
    color: '#aaa',
    fontSize: '14px'
  },
  greeksGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
    gap: '20px',
    marginBottom: '30px'
  },
  greekCard: {
    padding: '20px',
    background: 'rgba(0, 0, 0, 0.3)',
    border: '1px solid rgba(0, 212, 255, 0.2)',
    borderRadius: '12px',
    transition: 'all 0.3s ease'
  },
  greekHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    marginBottom: '15px'
  },
  greekName: {
    fontSize: '16px',
    fontWeight: 'bold',
    color: 'white'
  },
  greekValue: {
    fontSize: '28px',
    fontWeight: 'bold',
    color: '#00d4ff',
    marginBottom: '10px'
  },
  greekDescription: {
    fontSize: '12px',
    color: '#aaa'
  },
  optionInfo: {
    padding: '20px',
    background: 'rgba(0, 0, 0, 0.3)',
    borderRadius: '12px',
    border: '1px solid rgba(255, 255, 255, 0.1)'
  },
  infoRow: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '10px 0',
    borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
    fontSize: '14px',
    color: '#aaa'
  },
  infoValue: {
    color: 'white',
    fontWeight: 'bold'
  },
  emptyState: {
    textAlign: 'center',
    padding: '60px 20px',
    color: '#666'
  },
  strategyView: {
    padding: '20px'
  },
  strategySelector: {
    marginBottom: '30px'
  },
  strategyGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
    gap: '15px'
  },
  strategyCard: {
    padding: '15px',
    background: 'rgba(0, 0, 0, 0.3)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '8px',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    textAlign: 'left'
  },
  strategyCardActive: {
    background: 'linear-gradient(135deg, rgba(0, 212, 255, 0.2) 0%, rgba(255, 0, 255, 0.2) 100%)',
    border: '1px solid rgba(0, 212, 255, 0.5)'
  },
  strategyName: {
    fontSize: '14px',
    fontWeight: 'bold',
    color: 'white',
    marginBottom: '8px'
  },
  strategyDescription: {
    fontSize: '12px',
    color: '#aaa'
  },
  strategyLegs: {
    marginBottom: '30px'
  },
  legsHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '15px'
  },
  clearBtn: {
    padding: '8px 16px',
    background: 'rgba(255, 107, 107, 0.2)',
    border: '1px solid rgba(255, 107, 107, 0.3)',
    borderRadius: '8px',
    color: '#ff6b6b',
    cursor: 'pointer',
    fontSize: '14px'
  },
  emptyLegs: {
    padding: '40px',
    textAlign: 'center',
    color: '#666',
    background: 'rgba(0, 0, 0, 0.2)',
    borderRadius: '8px',
    border: '1px dashed rgba(255, 255, 255, 0.1)'
  },
  legsList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '10px'
  },
  legItem: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '12px 16px',
    background: 'rgba(0, 0, 0, 0.3)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '8px'
  },
  legInfo: {
    display: 'flex',
    gap: '15px',
    alignItems: 'center'
  },
  legAction: {
    fontSize: '14px',
    fontWeight: 'bold'
  },
  legType: {
    fontSize: '14px',
    color: '#aaa'
  },
  legStrike: {
    fontSize: '14px',
    color: 'white',
    fontWeight: 'bold'
  },
  legPrice: {
    fontSize: '14px',
    color: '#00d4ff'
  },
  removeLegBtn: {
    width: '30px',
    height: '30px',
    background: 'rgba(255, 107, 107, 0.2)',
    border: '1px solid rgba(255, 107, 107, 0.3)',
    borderRadius: '50%',
    color: '#ff6b6b',
    cursor: 'pointer',
    fontSize: '20px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center'
  },
  pnlDiagram: {
    padding: '20px',
    background: 'rgba(0, 0, 0, 0.3)',
    borderRadius: '12px',
    border: '1px solid rgba(255, 255, 255, 0.1)'
  },
  chartContainer: {
    marginTop: '20px'
  },
  svg: {
    background: 'rgba(0, 0, 0, 0.2)',
    borderRadius: '8px'
  },
  chartLabels: {
    display: 'flex',
    justifyContent: 'space-around',
    marginTop: '15px',
    padding: '15px',
    background: 'rgba(0, 0, 0, 0.2)',
    borderRadius: '8px'
  },
  chartLabel: {
    fontSize: '14px',
    color: '#aaa'
  },
  calculatorView: {
    padding: '20px'
  },
  calculatorInputs: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '20px',
    marginBottom: '30px'
  },
  inputGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px'
  },
  inputLabel: {
    fontSize: '14px',
    color: '#aaa',
    fontWeight: '500'
  },
  input: {
    padding: '10px 12px',
    background: 'rgba(0, 0, 0, 0.3)',
    border: '1px solid rgba(0, 212, 255, 0.3)',
    borderRadius: '8px',
    color: 'white',
    fontSize: '14px'
  },
  select: {
    padding: '10px 12px',
    background: 'rgba(0, 0, 0, 0.3)',
    border: '1px solid rgba(0, 212, 255, 0.3)',
    borderRadius: '8px',
    color: 'white',
    fontSize: '14px'
  },
  calculatorResults: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
    gap: '20px'
  },
  resultCard: {
    padding: '20px',
    background: 'rgba(0, 212, 255, 0.1)',
    border: '1px solid rgba(0, 212, 255, 0.3)',
    borderRadius: '12px',
    textAlign: 'center'
  },
  resultLabel: {
    fontSize: '14px',
    color: '#aaa',
    marginBottom: '10px'
  },
  resultValue: {
    fontSize: '24px',
    fontWeight: 'bold',
    color: '#00d4ff'
  }
};

export default OptionsAnalytics;
