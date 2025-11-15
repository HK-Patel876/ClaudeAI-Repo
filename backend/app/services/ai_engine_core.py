"""
AI Engine Core - Unified system combining ML, Neural Networks, and Technical Analysis
Real-time signal generation for stocks, crypto, options, and derivatives
"""
import asyncio
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from loguru import logger
from collections import deque

from .ml_engine import ml_engine, MLPrediction, SignalStrength
from .neural_engine import neural_engine


class LiveSignal:
    """Real-time trading signal with all analysis"""

    def __init__(
        self,
        symbol: str,
        asset_type: str,
        signal: str,
        confidence: float,
        current_price: float,
        predicted_price: float,
        predicted_change_pct: float,
        technical_score: float,
        ml_score: float,
        neural_score: float,
        risk_score: float,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        position_size_pct: float,
        timestamp: datetime
    ):
        self.symbol = symbol
        self.asset_type = asset_type
        self.signal = signal
        self.confidence = confidence
        self.current_price = current_price
        self.predicted_price = predicted_price
        self.predicted_change_pct = predicted_change_pct
        self.technical_score = technical_score
        self.ml_score = ml_score
        self.neural_score = neural_score
        self.risk_score = risk_score
        self.entry_price = entry_price
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.position_size_pct = position_size_pct
        self.timestamp = timestamp

    def to_dict(self):
        return {
            "symbol": self.symbol,
            "asset_type": self.asset_type,
            "signal": self.signal,
            "confidence": round(self.confidence, 3),
            "current_price": round(self.current_price, 2),
            "predicted_price": round(self.predicted_price, 2),
            "predicted_change_pct": round(self.predicted_change_pct, 2),
            "scores": {
                "technical": round(self.technical_score, 3),
                "ml": round(self.ml_score, 3),
                "neural": round(self.neural_score, 3),
                "risk": round(self.risk_score, 3)
            },
            "trade_plan": {
                "entry": round(self.entry_price, 2),
                "stop_loss": round(self.stop_loss, 2),
                "take_profit": round(self.take_profit, 2),
                "position_size_pct": round(self.position_size_pct, 2),
                "risk_reward_ratio": round((self.take_profit - self.entry_price) / (self.entry_price - self.stop_loss), 2) if self.entry_price != self.stop_loss else 0
            },
            "timestamp": self.timestamp.isoformat(),
            "age_seconds": (datetime.now() - self.timestamp).total_seconds()
        }


