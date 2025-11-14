import React, { useEffect, useRef, useState, useCallback } from 'react';
import { createChart } from 'lightweight-charts';
import SymbolSearch from './SymbolSearch';
import wsService from '../../services/websocket';
import './MainChart.css';

const MainChart = ({ initialSymbol = 'AAPL' }) => {
  const [symbol, setSymbol] = useState(initialSymbol);
  const [timeframe, setTimeframe] = useState('1D');
  const [chartType, setChartType] = useState('candlestick');
  const [isLoading, setIsLoading] = useState(true);
  const [drawingMode, setDrawingMode] = useState(null);
  const [indicators, setIndicators] = useState({ sma: false, ema: false, rsi: false, macd: false });
  
  const chartRef = useRef(null);
  const containerRef = useRef(null);
  const candleSeriesRef = useRef(null);
  const volumeSeriesRef = useRef(null);
  const indicatorSeriesRef = useRef({});
  const resizeObserverRef = useRef(null);

  const timeframes = [
    { label: '1s', value: '1s' },
    { label: '5s', value: '5s' },
    { label: '1m', value: '1m' },
    { label: '5m', value: '5m' },
    { label: '15m', value: '15m' },
    { label: '1h', value: '1h' },
    { label: '4h', value: '4h' },
    { label: '1D', value: '1D' },
    { label: '1W', value: '1W' }
  ];

  const initializeChart = useCallback(() => {
    if (!containerRef.current || chartRef.current) return;

    const { width, height } = containerRef.current.getBoundingClientRect();
    if (width === 0 || height === 0) return;

    console.log('Initializing chart with dimensions:', { width, height });

    const chart = createChart(containerRef.current, {
      width,
      height,
      layout: {
        background: { color: '#0f1419' },
        textColor: '#d1d4dc',
      },
      grid: {
        vertLines: { color: 'rgba(42, 46, 57, 0.5)' },
        horzLines: { color: 'rgba(42, 46, 57, 0.5)' },
      },
      crosshair: {
        mode: 1,
      },
      rightPriceScale: {
        borderColor: 'rgba(197, 203, 206, 0.4)',
      },
      timeScale: {
        borderColor: 'rgba(197, 203, 206, 0.4)',
        timeVisible: true,
        secondsVisible: timeframe.includes('s'),
      },
    });

    const candleSeries = chart.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    });

    const volumeSeries = chart.addHistogramSeries({
      color: '#26a69a',
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: '',
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
    });

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;
    volumeSeriesRef.current = volumeSeries;

    console.log('Chart initialized successfully');
  }, [timeframe]);

  const loadChartData = useCallback(async () => {
    if (!candleSeriesRef.current || !volumeSeriesRef.current) return;

    setIsLoading(true);
    try {
      const response = await fetch(`/api/v1/data/chart/${symbol}?timeframe=${timeframe}&limit=500`);
      const data = await response.json();

      if (data.candles && data.candles.length > 0) {
        console.log(`Loaded ${data.candles.length} candles for ${symbol}`);
        
        candleSeriesRef.current.setData(data.candles);

        const volumeData = data.candles.map((candle, idx) => ({
          time: candle.time,
          value: data.volume[idx] || 0,
          color: candle.close >= candle.open ? 'rgba(38, 166, 154, 0.5)' : 'rgba(239, 83, 80, 0.5)',
        }));
        volumeSeriesRef.current.setData(volumeData);

        chartRef.current.timeScale().fitContent();
      }
    } catch (error) {
      console.error('Error loading chart data:', error);
    } finally {
      setIsLoading(false);
    }
  }, [symbol, timeframe]);

  useEffect(() => {
    if (!chartRef.current || !candleSeriesRef.current) return;

    chartRef.current.removeSeries(candleSeriesRef.current);

    let newSeries;
    if (chartType === 'line') {
      newSeries = chartRef.current.addLineSeries({
        color: '#2962FF',
        lineWidth: 2,
      });
    } else if (chartType === 'area') {
      newSeries = chartRef.current.addAreaSeries({
        topColor: 'rgba(41, 98, 255, 0.4)',
        bottomColor: 'rgba(41, 98, 255, 0.0)',
        lineColor: '#2962FF',
        lineWidth: 2,
      });
    } else {
      newSeries = chartRef.current.addCandlestickSeries({
        upColor: '#26a69a',
        downColor: '#ef5350',
        borderVisible: false,
        wickUpColor: '#26a69a',
        wickDownColor: '#ef5350',
      });
    }

    candleSeriesRef.current = newSeries;
    loadChartData();
  }, [chartType, loadChartData]);

  useEffect(() => {
    if (!containerRef.current) return;

    const checkDimensions = () => {
      const { width, height } = containerRef.current.getBoundingClientRect();
      if (width > 0 && height > 0) {
        initializeChart();
      } else {
        requestAnimationFrame(checkDimensions);
      }
    };

    checkDimensions();

    resizeObserverRef.current = new ResizeObserver(() => {
      if (chartRef.current && containerRef.current) {
        const { width, height } = containerRef.current.getBoundingClientRect();
        if (width > 0 && height > 0) {
          chartRef.current.resize(width, height);
        }
      }
    });

    resizeObserverRef.current.observe(containerRef.current);

    return () => {
      if (resizeObserverRef.current) {
        resizeObserverRef.current.disconnect();
      }
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
    };
  }, [initializeChart]);

  useEffect(() => {
    if (chartRef.current) {
      loadChartData();
    }
  }, [symbol, timeframe, loadChartData]);

  useEffect(() => {
    const unsubscribe = wsService.subscribe('price_update', (data) => {
      if (data.symbol === symbol && candleSeriesRef.current) {
        const lastCandle = {
          time: Math.floor(Date.now() / 1000),
          open: data.open || data.price,
          high: data.high || data.price,
          low: data.low || data.price,
          close: data.price,
        };
        candleSeriesRef.current.update(lastCandle);
      }
    });

    return unsubscribe;
  }, [symbol]);

  const handleTimeframeChange = (newTimeframe) => {
    setTimeframe(newTimeframe);
  };

  const handleSymbolChange = (newSymbol) => {
    setSymbol(newSymbol);
  };

  const handleChartTypeChange = (type) => {
    setChartType(type);
  };

  const handleDrawingTool = (tool) => {
    setDrawingMode(drawingMode === tool ? null : tool);
  };

  const toggleIndicator = (indicator) => {
    setIndicators(prev => ({ ...prev, [indicator]: !prev[indicator] }));
  };

  return (
    <div className="main-chart-container">
      <div className="chart-header">
        <div className="symbol-display">
          <span className="symbol-text">{symbol}</span>
          <SymbolSearch currentSymbol={symbol} onSymbolChange={handleSymbolChange} />
        </div>

        <div className="chart-controls">
          <div className="control-group">
            <label>Type:</label>
            <button
              className={`control-btn ${chartType === 'candlestick' ? 'active' : ''}`}
              onClick={() => handleChartTypeChange('candlestick')}
            >
              Candles
            </button>
            <button
              className={`control-btn ${chartType === 'line' ? 'active' : ''}`}
              onClick={() => handleChartTypeChange('line')}
            >
              Line
            </button>
            <button
              className={`control-btn ${chartType === 'area' ? 'active' : ''}`}
              onClick={() => handleChartTypeChange('area')}
            >
              Area
            </button>
          </div>

          <div className="control-group">
            <label>Timeframe:</label>
            {timeframes.map(tf => (
              <button
                key={tf.value}
                className={`control-btn ${timeframe === tf.value ? 'active' : ''}`}
                onClick={() => handleTimeframeChange(tf.value)}
              >
                {tf.label}
              </button>
            ))}
          </div>

          <div className="control-group">
            <label>Draw:</label>
            <button
              className={`control-btn ${drawingMode === 'trendline' ? 'active' : ''}`}
              onClick={() => handleDrawingTool('trendline')}
              title="Trend Line"
            >
              📈
            </button>
            <button
              className={`control-btn ${drawingMode === 'horizontal' ? 'active' : ''}`}
              onClick={() => handleDrawingTool('horizontal')}
              title="Horizontal Line"
            >
              ➖
            </button>
            <button
              className={`control-btn ${drawingMode === 'rectangle' ? 'active' : ''}`}
              onClick={() => handleDrawingTool('rectangle')}
              title="Rectangle"
            >
              ⬜
            </button>
          </div>

          <div className="control-group">
            <label>Indicators:</label>
            <button
              className={`control-btn ${indicators.sma ? 'active' : ''}`}
              onClick={() => toggleIndicator('sma')}
              title="Simple Moving Average"
            >
              SMA
            </button>
            <button
              className={`control-btn ${indicators.ema ? 'active' : ''}`}
              onClick={() => toggleIndicator('ema')}
              title="Exponential Moving Average"
            >
              EMA
            </button>
            <button
              className={`control-btn ${indicators.rsi ? 'active' : ''}`}
              onClick={() => toggleIndicator('rsi')}
              title="Relative Strength Index"
            >
              RSI
            </button>
            <button
              className={`control-btn ${indicators.macd ? 'active' : ''}`}
              onClick={() => toggleIndicator('macd')}
              title="MACD"
            >
              MACD
            </button>
          </div>
        </div>
      </div>

      <div className="chart-workspace">
        {isLoading && (
          <div className="chart-loading">
            <div className="spinner"></div>
            <span>Loading chart data...</span>
          </div>
        )}
        {drawingMode && (
          <div className="drawing-hint">
            {drawingMode === 'trendline' && 'Click two points to draw a trend line'}
            {drawingMode === 'horizontal' && 'Click to place a horizontal line'}
            {drawingMode === 'rectangle' && 'Click two corners to draw a rectangle'}
          </div>
        )}
        <div ref={containerRef} className="chart-canvas" />
      </div>
    </div>
  );
};

export default MainChart;
