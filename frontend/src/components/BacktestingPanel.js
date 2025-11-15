import React, { useState } from 'react';
import { Activity, TrendingUp, TrendingDown, DollarSign, Target, AlertCircle, PlayCircle, Loader } from 'lucide-react';
import api from '../services/api';

function BacktestingPanel() {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  // Form state
  const [symbol, setSymbol] = useState('AAPL');
  const [timeframe, setTimeframe] = useState('1Y');
  const [minConfidence, setMinConfidence] = useState(0.6);
  const [preset, setPreset] = useState('moderate');

  const presets = {
    conservative: {
      name: 'Conservative',
      description: 'High confidence, strict risk management',
      minConfidence: 0.8,
      color: 'bg-blue-500'
    },
    moderate: {
      name: 'Moderate',
      description: 'Balanced approach',
      minConfidence: 0.6,
      color: 'bg-green-500'
    },
    aggressive: {
      name: 'Aggressive',
      description: 'Lower confidence, larger positions',
      minConfidence: 0.5,
      color: 'bg-red-500'
    }
  };

  const timeframes = {
    '1M': 'Last 1 Month',
    '3M': 'Last 3 Months',
    '6M': 'Last 6 Months',
    '1Y': 'Last 1 Year',
    '2Y': 'Last 2 Years',
    '5Y': 'Last 5 Years'
  };

  const popularSymbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'BTC-USD', 'ETH-USD', 'SPY', 'QQQ'];

  const runBacktest = async () => {
    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const response = await api.post('/backtest/quick', {
        symbol: symbol.toUpperCase(),
        timeframe: timeframe,
        min_confidence: minConfidence
      });

      if (response.data.success) {
        setResults(response.data.backtest_result);
      } else {
        setError('Backtest failed');
      }
    } catch (err) {
      console.error('Backtest error:', err);
      setError(err.response?.data?.detail || 'Failed to run backtest');
    } finally {
      setLoading(false);
    }
  };

  const handlePresetChange = (presetName) => {
    setPreset(presetName);
    setMinConfidence(presets[presetName].minConfidence);
  };

  const getReturnColor = (returnPct) => {
    if (returnPct > 0) return 'text-green-400';
    if (returnPct < 0) return 'text-red-400';
    return 'text-gray-400';
  };

  const getWinRateColor = (winRate) => {
    if (winRate >= 60) return 'text-green-400';
    if (winRate >= 50) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getSharpeColor = (sharpe) => {
    if (sharpe >= 1.5) return 'text-green-400';
    if (sharpe >= 1.0) return 'text-yellow-400';
    return 'text-red-400';
  };

  return (
    <div className="backtesting-panel bg-gray-800 rounded-lg p-6 shadow-xl animate-fade-in-up card-hover">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-white flex items-center animate-fade-in-left">
          <Activity className="mr-2 animate-spin-slow" size={24} />
          AI Strategy Backtesting
        </h2>
      </div>

      {/* Configuration Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {/* Symbol Selection */}
        <div>
          <label className="block text-gray-300 mb-2 font-semibold">Symbol</label>
          <div className="flex gap-2">
            <input
              type="text"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              placeholder="Enter symbol"
              className="flex-1 bg-gray-700 text-white px-4 py-2 rounded-lg border border-gray-600 focus:border-blue-500 focus:outline-none"
            />
          </div>
          <div className="flex flex-wrap gap-2 mt-2">
            {popularSymbols.map((sym) => (
              <button
                key={sym}
                onClick={() => setSymbol(sym)}
                className={`px-3 py-1 rounded text-sm ${
                  symbol === sym
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                {sym}
              </button>
            ))}
          </div>
        </div>

        {/* Timeframe Selection */}
        <div>
          <label className="block text-gray-300 mb-2 font-semibold">Timeframe</label>
          <select
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value)}
            className="w-full bg-gray-700 text-white px-4 py-2 rounded-lg border border-gray-600 focus:border-blue-500 focus:outline-none"
          >
            {Object.entries(timeframes).map(([key, label]) => (
              <option key={key} value={key}>
                {label}
              </option>
            ))}
          </select>
        </div>

        {/* Strategy Preset */}
        <div>
          <label className="block text-gray-300 mb-2 font-semibold">Strategy</label>
          <div className="grid grid-cols-3 gap-2">
            {Object.entries(presets).map(([key, config]) => (
              <button
                key={key}
                onClick={() => handlePresetChange(key)}
                className={`p-3 rounded-lg text-center transition-all ${
                  preset === key
                    ? `${config.color} text-white`
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                <div className="font-semibold text-sm">{config.name}</div>
                <div className="text-xs opacity-80 mt-1">{config.description}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Confidence Slider */}
        <div>
          <label className="block text-gray-300 mb-2 font-semibold">
            Min Confidence: {(minConfidence * 100).toFixed(0)}%
          </label>
          <input
            type="range"
            min="0.4"
            max="0.9"
            step="0.05"
            value={minConfidence}
            onChange={(e) => setMinConfidence(parseFloat(e.target.value))}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-gray-400 mt-1">
            <span>Low (40%)</span>
            <span>High (90%)</span>
          </div>
        </div>
      </div>

      {/* Run Button */}
      <button
        onClick={runBacktest}
        disabled={loading}
        className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3 rounded-lg font-semibold hover:from-blue-700 hover:to-purple-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
      >
        {loading ? (
          <>
            <Loader className="animate-spin mr-2" size={20} />
            Running Backtest...
          </>
        ) : (
          <>
            <PlayCircle className="mr-2" size={20} />
            Run Backtest
          </>
        )}
      </button>

      {/* Error Display */}
      {error && (
        <div className="mt-4 bg-red-900/50 border border-red-500 text-red-200 px-4 py-3 rounded-lg flex items-center">
          <AlertCircle className="mr-2" size={20} />
          {error}
        </div>
      )}

      {/* Results Display */}
      {results && (
        <div className="mt-6 space-y-4">
          {/* Header */}
          <div className="bg-gray-700 rounded-lg p-4">
            <h3 className="text-xl font-bold text-white mb-2">
              {results.symbol} - {timeframes[timeframe]}
            </h3>
            <div className="text-sm text-gray-400">
              {results.period.start_date} to {results.period.end_date} ({results.period.days} days)
            </div>
          </div>

          {/* Key Metrics Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {/* Total Return */}
            <div className="bg-gray-700 rounded-lg p-4 animate-scale-in-bounce hover-lift animate-delay-1">
              <div className="text-gray-400 text-sm mb-1">Total Return</div>
              <div className={`text-2xl font-bold ${getReturnColor(results.capital.total_return_pct)} animate-number-pop`}>
                {results.capital.total_return_pct >= 0 ? '+' : ''}
                {results.capital.total_return_pct.toFixed(2)}%
              </div>
              <div className="text-xs text-gray-500 mt-1">
                ${results.capital.initial.toLocaleString()} → ${results.capital.final.toLocaleString()}
              </div>
            </div>

            {/* Win Rate */}
            <div className="bg-gray-700 rounded-lg p-4 animate-scale-in-bounce hover-lift animate-delay-2">
              <div className="text-gray-400 text-sm mb-1">Win Rate</div>
              <div className={`text-2xl font-bold ${getWinRateColor(results.trades.win_rate)} animate-number-pop`}>
                {results.trades.win_rate.toFixed(1)}%
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {results.trades.winning} wins / {results.trades.losing} losses
              </div>
            </div>

            {/* Total Trades */}
            <div className="bg-gray-700 rounded-lg p-4 animate-scale-in-bounce hover-lift animate-delay-3">
              <div className="text-gray-400 text-sm mb-1">Total Trades</div>
              <div className="text-2xl font-bold text-blue-400 animate-number-pop">{results.trades.total}</div>
              <div className="text-xs text-gray-500 mt-1">
                {results.trades.total > 0 ? (results.period.days / results.trades.total).toFixed(1) : 'N/A'} days/trade
              </div>
            </div>

            {/* Sharpe Ratio */}
            <div className="bg-gray-700 rounded-lg p-4 animate-scale-in-bounce hover-lift animate-delay-4">
              <div className="text-gray-400 text-sm mb-1">Sharpe Ratio</div>
              <div className={`text-2xl font-bold ${getSharpeColor(results.performance.sharpe_ratio)} animate-number-pop`}>
                {results.performance.sharpe_ratio.toFixed(2)}
              </div>
              <div className="text-xs text-gray-500 mt-1">Risk-adjusted return</div>
            </div>
          </div>

          {/* Performance Details */}
          <div className="bg-gray-700 rounded-lg p-4">
            <h4 className="text-white font-semibold mb-3">Performance Details</h4>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div>
                <div className="text-gray-400 text-sm">Avg Win</div>
                <div className="text-green-400 font-semibold">
                  ${results.performance.avg_win.toFixed(2)}
                </div>
              </div>
              <div>
                <div className="text-gray-400 text-sm">Avg Loss</div>
                <div className="text-red-400 font-semibold">
                  ${results.performance.avg_loss.toFixed(2)}
                </div>
              </div>
              <div>
                <div className="text-gray-400 text-sm">Profit Factor</div>
                <div className="text-white font-semibold">
                  {results.performance.profit_factor.toFixed(2)}
                </div>
              </div>
              <div>
                <div className="text-gray-400 text-sm">Largest Win</div>
                <div className="text-green-400 font-semibold">
                  ${results.performance.largest_win.toFixed(2)}
                </div>
              </div>
              <div>
                <div className="text-gray-400 text-sm">Largest Loss</div>
                <div className="text-red-400 font-semibold">
                  ${results.performance.largest_loss.toFixed(2)}
                </div>
              </div>
              <div>
                <div className="text-gray-400 text-sm">Max Drawdown</div>
                <div className="text-orange-400 font-semibold">
                  {results.risk_metrics.max_drawdown_pct.toFixed(2)}%
                </div>
              </div>
            </div>
          </div>

          {/* Signal Performance */}
          {results.signal_performance && Object.keys(results.signal_performance).length > 0 && (
            <div className="bg-gray-700 rounded-lg p-4">
              <h4 className="text-white font-semibold mb-3">Signal Performance</h4>
              <div className="space-y-2">
                {Object.entries(results.signal_performance).map(([signal, perf]) => (
                  <div key={signal} className="flex justify-between items-center">
                    <div className="flex items-center">
                      <span
                        className={`px-3 py-1 rounded text-sm font-semibold ${
                          signal.includes('BUY')
                            ? 'bg-green-600 text-white'
                            : signal.includes('SELL')
                            ? 'bg-red-600 text-white'
                            : 'bg-gray-600 text-white'
                        }`}
                      >
                        {signal.replace('_', ' ')}
                      </span>
                      <span className="ml-3 text-gray-400 text-sm">
                        {perf.total_trades} trades
                      </span>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <div className={`font-semibold ${getWinRateColor(perf.win_rate)}`}>
                          {perf.win_rate.toFixed(1)}% win rate
                        </div>
                        <div className={`text-sm ${getReturnColor(perf.total_pnl)}`}>
                          ${perf.total_pnl.toFixed(2)} total P&L
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Equity Curve Chart */}
          {results.equity_curve && results.equity_curve.length > 0 && (
            <div className="bg-gray-700 rounded-lg p-4">
              <h4 className="text-white font-semibold mb-3">Equity Curve</h4>
              <div className="relative h-48">
                <svg className="w-full h-full">
                  <polyline
                    fill="none"
                    stroke="#3b82f6"
                    strokeWidth="2"
                    points={results.equity_curve
                      .map((point, i) => {
                        const x = (i / (results.equity_curve.length - 1)) * 100;
                        const maxEquity = Math.max(...results.equity_curve.map(p => p.equity));
                        const minEquity = Math.min(...results.equity_curve.map(p => p.equity));
                        const range = maxEquity - minEquity || 1;
                        const y = 100 - ((point.equity - minEquity) / range) * 80;
                        return `${x}%,${y}%`;
                      })
                      .join(' ')}
                  />
                </svg>
              </div>
              <div className="flex justify-between text-xs text-gray-400 mt-2">
                <span>Start</span>
                <span className={getReturnColor(results.capital.total_return_pct)}>
                  {results.capital.total_return_pct >= 0 ? '↑' : '↓'} {Math.abs(results.capital.total_return_pct).toFixed(2)}%
                </span>
                <span>End</span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default BacktestingPanel;