class AIEngineCore:
    """
    Core AI Engine that orchestrates all analysis systems
    Provides real-time signals for multiple assets
    """

    def __init__(self):
        self.ml_engine = ml_engine
        self.neural_engine = neural_engine

        # Signal cache - stores latest signals for each symbol
        self.live_signals: Dict[str, LiveSignal] = {}

        # Historical signal queue for backtesting
        self.signal_history: Dict[str, deque] = {}

        # Asset types supported
        self.asset_types = {
            'stocks': ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN', 'NVDA', 'META', 'NFLX'],
            'crypto': ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD', 'ADA-USD'],
            'indices': ['SPY', 'QQQ', 'DIA', 'IWM'],
            'forex': ['EURUSD=X', 'GBPUSD=X', 'USDJPY=X']
        }

        # Performance tracking
        self.signal_accuracy = {}
        self.is_running = False

        logger.info("AI Engine Core initialized")

    async def analyze_symbol(
        self,
        symbol: str,
        df: pd.DataFrame,
        current_price: float,
        asset_type: str = 'stock'
    ) -> LiveSignal:
        """
        Comprehensive analysis of a single symbol
        Combines all AI systems for maximum accuracy
        """
        try:
            # Run all engines in parallel
            ml_prediction, neural_prediction = await asyncio.gather(
                self.ml_engine.predict(symbol, df, current_price),
                self.neural_engine.predict(symbol, df)
            )

            # Combine predictions with weighted scores
            combined_score, confidence = self._combine_predictions(
                ml_prediction,
                neural_prediction
            )

            # Determine final signal
            signal = self._determine_signal(combined_score, confidence)

            # Calculate risk metrics
            risk_score = self._calculate_risk_score(df, signal, confidence)

            # Generate trade plan
            trade_plan = self._generate_trade_plan(
                signal=signal,
                current_price=current_price,
                ml_prediction=ml_prediction,
                neural_prediction=neural_prediction,
                risk_score=risk_score,
                df=df
            )

            # Create live signal
            live_signal = LiveSignal(
                symbol=symbol,
                asset_type=asset_type,
                signal=signal,
                confidence=confidence,
                current_price=current_price,
                predicted_price=neural_prediction['predicted_price'],
                predicted_change_pct=neural_prediction['predicted_change_pct'],
                technical_score=combined_score['technical'],
                ml_score=combined_score['ml'],
                neural_score=combined_score['neural'],
                risk_score=risk_score,
                entry_price=trade_plan['entry'],
                stop_loss=trade_plan['stop_loss'],
                take_profit=trade_plan['take_profit'],
                position_size_pct=trade_plan['position_size_pct'],
                timestamp=datetime.now()
            )

            # Cache the signal
            self.live_signals[symbol] = live_signal

            # Add to history
            if symbol not in self.signal_history:
                self.signal_history[symbol] = deque(maxlen=100)
            self.signal_history[symbol].append(live_signal)

            return live_signal

        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return self._create_neutral_signal(symbol, current_price, asset_type)

    def _combine_predictions(
        self,
        ml_prediction: MLPrediction,
        neural_prediction: Dict
    ) -> tuple:
        """Combine ML and Neural predictions with optimal weights"""

        # Extract scores
        ml_score = self._signal_to_score(ml_prediction.signal)
        neural_score = neural_prediction['predicted_change_pct'] / 2  # Normalize to -1 to 1

        # Technical score from ML model scores
        technical_score = np.mean(list(ml_prediction.model_scores.values()))

        # Weighted combination
        weights = {
            'technical': 0.3,
            'ml': 0.35,
            'neural': 0.35
        }

        combined_score = {
            'technical': technical_score,
            'ml': ml_score,
            'neural': neural_score,
            'overall': (
                technical_score * weights['technical'] +
                ml_score * weights['ml'] +
                neural_score * weights['neural']
            )
        }

        # Calculate confidence
        confidence = np.mean([
            ml_prediction.confidence,
            neural_prediction['confidence']
        ])

        return combined_score, confidence

    def _signal_to_score(self, signal: SignalStrength) -> float:
        """Convert signal enum to numerical score"""
        mapping = {
            SignalStrength.STRONG_BUY: 1.0,
            SignalStrength.BUY: 0.5,
            SignalStrength.NEUTRAL: 0.0,
            SignalStrength.SELL: -0.5,
            SignalStrength.STRONG_SELL: -1.0
        }
        return mapping.get(signal, 0.0)

    def _determine_signal(self, combined_score: Dict, confidence: float) -> str:
        """Determine final trading signal"""
        overall_score = combined_score['overall']

        if overall_score > 0.6 and confidence > 0.75:
            return "STRONG_BUY"
        elif overall_score > 0.3:
            return "BUY"
        elif overall_score < -0.6 and confidence > 0.75:
            return "STRONG_SELL"
        elif overall_score < -0.3:
            return "SELL"
        else:
            return "NEUTRAL"

    def _calculate_risk_score(
        self,
        df: pd.DataFrame,
        signal: str,
        confidence: float
    ) -> float:
        """
        Calculate comprehensive risk score
        Lower is better (0 = low risk, 1 = high risk)
        """
        risk_factors = []

        # Volatility risk
        if 'close' in df.columns:
            volatility = df['close'].pct_change().tail(20).std()
            vol_risk = min(volatility * 50, 1.0)  # Normalize
            risk_factors.append(vol_risk)

        # Volume risk (low volume = higher risk)
        if 'volume' in df.columns:
            avg_volume = df['volume'].tail(20).mean()
            recent_volume = df['volume'].tail(5).mean()
            volume_risk = 1.0 - min(recent_volume / avg_volume, 1.0)
            risk_factors.append(volume_risk)

        # Confidence risk
        confidence_risk = 1.0 - confidence
        risk_factors.append(confidence_risk)

        # Signal strength risk
        signal_risk_map = {
            "STRONG_BUY": 0.2,
            "BUY": 0.3,
            "NEUTRAL": 0.8,
            "SELL": 0.3,
            "STRONG_SELL": 0.2
        }
        signal_risk = signal_risk_map.get(signal, 0.5)
        risk_factors.append(signal_risk)

        # Average all risk factors
        overall_risk = np.mean(risk_factors)

        return overall_risk

    def _generate_trade_plan(
        self,
        signal: str,
        current_price: float,
        ml_prediction: MLPrediction,
        neural_prediction: Dict,
        risk_score: float,
        df: pd.DataFrame
    ) -> Dict:
        """Generate detailed trade plan with entry, stop loss, take profit"""

        # Calculate ATR for stop loss / take profit
        if 'high' in df.columns and 'low' in df.columns:
            atr = self._calculate_atr(df)
        else:
            atr = current_price * 0.02  # 2% default

        # Position sizing based on risk
        max_position = 10.0  # Max 10% of portfolio
        position_size_pct = max_position * (1.0 - risk_score)

        if signal in ["BUY", "STRONG_BUY"]:
            entry = current_price
            stop_loss = current_price - (atr * 2)
            take_profit = current_price + (atr * 3)

        elif signal in ["SELL", "STRONG_SELL"]:
            entry = current_price
            stop_loss = current_price + (atr * 2)
            take_profit = current_price - (atr * 3)

        else:  # NEUTRAL
            entry = current_price
            stop_loss = current_price * 0.98
            take_profit = current_price * 1.02

        return {
            'entry': entry,
            'stop_loss': max(stop_loss, 0),
            'take_profit': take_profit,
            'position_size_pct': position_size_pct
        }

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range"""
        high = df['high'].tail(period)
        low = df['low'].tail(period)
        close = df['close'].tail(period + 1)

        tr1 = high - low
        tr2 = abs(high - close.shift(1).tail(period))
        tr3 = abs(low - close.shift(1).tail(period))

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.mean()

        return atr

    def _create_neutral_signal(
        self,
        symbol: str,
        current_price: float,
        asset_type: str
    ) -> LiveSignal:
        """Create neutral signal when analysis fails"""
        return LiveSignal(
            symbol=symbol,
            asset_type=asset_type,
            signal="NEUTRAL",
            confidence=0.3,
            current_price=current_price,
            predicted_price=current_price,
            predicted_change_pct=0.0,
            technical_score=0.0,
            ml_score=0.0,
            neural_score=0.0,
            risk_score=0.5,
            entry_price=current_price,
            stop_loss=current_price * 0.98,
            take_profit=current_price * 1.02,
            position_size_pct=1.0,
            timestamp=datetime.now()
        )

    def get_all_live_signals(self) -> List[Dict]:
        """Get all current live signals"""
        return [signal.to_dict() for signal in self.live_signals.values()]

    def get_signal(self, symbol: str) -> Optional[Dict]:
        """Get live signal for specific symbol"""
        signal = self.live_signals.get(symbol)
        return signal.to_dict() if signal else None

    def get_top_signals(self, limit: int = 10, min_confidence: float = 0.6) -> List[Dict]:
        """Get top trading opportunities"""
        signals = [
            signal.to_dict()
            for signal in self.live_signals.values()
            if signal.confidence >= min_confidence and signal.signal != "NEUTRAL"
        ]

        # Sort by confidence * predicted_change
        signals.sort(
            key=lambda x: abs(x['confidence'] * x['predicted_change_pct']),
            reverse=True
        )

        return signals[:limit]

    async def continuous_analysis(self, symbols: List[str], interval_seconds: int = 1):
        """
        Continuously analyze symbols at specified interval
        This runs in the background
        """
        self.is_running = True
        logger.info(f"Starting continuous analysis for {len(symbols)} symbols")

        while self.is_running:
            try:
                # Analyze all symbols in parallel
                tasks = []
                for symbol in symbols:
                    # In real implementation, fetch real data here
                    # For now, use demo data
                    df = self._generate_demo_data()
                    current_price = df['close'].iloc[-1]
                    asset_type = self._detect_asset_type(symbol)

                    tasks.append(
                        self.analyze_symbol(symbol, df, current_price, asset_type)
                    )

                # Run all analyses in parallel
                await asyncio.gather(*tasks, return_exceptions=True)

                # Wait for next interval
                await asyncio.sleep(interval_seconds)

            except Exception as e:
                logger.error(f"Error in continuous analysis: {e}")
                await asyncio.sleep(interval_seconds)

    def stop_continuous_analysis(self):
        """Stop the continuous analysis loop"""
        self.is_running = False
        logger.info("Stopping continuous analysis")

    def _detect_asset_type(self, symbol: str) -> str:
        """Detect asset type from symbol"""
        if '-USD' in symbol or 'BTC' in symbol or 'ETH' in symbol:
            return 'crypto'
        elif '=X' in symbol:
            return 'forex'
        elif symbol in ['SPY', 'QQQ', 'DIA', 'IWM']:
            return 'index'
        else:
            return 'stock'

    def _generate_demo_data(self) -> pd.DataFrame:
        """Generate demo OHLCV data for testing"""
        dates = pd.date_range(end=datetime.now(), periods=200, freq='1min')
        base_price = 150 + np.random.randn() * 10

        data = []
        price = base_price
        for i in range(200):
            change = np.random.randn() * 2
            price = price + change

            open_price = price
            high = price + abs(np.random.randn())
            low = price - abs(np.random.randn())
            close = price + np.random.randn() * 0.5
            volume = np.random.randint(1000000, 10000000)

            data.append({
                'timestamp': dates[i],
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume
            })

        return pd.DataFrame(data)


# Global AI Engine Core instance
ai_core = AIEngineCore()
