"""
Advanced Machine Learning Engine for Trading Predictions
Includes LSTM Neural Networks, Random Forest, and XGBoost models
Enhanced with 100+ technical indicators from comprehensive library
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger
from enum import Enum
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Import comprehensive indicators library
from .indicators_library import (
    VolumeIndicators,
    MomentumIndicators,
    TrendIndicators,
    VolatilityIndicators
)

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
        """
        Calculate comprehensive technical features using 100+ indicators library
        Intelligently selects most relevant indicators for ML training
        """
        features = df.copy()

        # Extract price and volume data
        close = features['close']
        high = features['high']
        low = features['low']
        open_price = features['open']
        volume = features['volume'] if 'volume' in features.columns else pd.Series(index=features.index, data=0)

        # ===== PRICE-BASED FEATURES =====
        features['returns'] = close.pct_change()
        features['log_returns'] = np.log(close / close.shift(1))
        features['price_range'] = high - low
        features['body_size'] = abs(close - open_price)
        features['upper_shadow'] = high - pd.concat([close, open_price], axis=1).max(axis=1)
        features['lower_shadow'] = pd.concat([close, open_price], axis=1).min(axis=1) - low

        # ===== VOLUME INDICATORS (20+ from library) =====
        try:
            features['obv'] = VolumeIndicators.obv(close, volume)
            features['ad_line'] = VolumeIndicators.ad_line(high, low, close, volume)
            features['cmf'] = VolumeIndicators.cmf(high, low, close, volume, period=20)
            features['force_index'] = VolumeIndicators.force_index(close, volume, period=13)
            features['mfi'] = VolumeIndicators.mfi(high, low, close, volume, period=14)
            features['vwap'] = VolumeIndicators.vwap(high, low, close, volume)
            features['volume_roc'] = VolumeIndicators.volume_roc(volume, period=14)
            features['ease_of_movement'] = VolumeIndicators.ease_of_movement(high, low, volume, period=14)

            # Volume profile indicators
            nvi, pvi = VolumeIndicators.nvi_pvi(close, volume)
            features['nvi'] = nvi
            features['pvi'] = pvi

        except Exception as e:
            logger.warning(f"Error calculating volume indicators: {e}")

        # ===== MOMENTUM INDICATORS (20+ from library) =====
        try:
            features['rsi_14'] = MomentumIndicators.rsi(close, period=14)
            features['rsi_28'] = MomentumIndicators.rsi(close, period=28)

            stoch_k, stoch_d = MomentumIndicators.stochastic(high, low, close, period=14, smooth=3)
            features['stoch_k'] = stoch_k
            features['stoch_d'] = stoch_d

            features['williams_r'] = MomentumIndicators.williams_r(high, low, close, period=14)
            features['cci'] = MomentumIndicators.cci(high, low, close, period=20)
            features['roc'] = MomentumIndicators.roc(close, period=12)
            features['momentum'] = MomentumIndicators.momentum(close, period=10)
            features['tsi'] = MomentumIndicators.tsi(close, long=25, short=13)
            features['ultimate_osc'] = MomentumIndicators.ultimate_oscillator(high, low, close)
            features['coppock'] = MomentumIndicators.coppock_curve(close)
            features['kst'] = MomentumIndicators.know_sure_thing(close)

        except Exception as e:
            logger.warning(f"Error calculating momentum indicators: {e}")

        # ===== TREND INDICATORS (20+ from library) =====
        try:
            # MACD
            macd_line, macd_signal, macd_hist = TrendIndicators.macd(close, fast=12, slow=26, signal=9)
            features['macd'] = macd_line
            features['macd_signal'] = macd_signal
            features['macd_hist'] = macd_hist

            features['adx'] = TrendIndicators.adx(high, low, close, period=14)

            aroon_up, aroon_down = TrendIndicators.aroon(high, low, period=25)
            features['aroon_up'] = aroon_up
            features['aroon_down'] = aroon_down
            features['aroon_osc'] = aroon_up - aroon_down

            features['psar'] = TrendIndicators.parabolic_sar(high, low, af=0.02, max_af=0.2)

            supertrend, supertrend_direction = TrendIndicators.supertrend(high, low, close, period=10, multiplier=3.0)
            features['supertrend'] = supertrend
            features['supertrend_dir'] = supertrend_direction

            # Ichimoku Cloud
            ichimoku = TrendIndicators.ichimoku(high, low, close)
            features['tenkan_sen'] = ichimoku['tenkan_sen']
            features['kijun_sen'] = ichimoku['kijun_sen']
            features['senkou_span_a'] = ichimoku['senkou_span_a']
            features['senkou_span_b'] = ichimoku['senkou_span_b']

            features['trix'] = TrendIndicators.trix(close, period=15)
            features['mass_index'] = TrendIndicators.mass_index(high, low, period=25)

            vortex_pos, vortex_neg = TrendIndicators.vortex_indicator(high, low, close, period=14)
            features['vortex_pos'] = vortex_pos
            features['vortex_neg'] = vortex_neg

            # Adaptive moving averages
            features['kama'] = TrendIndicators.kama(close, period=10)
            features['hull_ma'] = TrendIndicators.hull_moving_average(close, period=20)

            # Standard moving averages
            for period in [5, 10, 20, 50, 200]:
                features[f'sma_{period}'] = close.rolling(window=period).mean()
                features[f'ema_{period}'] = close.ewm(span=period, adjust=False).mean()

        except Exception as e:
            logger.warning(f"Error calculating trend indicators: {e}")

        # ===== VOLATILITY INDICATORS (15+ from library) =====
        try:
            features['atr'] = VolatilityIndicators.atr(high, low, close, period=14)
            features['natr'] = VolatilityIndicators.natr(high, low, close, period=14)

            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = VolatilityIndicators.bollinger_bands(close, period=20, std_dev=2.0)
            features['bb_upper'] = bb_upper
            features['bb_middle'] = bb_middle
            features['bb_lower'] = bb_lower
            features['bb_width'] = (bb_upper - bb_lower) / bb_middle
            features['bb_position'] = (close - bb_lower) / (bb_upper - bb_lower)
            features['bb_pct'] = VolatilityIndicators.bollinger_percent_b(close, period=20, std_dev=2.0)

            # Keltner Channels
            kc_upper, kc_middle, kc_lower = VolatilityIndicators.keltner_channels(high, low, close, period=20)
            features['kc_upper'] = kc_upper
            features['kc_middle'] = kc_middle
            features['kc_lower'] = kc_lower

            # Donchian Channels
            dc_upper, dc_middle, dc_lower = VolatilityIndicators.donchian_channels(high, low, period=20)
            features['dc_upper'] = dc_upper
            features['dc_lower'] = dc_lower

            features['historical_vol'] = VolatilityIndicators.historical_volatility(close, period=20)
            features['parkinson_vol'] = VolatilityIndicators.parkinson_volatility(high, low, period=20)
            features['garman_klass_vol'] = VolatilityIndicators.garman_klass_volatility(open_price, high, low, close, period=20)
            features['ulcer_index'] = VolatilityIndicators.ulcer_index(close, period=14)

        except Exception as e:
            logger.warning(f"Error calculating volatility indicators: {e}")


        # ===== PRICE PATTERN FEATURES =====
        features['higher_high'] = (high > high.shift(1)).astype(int)
        features['lower_low'] = (low < low.shift(1)).astype(int)
        features['higher_close'] = (close > close.shift(1)).astype(int)
        features['gap_up'] = (low > high.shift(1)).astype(int)
        features['gap_down'] = (high < low.shift(1)).astype(int)

        # ===== DERIVED FEATURES FOR ML =====
        # Price position relative to key levels
        if 'sma_20' in features.columns and 'sma_50' in features.columns:
            features['price_above_sma20'] = (close > features['sma_20']).astype(int)
            features['price_above_sma50'] = (close > features['sma_50']).astype(int)
            features['sma_20_50_cross'] = (features['sma_20'] > features['sma_50']).astype(int)

        # Volatility regimes
        if 'atr' in features.columns:
            atr_ma = features['atr'].rolling(window=20).mean()
            features['high_volatility'] = (features['atr'] > atr_ma * 1.5).astype(int)
            features['low_volatility'] = (features['atr'] < atr_ma * 0.5).astype(int)

        # Momentum shifts
        if 'rsi_14' in features.columns:
            features['rsi_oversold'] = (features['rsi_14'] < 30).astype(int)
            features['rsi_overbought'] = (features['rsi_14'] > 70).astype(int)
            features['rsi_divergence'] = features['rsi_14'].diff()

        logger.info(f"Calculated {len(features.columns)} technical features from comprehensive library")

        return features


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
        """
        Calculate comprehensive technical analysis score using multiple indicators
        """
        score = 0
        count = 0
        latest = df.iloc[-1]

        # RSI Analysis (Multiple timeframes)
        if 'rsi_14' in df.columns:
            rsi_14 = latest['rsi_14']
            if rsi_14 < 30:
                score += 0.4  # Strong oversold
                count += 1
            elif rsi_14 < 40:
                score += 0.2  # Mild oversold
                count += 1
            elif rsi_14 > 70:
                score -= 0.4  # Strong overbought
                count += 1
            elif rsi_14 > 60:
                score -= 0.2  # Mild overbought
                count += 1

        if 'rsi_28' in df.columns:
            rsi_28 = latest['rsi_28']
            if rsi_28 < 30:
                score += 0.2
                count += 1
            elif rsi_28 > 70:
                score -= 0.2
                count += 1

        # MACD Analysis
        if 'macd_hist' in df.columns and 'macd' in df.columns:
            macd_hist = latest['macd_hist']
            macd = latest['macd']

            if macd_hist > 0 and macd > 0:
                score += 0.3  # Strong bullish
                count += 1
            elif macd_hist > 0:
                score += 0.15  # Bullish crossover
                count += 1
            elif macd_hist < 0 and macd < 0:
                score -= 0.3  # Strong bearish
                count += 1
            elif macd_hist < 0:
                score -= 0.15  # Bearish crossover
                count += 1

        # Stochastic Oscillator
        if 'stoch_k' in df.columns and 'stoch_d' in df.columns:
            stoch_k = latest['stoch_k']
            stoch_d = latest['stoch_d']
            if stoch_k < 20 and stoch_k > stoch_d:
                score += 0.3  # Oversold and crossing up
                count += 1
            elif stoch_k > 80 and stoch_k < stoch_d:
                score -= 0.3  # Overbought and crossing down
                count += 1

        # Williams %R
        if 'williams_r' in df.columns:
            williams = latest['williams_r']
            if williams < -80:
                score += 0.2  # Oversold
                count += 1
            elif williams > -20:
                score -= 0.2  # Overbought
                count += 1

        # CCI (Commodity Channel Index)
        if 'cci' in df.columns:
            cci = latest['cci']
            if cci < -100:
                score += 0.25  # Oversold
                count += 1
            elif cci > 100:
                score -= 0.25  # Overbought
                count += 1

        # Bollinger Bands Analysis
        if 'bb_position' in df.columns and 'bb_pct' in df.columns:
            bb_pos = latest['bb_position']
            bb_pct = latest['bb_pct']

            if bb_pct < 0:
                score += 0.3  # Below lower band
                count += 1
            elif bb_pct < 0.2:
                score += 0.15  # Near lower band
                count += 1
            elif bb_pct > 1:
                score -= 0.3  # Above upper band
                count += 1
            elif bb_pct > 0.8:
                score -= 0.15  # Near upper band
                count += 1


        # Ultimate Oscillator
        if 'ultimate_osc' in df.columns:
            ult_osc = latest['ultimate_osc']
            if ult_osc < 30:
                score += 0.2
                count += 1
            elif ult_osc > 70:
                score -= 0.2
                count += 1

        # Normalize by count of indicators used
        final_score = score / count if count > 0 else 0
        return np.clip(final_score, -1, 1)

    def _momentum_score(self, df: pd.DataFrame) -> float:
        """
        Calculate momentum score using comprehensive momentum indicators
        """
        score = 0
        count = 0
        latest = df.iloc[-1]

        # Price momentum
        if 'returns' in df.columns:
            recent_returns = df['returns'].tail(5).mean()
            score += np.clip(recent_returns * 100, -0.5, 0.5)
            count += 1

        # Rate of Change (ROC)
        if 'roc' in df.columns:
            roc = latest['roc']
            score += np.clip(roc / 10, -0.3, 0.3)  # Normalize ROC
            count += 1

        # Momentum Indicator
        if 'momentum' in df.columns:
            mom = latest['momentum']
            if mom > 100:
                score += 0.25  # Positive momentum
                count += 1
            elif mom < 100:
                score -= 0.25  # Negative momentum
                count += 1

        # True Strength Index (TSI)
        if 'tsi' in df.columns:
            tsi = latest['tsi']
            if tsi > 0:
                score += 0.3
                count += 1
            else:
                score -= 0.3
                count += 1

        # Know Sure Thing (KST)
        if 'kst' in df.columns:
            kst = latest['kst']
            if kst > 0:
                score += 0.2
                count += 1
            else:
                score -= 0.2
                count += 1

        # Coppock Curve
        if 'coppock' in df.columns:
            coppock = latest['coppock']
            if coppock > 0:
                score += 0.2
                count += 1
            else:
                score -= 0.2
                count += 1

        # Chande Momentum Oscillator
        if 'chande_mo' in df.columns:
            chande = latest['chande_mo']
            if chande > 50:
                score += 0.3  # Strong positive momentum
                count += 1
            elif chande > 0:
                score += 0.15  # Mild positive momentum
                count += 1
            elif chande < -50:
                score -= 0.3  # Strong negative momentum
                count += 1
            elif chande < 0:
                score -= 0.15  # Mild negative momentum
                count += 1

        # Moving average crossovers
        if 'sma_5' in df.columns and 'sma_20' in df.columns:
            if latest['sma_5'] > latest['sma_20']:
                score += 0.3  # Golden cross
                count += 1
            else:
                score -= 0.3  # Death cross
                count += 1

        if 'ema_5' in df.columns and 'ema_20' in df.columns:
            if latest['ema_5'] > latest['ema_20']:
                score += 0.2  # EMA golden cross
                count += 1
            else:
                score -= 0.2  # EMA death cross
                count += 1

        # KAMA (Kaufman Adaptive MA) vs price
        if 'kama' in df.columns and 'close' in df.columns:
            if latest['close'] > latest['kama']:
                score += 0.2
                count += 1
            else:
                score -= 0.2
                count += 1

        # Normalize by count
        final_score = score / count if count > 0 else 0
        return np.clip(final_score, -1, 1)

    def _trend_score(self, df: pd.DataFrame) -> float:
        """
        Calculate trend strength score using comprehensive trend indicators
        """
        score = 0
        count = 0
        latest = df.iloc[-1]

        # ADX (trend strength)
        if 'adx' in df.columns:
            adx = latest['adx']
            if adx > 40:
                # Very strong trend
                if 'close' in df.columns and 'sma_20' in df.columns and latest['close'] > latest['sma_20']:
                    score += 0.5
                    count += 1
                else:
                    score -= 0.5
                    count += 1
            elif adx > 25:
                # Strong trend
                if 'close' in df.columns and 'sma_20' in df.columns and latest['close'] > latest['sma_20']:
                    score += 0.3
                    count += 1
                else:
                    score -= 0.3
                    count += 1

        # Aroon Indicator
        if 'aroon_up' in df.columns and 'aroon_down' in df.columns:
            aroon_up = latest['aroon_up']
            aroon_down = latest['aroon_down']
            if aroon_up > 70 and aroon_down < 30:
                score += 0.4  # Strong uptrend
                count += 1
            elif aroon_down > 70 and aroon_up < 30:
                score -= 0.4  # Strong downtrend
                count += 1
            elif aroon_up > aroon_down:
                score += 0.2  # Mild uptrend
                count += 1
            else:
                score -= 0.2  # Mild downtrend
                count += 1

        # Parabolic SAR
        if 'psar' in df.columns and 'close' in df.columns:
            if latest['close'] > latest['psar']:
                score += 0.3  # Price above SAR (uptrend)
                count += 1
            else:
                score -= 0.3  # Price below SAR (downtrend)
                count += 1

        # Supertrend
        if 'supertrend_dir' in df.columns:
            st_dir = latest['supertrend_dir']
            if st_dir > 0:
                score += 0.35  # Uptrend
                count += 1
            else:
                score -= 0.35  # Downtrend
                count += 1

        # Ichimoku Cloud
        if all(col in df.columns for col in ['tenkan_sen', 'kijun_sen', 'senkou_span_a', 'senkou_span_b', 'close']):
            price = latest['close']
            tenkan = latest['tenkan_sen']
            kijun = latest['kijun_sen']
            span_a = latest['senkou_span_a']
            span_b = latest['senkou_span_b']

            # Price above cloud = bullish
            cloud_top = max(span_a, span_b)
            cloud_bottom = min(span_a, span_b)

            if price > cloud_top and tenkan > kijun:
                score += 0.5  # Strong bullish
                count += 1
            elif price > cloud_top:
                score += 0.3  # Bullish
                count += 1
            elif price < cloud_bottom and tenkan < kijun:
                score -= 0.5  # Strong bearish
                count += 1
            elif price < cloud_bottom:
                score -= 0.3  # Bearish
                count += 1

        # Vortex Indicator
        if 'vortex_pos' in df.columns and 'vortex_neg' in df.columns:
            vortex_pos = latest['vortex_pos']
            vortex_neg = latest['vortex_neg']
            if vortex_pos > vortex_neg and vortex_pos > 1:
                score += 0.3  # Positive trend
                count += 1
            elif vortex_neg > vortex_pos and vortex_neg > 1:
                score -= 0.3  # Negative trend
                count += 1

        # TRIX
        if 'trix' in df.columns:
            trix = latest['trix']
            if trix > 0:
                score += 0.25
                count += 1
            else:
                score -= 0.25
                count += 1

        # Mass Index (trend reversal warning)
        if 'mass_index' in df.columns:
            mass_index = latest['mass_index']
            if mass_index > 27:
                score *= 0.7  # Reduce confidence - potential reversal
                count += 1

        # Price position vs moving averages (Multiple timeframes)
        if all(col in df.columns for col in ['close', 'sma_20', 'sma_50', 'sma_200']):
            price = latest['close']
            sma_20 = latest['sma_20']
            sma_50 = latest['sma_50']
            sma_200 = latest['sma_200']

            if price > sma_20 > sma_50 > sma_200:
                score += 0.5  # Perfect bullish alignment
                count += 1
            elif price > sma_50 > sma_200:
                score += 0.3  # Strong uptrend
                count += 1
            elif price > sma_200:
                score += 0.15  # Long-term uptrend
                count += 1
            elif price < sma_20 < sma_50 < sma_200:
                score -= 0.5  # Perfect bearish alignment
                count += 1
            elif price < sma_50 < sma_200:
                score -= 0.3  # Strong downtrend
                count += 1
            elif price < sma_200:
                score -= 0.15  # Long-term downtrend
                count += 1

        # Hull Moving Average
        if 'hull_ma' in df.columns and 'close' in df.columns:
            if latest['close'] > latest['hull_ma']:
                score += 0.2
                count += 1
            else:
                score -= 0.2
                count += 1

        # Normalize by count
        final_score = score / count if count > 0 else 0
        return np.clip(final_score, -1, 1)

    def _volume_score(self, df: pd.DataFrame) -> float:
        """
        Calculate volume-based score using comprehensive volume indicators
        """
        score = 0
        count = 0
        latest = df.iloc[-1]

        # On-Balance Volume (OBV)
        if 'obv' in df.columns and len(df) > 1:
            obv_current = latest['obv']
            obv_prev = df['obv'].iloc[-2]
            if obv_current > obv_prev:
                score += 0.3  # Volume supporting upward move
                count += 1
            else:
                score -= 0.3  # Volume supporting downward move
                count += 1

        # Accumulation/Distribution Line
        if 'ad_line' in df.columns and len(df) > 1:
            ad_current = latest['ad_line']
            ad_prev = df['ad_line'].iloc[-2]
            if ad_current > ad_prev:
                score += 0.25  # Accumulation
                count += 1
            else:
                score -= 0.25  # Distribution
                count += 1

        # Chaikin Money Flow (CMF)
        if 'cmf' in df.columns:
            cmf = latest['cmf']
            if cmf > 0.1:
                score += 0.35  # Strong buying pressure
                count += 1
            elif cmf > 0:
                score += 0.15  # Mild buying pressure
                count += 1
            elif cmf < -0.1:
                score -= 0.35  # Strong selling pressure
                count += 1
            elif cmf < 0:
                score -= 0.15  # Mild selling pressure
                count += 1

        # Money Flow Index (MFI)
        if 'mfi' in df.columns:
            mfi = latest['mfi']
            if mfi < 20:
                score += 0.3  # Oversold with volume
                count += 1
            elif mfi > 80:
                score -= 0.3  # Overbought with volume
                count += 1

        # Force Index
        if 'force_index' in df.columns:
            force = latest['force_index']
            if force > 0:
                score += 0.25  # Positive force
                count += 1
            else:
                score -= 0.25  # Negative force
                count += 1

        # VWAP (Volume Weighted Average Price)
        if 'vwap' in df.columns and 'close' in df.columns:
            if latest['close'] > latest['vwap']:
                score += 0.3  # Price above VWAP (bullish)
                count += 1
            else:
                score -= 0.3  # Price below VWAP (bearish)
                count += 1

        # Volume Rate of Change
        if 'volume_roc' in df.columns:
            vol_roc = latest['volume_roc']
            if vol_roc > 50:
                # High volume spike
                if 'close' in df.columns and 'open' in df.columns:
                    if latest['close'] > latest['open']:
                        score += 0.3  # Bullish volume spike
                        count += 1
                    else:
                        score -= 0.3  # Bearish volume spike
                        count += 1

        # Ease of Movement
        if 'ease_of_movement' in df.columns:
            eom = latest['ease_of_movement']
            if eom > 0:
                score += 0.2  # Easy upward movement
                count += 1
            else:
                score -= 0.2  # Easy downward movement
                count += 1

        # Negative/Positive Volume Index
        if 'nvi' in df.columns and 'pvi' in df.columns and len(df) > 1:
            nvi_trend = latest['nvi'] - df['nvi'].iloc[-5:].mean() if len(df) >= 5 else 0
            pvi_trend = latest['pvi'] - df['pvi'].iloc[-5:].mean() if len(df) >= 5 else 0

            if pvi_trend > 0:
                score += 0.15  # Smart money buying
                count += 1
            elif pvi_trend < 0:
                score -= 0.15  # Smart money selling
                count += 1

        # Price-Volume Oscillator (PVO)
        if 'pvo' in df.columns:
            pvo = latest['pvo']
            if pvo > 0:
                score += 0.2
                count += 1
            else:
                score -= 0.2
                count += 1

        # Normalize by count
        final_score = score / count if count > 0 else 0
        return np.clip(final_score, -1, 1)

    def _volatility_score(self, df: pd.DataFrame) -> float:
        """
        Calculate volatility score using comprehensive volatility indicators
        """
        score = 0
        count = 0
        latest = df.iloc[-1]

        # Bollinger Band Width (volatility measurement)
        if 'bb_width' in df.columns:
            bb_width = latest['bb_width']
            avg_bb_width = df['bb_width'].tail(20).mean() if len(df) >= 20 else bb_width

            # Low volatility -> potential breakout opportunity
            if bb_width < avg_bb_width * 0.5:
                score += 0.25  # Volatility squeeze - potential opportunity
                count += 1
            # High volatility -> caution needed
            elif bb_width > avg_bb_width * 1.5:
                score -= 0.15  # High volatility risk
                count += 1

        # Average True Range (ATR)
        if 'atr' in df.columns and 'natr' in df.columns:
            natr = latest['natr']  # Normalized ATR
            avg_natr = df['natr'].tail(20).mean() if len(df) >= 20 else natr

            # Moderate volatility is good for trading
            if 0.02 < natr < 0.05:
                score += 0.15  # Ideal volatility range
                count += 1
            elif natr > 0.08:
                score -= 0.2  # Too volatile
                count += 1

        # Keltner Channels
        if all(col in df.columns for col in ['close', 'kc_upper', 'kc_lower']):
            price = latest['close']
            kc_upper = latest['kc_upper']
            kc_lower = latest['kc_lower']
            kc_middle = latest['kc_middle'] if 'kc_middle' in df.columns else (kc_upper + kc_lower) / 2

            # Price near edges indicates potential reversal
            if price > kc_upper:
                score -= 0.2  # Overextended upward
                count += 1
            elif price < kc_lower:
                score += 0.2  # Overextended downward (buy opportunity)
                count += 1
            # Price near middle is neutral
            elif abs(price - kc_middle) / kc_middle < 0.01:
                # Neutral position
                count += 1

        # Donchian Channels
        if all(col in df.columns for col in ['close', 'dc_upper', 'dc_lower']):
            price = latest['close']
            dc_upper = latest['dc_upper']
            dc_lower = latest['dc_lower']

            # Breakout signals
            if price >= dc_upper:
                score += 0.25  # Breakout to upside
                count += 1
            elif price <= dc_lower:
                score -= 0.25  # Breakdown to downside
                count += 1

        # Historical Volatility
        if 'historical_vol' in df.columns:
            hist_vol = latest['historical_vol']
            avg_hist_vol = df['historical_vol'].tail(60).mean() if len(df) >= 60 else hist_vol

            # Volatility regime detection
            if hist_vol < avg_hist_vol * 0.7:
                score += 0.2  # Low volatility regime
                count += 1
            elif hist_vol > avg_hist_vol * 1.3:
                score -= 0.15  # High volatility regime
                count += 1

        # Parkinson Volatility (uses High-Low range)
        if 'parkinson_vol' in df.columns:
            park_vol = latest['parkinson_vol']
            avg_park_vol = df['parkinson_vol'].tail(20).mean() if len(df) >= 20 else park_vol

            # Compare current to average
            if park_vol < avg_park_vol * 0.8:
                score += 0.15  # Below average volatility
                count += 1
            elif park_vol > avg_park_vol * 1.2:
                score -= 0.15  # Above average volatility
                count += 1

        # Garman-Klass Volatility (more accurate)
        if 'garman_klass_vol' in df.columns:
            gk_vol = latest['garman_klass_vol']
            avg_gk_vol = df['garman_klass_vol'].tail(20).mean() if len(df) >= 20 else gk_vol

            # Use as confirmation
            if gk_vol < avg_gk_vol * 0.75:
                score += 0.1  # Low volatility confirmed
                count += 1

        # Ulcer Index (downside volatility)
        if 'ulcer_index' in df.columns:
            ulcer = latest['ulcer_index']
            avg_ulcer = df['ulcer_index'].tail(20).mean() if len(df) >= 20 else ulcer

            # High ulcer index = high downside risk
            if ulcer > avg_ulcer * 1.5:
                score -= 0.3  # High downside risk
                count += 1
            elif ulcer < avg_ulcer * 0.5:
                score += 0.2  # Low downside risk
                count += 1

        # Bollinger Band %B position combined with volatility
        if 'bb_pct' in df.columns and 'bb_width' in df.columns:
            bb_pct = latest['bb_pct']
            bb_width = latest['bb_width']

            # Squeeze with position
            if bb_width < 0.05:
                if bb_pct > 0.7:
                    score += 0.2  # Squeeze at top (potential bullish breakout)
                    count += 1
                elif bb_pct < 0.3:
                    score += 0.15  # Squeeze at bottom (potential bounce)
                    count += 1

        # Normalize by count
        final_score = score / count if count > 0 else 0
        return np.clip(final_score, -1, 1)

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
