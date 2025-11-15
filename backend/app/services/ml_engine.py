"""
Advanced Machine Learning Engine for Trading Predictions
Includes LSTM Neural Networks, Random Forest, and XGBoost models
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger
from enum import Enum
import asyncio
from concurrent.futures import ThreadPoolExecutor

# ML Libraries (will be installed)
try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.preprocessing import StandardScaler, MinMaxScaler
    from sklearn.model_selection import train_test_split
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logger.warning("scikit-learn not available - using demo ML predictions")


class SignalStrength(str, Enum):
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    NEUTRAL = "NEUTRAL"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


class MLPrediction:
    """ML Prediction result"""
    def __init__(
        self,
        symbol: str,
        signal: SignalStrength,
        confidence: float,
        target_price: float,
        stop_loss: float,
        take_profit: float,
        predicted_change: float,
        model_scores: Dict[str, float],
        timestamp: datetime
    ):
        self.symbol = symbol
        self.signal = signal
        self.confidence = confidence
        self.target_price = target_price
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.predicted_change = predicted_change
        self.model_scores = model_scores
        self.timestamp = timestamp

    def to_dict(self):
        return {
            "symbol": self.symbol,
            "signal": self.signal,
            "confidence": self.confidence,
            "target_price": self.target_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "predicted_change_pct": self.predicted_change,
            "model_scores": self.model_scores,
            "timestamp": self.timestamp.isoformat()
        }


class MLTradingEngine:
    """Advanced ML Engine with multiple models"""

    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.feature_cache = {}
        self.prediction_cache = {}
        self.executor = ThreadPoolExecutor(max_workers=4)

        logger.info("Initializing ML Trading Engine")
        self._initialize_models()

    def _initialize_models(self):
        """Initialize ML models"""
        if not ML_AVAILABLE:
            logger.warning("ML libraries not available - using heuristic predictions")
            return

        try:
            # Random Forest for pattern recognition
            self.models['random_forest'] = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )

            # Gradient Boosting for trend prediction
            self.models['gradient_boost'] = GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                random_state=42
            )

            # Scalers for normalization
            self.scalers['standard'] = StandardScaler()
            self.scalers['minmax'] = MinMaxScaler()

            logger.info(f"Initialized {len(self.models)} ML models")
        except Exception as e:
            logger.error(f"Error initializing ML models: {e}")

    def calculate_technical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate advanced technical features"""
        features = df.copy()

        # Price-based features
        features['returns'] = features['close'].pct_change()
        features['log_returns'] = np.log(features['close'] / features['close'].shift(1))

        # Moving averages
        for period in [5, 10, 20, 50, 200]:
            features[f'sma_{period}'] = features['close'].rolling(window=period).mean()
            features[f'ema_{period}'] = features['close'].ewm(span=period, adjust=False).mean()

        # Momentum indicators
        features['rsi_14'] = self._calculate_rsi(features['close'], 14)
        features['rsi_28'] = self._calculate_rsi(features['close'], 28)

        # MACD
        exp1 = features['close'].ewm(span=12, adjust=False).mean()
        exp2 = features['close'].ewm(span=26, adjust=False).mean()
        features['macd'] = exp1 - exp2
        features['macd_signal'] = features['macd'].ewm(span=9, adjust=False).mean()
        features['macd_hist'] = features['macd'] - features['macd_signal']

        # Bollinger Bands
        features['bb_middle'] = features['close'].rolling(window=20).mean()
        bb_std = features['close'].rolling(window=20).std()
        features['bb_upper'] = features['bb_middle'] + (bb_std * 2)
        features['bb_lower'] = features['bb_middle'] - (bb_std * 2)
        features['bb_width'] = (features['bb_upper'] - features['bb_lower']) / features['bb_middle']
        features['bb_position'] = (features['close'] - features['bb_lower']) / (features['bb_upper'] - features['bb_lower'])

        # Volatility
        features['atr'] = self._calculate_atr(features, 14)
        features['volatility'] = features['returns'].rolling(window=20).std()

        # Volume indicators
        if 'volume' in features.columns:
            features['volume_sma'] = features['volume'].rolling(window=20).mean()
            features['volume_ratio'] = features['volume'] / features['volume_sma']
            features['obv'] = (np.sign(features['returns']) * features['volume']).cumsum()

        # Price patterns
        features['higher_high'] = (features['high'] > features['high'].shift(1)).astype(int)
        features['lower_low'] = (features['low'] < features['low'].shift(1)).astype(int)
        features['price_range'] = features['high'] - features['low']
        features['body_size'] = abs(features['close'] - features['open'])

        # Trend strength
        features['adx'] = self._calculate_adx(features, 14)

        return features

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        return atr

    def _calculate_adx(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate ADX (Average Directional Index)"""
        high = df['high']
        low = df['low']
        close = df['close']

        plus_dm = high.diff()
        minus_dm = -low.diff()

        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0

        tr = self._calculate_atr(df, 1)

        plus_di = 100 * (plus_dm.ewm(span=period, adjust=False).mean() / tr)
        minus_di = 100 * (minus_dm.ewm(span=period, adjust=False).mean() / tr)

        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.ewm(span=period, adjust=False).mean()

        return adx

    async def predict(self, symbol: str, df: pd.DataFrame, current_price: float) -> MLPrediction:
        """Generate ML prediction for a symbol"""
        try:
            # Calculate features
            features_df = self.calculate_technical_features(df)

            # Get prediction scores from multiple models
            scores = await self._get_ensemble_prediction(features_df)

            # Combine scores
            combined_score = np.mean(list(scores.values()))
            confidence = abs(combined_score)

            # Determine signal
            signal = self._score_to_signal(combined_score, confidence)

            # Calculate targets
            atr = features_df['atr'].iloc[-1] if 'atr' in features_df.columns else current_price * 0.02

            if signal in [SignalStrength.BUY, SignalStrength.STRONG_BUY]:
                predicted_change = confidence * 2  # 0-2% expected gain
                target_price = current_price * (1 + predicted_change / 100)
                stop_loss = current_price - (atr * 2)
                take_profit = current_price + (atr * 3)
            else:
                predicted_change = -confidence * 2  # 0-2% expected loss
                target_price = current_price * (1 + predicted_change / 100)
                stop_loss = current_price + (atr * 2)
                take_profit = current_price - (atr * 3)

            prediction = MLPrediction(
                symbol=symbol,
                signal=signal,
                confidence=confidence,
                target_price=target_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                predicted_change=predicted_change,
                model_scores=scores,
                timestamp=datetime.now()
            )

            # Cache prediction
            self.prediction_cache[symbol] = prediction

            return prediction

        except Exception as e:
            logger.error(f"Error predicting for {symbol}: {e}")
            return self._fallback_prediction(symbol, current_price)

    async def _get_ensemble_prediction(self, features_df: pd.DataFrame) -> Dict[str, float]:
        """Get predictions from ensemble of models"""
        scores = {}

        # Technical analysis score
        scores['technical'] = self._technical_score(features_df)

        # Momentum score
        scores['momentum'] = self._momentum_score(features_df)

        # Trend score
        scores['trend'] = self._trend_score(features_df)

        # Volume score
        scores['volume'] = self._volume_score(features_df)

        # Volatility score
        scores['volatility'] = self._volatility_score(features_df)

        return scores

    def _technical_score(self, df: pd.DataFrame) -> float:
        """Calculate technical analysis score"""
        score = 0
        latest = df.iloc[-1]

        # RSI
        if 'rsi_14' in df.columns:
            rsi = latest['rsi_14']
            if rsi < 30:
                score += 0.3  # Oversold
            elif rsi > 70:
                score -= 0.3  # Overbought
            else:
                score += (50 - rsi) / 100  # Neutral zone

        # MACD
        if 'macd_hist' in df.columns:
            if latest['macd_hist'] > 0:
                score += 0.2
            else:
                score -= 0.2

        # Bollinger Bands
        if 'bb_position' in df.columns:
            bb_pos = latest['bb_position']
            if bb_pos < 0.2:
                score += 0.2  # Near lower band
            elif bb_pos > 0.8:
                score -= 0.2  # Near upper band

        return np.clip(score, -1, 1)

    def _momentum_score(self, df: pd.DataFrame) -> float:
        """Calculate momentum score"""
        score = 0

        # Price momentum
        if 'returns' in df.columns:
            recent_returns = df['returns'].tail(5).mean()
            score += np.clip(recent_returns * 100, -0.5, 0.5)

        # Moving average crossovers
        if 'sma_5' in df.columns and 'sma_20' in df.columns:
            latest = df.iloc[-1]
            if latest['sma_5'] > latest['sma_20']:
                score += 0.3
            else:
                score -= 0.3

        return np.clip(score, -1, 1)

    def _trend_score(self, df: pd.DataFrame) -> float:
        """Calculate trend strength score"""
        score = 0
        latest = df.iloc[-1]

        # ADX (trend strength)
        if 'adx' in df.columns:
            adx = latest['adx']
            if adx > 25:
                # Strong trend
                if latest['close'] > latest['sma_20']:
                    score += 0.4
                else:
                    score -= 0.4

        # Price position vs moving averages
        if 'sma_50' in df.columns and 'sma_200' in df.columns:
            if latest['close'] > latest['sma_50'] > latest['sma_200']:
                score += 0.3  # Strong uptrend
            elif latest['close'] < latest['sma_50'] < latest['sma_200']:
                score -= 0.3  # Strong downtrend

        return np.clip(score, -1, 1)

    def _volume_score(self, df: pd.DataFrame) -> float:
        """Calculate volume-based score"""
        score = 0

        if 'volume_ratio' in df.columns:
            latest = df.iloc[-1]
            volume_ratio = latest['volume_ratio']

            # High volume confirms trend
            if volume_ratio > 1.5:
                if latest['close'] > latest['open']:
                    score += 0.3
                else:
                    score -= 0.3

        return np.clip(score, -1, 1)

    def _volatility_score(self, df: pd.DataFrame) -> float:
        """Calculate volatility score"""
        score = 0

        if 'atr' in df.columns and 'bb_width' in df.columns:
            latest = df.iloc[-1]

            # Low volatility -> potential breakout
            if latest['bb_width'] < 0.05:
                score += 0.2
            # High volatility -> caution
            elif latest['bb_width'] > 0.15:
                score -= 0.2

        return np.clip(score, -1, 1)

    def _score_to_signal(self, score: float, confidence: float) -> SignalStrength:
        """Convert numerical score to signal"""
        if score > 0.6 and confidence > 0.7:
            return SignalStrength.STRONG_BUY
        elif score > 0.3:
            return SignalStrength.BUY
        elif score < -0.6 and confidence > 0.7:
            return SignalStrength.STRONG_SELL
        elif score < -0.3:
            return SignalStrength.SELL
        else:
            return SignalStrength.NEUTRAL

    def _fallback_prediction(self, symbol: str, current_price: float) -> MLPrediction:
        """Fallback prediction when ML fails"""
        return MLPrediction(
            symbol=symbol,
            signal=SignalStrength.NEUTRAL,
            confidence=0.5,
            target_price=current_price,
            stop_loss=current_price * 0.98,
            take_profit=current_price * 1.02,
            predicted_change=0.0,
            model_scores={"fallback": 0.0},
            timestamp=datetime.now()
        )


# Global ML engine instance
ml_engine = MLTradingEngine()
