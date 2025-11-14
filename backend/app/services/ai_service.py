from typing import List, Dict
from datetime import datetime
import random
from loguru import logger
import pandas as pd
import numpy as np

from ..models.trading_models import AgentAnalysis, AgentType, Signal, TradingDecision, OrderSide
from ..models.data_models import TechnicalIndicators, NewsItem
from ..database import SessionLocal
from ..db.repos.analysis_repository import AnalysisRepository


class AIAgent:
    """Base class for AI trading agents"""
    
    def __init__(self, agent_type: AgentType):
        self.agent_type = agent_type
        self.confidence_threshold = 0.6
    
    async def analyze(self, symbol: str, data: Dict) -> AgentAnalysis:
        """Analyze market data and generate signal"""
        raise NotImplementedError


class TechnicalAnalystAgent(AIAgent):
    """Enhanced technical analysis agent with multiple indicators"""
    
    def __init__(self):
        super().__init__(AgentType.TECHNICAL)
    
    def _convert_to_native_types(self, obj):
        """Convert numpy/pandas types to native Python types for JSON serialization"""
        if isinstance(obj, dict):
            return {key: self._convert_to_native_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_to_native_types(item) for item in obj]
        elif isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif pd.isna(obj):
            return None
        else:
            return obj
    
    def calculate_rsi(self, prices: pd.Series, window: int = 14) -> Dict:
        """Calculate RSI indicator"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            rsi_value = rsi.iloc[-1]
            
            if pd.isna(rsi_value):
                return {'value': None, 'signal': 'NEUTRAL', 'confidence': 0.0}
            
            signal = "NEUTRAL"
            confidence = 0.5
            
            if rsi_value < 30:
                signal = "BUY"
                confidence = min((30 - rsi_value) / 30, 1.0)
            elif rsi_value > 70:
                signal = "SELL"
                confidence = min((rsi_value - 70) / 30, 1.0)
            
            return {'value': rsi_value, 'signal': signal, 'confidence': confidence}
        except Exception as e:
            logger.error(f"Error calculating RSI: {e}")
            return {'value': None, 'signal': 'NEUTRAL', 'confidence': 0.0}
    
    def calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
        """Calculate MACD indicator"""
        try:
            ema_fast = prices.ewm(span=fast, adjust=False).mean()
            ema_slow = prices.ewm(span=slow, adjust=False).mean()
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal, adjust=False).mean()
            histogram = macd_line - signal_line
            
            macd_value = macd_line.iloc[-1]
            signal_value = signal_line.iloc[-1]
            histogram_value = histogram.iloc[-1]
            
            if pd.isna(macd_value) or pd.isna(signal_value):
                return {'macd': None, 'signal_line': None, 'histogram': None, 'signal': 'NEUTRAL', 'confidence': 0.0}
            
            macd_signal = "NEUTRAL"
            confidence = 0.5
            
            if macd_value > signal_value and histogram_value > 0:
                macd_signal = "BUY"
                confidence = min(abs(histogram_value) / abs(macd_value) if macd_value != 0 else 0.5, 1.0)
            elif macd_value < signal_value and histogram_value < 0:
                macd_signal = "SELL"
                confidence = min(abs(histogram_value) / abs(macd_value) if macd_value != 0 else 0.5, 1.0)
            
            return {
                'macd': macd_value,
                'signal_line': signal_value,
                'histogram': histogram_value,
                'signal': macd_signal,
                'confidence': confidence
            }
        except Exception as e:
            logger.error(f"Error calculating MACD: {e}")
            return {'macd': None, 'signal_line': None, 'histogram': None, 'signal': 'NEUTRAL', 'confidence': 0.0}
    
    def calculate_moving_averages(self, prices: pd.Series) -> Dict:
        """Calculate moving averages"""
        try:
            sma_20 = prices.rolling(window=20).mean().iloc[-1]
            sma_50 = prices.rolling(window=50).mean().iloc[-1]
            current_price = prices.iloc[-1]
            
            if pd.isna(sma_20) or pd.isna(sma_50):
                return {'sma_20': None, 'sma_50': None, 'signal': 'NEUTRAL', 'confidence': 0.0}
            
            signal = "NEUTRAL"
            confidence = 0.5
            
            if sma_20 > sma_50 and current_price > sma_20:
                signal = "BUY"
                confidence = min(((current_price - sma_20) / sma_20) * 10, 1.0)
            elif sma_20 < sma_50 and current_price < sma_20:
                signal = "SELL"
                confidence = min(((sma_20 - current_price) / sma_20) * 10, 1.0)
            
            return {
                'sma_20': sma_20,
                'sma_50': sma_50,
                'current_price': current_price,
                'signal': signal,
                'confidence': confidence
            }
        except Exception as e:
            logger.error(f"Error calculating moving averages: {e}")
            return {'sma_20': None, 'sma_50': None, 'signal': 'NEUTRAL', 'confidence': 0.0}
    
    def calculate_bollinger_bands(self, prices: pd.Series, window: int = 20, num_std: int = 2) -> Dict:
        """Calculate Bollinger Bands"""
        try:
            middle_band = prices.rolling(window=window).mean()
            std = prices.rolling(window=window).std()
            upper_band = middle_band + (std * num_std)
            lower_band = middle_band - (std * num_std)
            
            current_price = prices.iloc[-1]
            upper = upper_band.iloc[-1]
            middle = middle_band.iloc[-1]
            lower = lower_band.iloc[-1]
            
            if pd.isna(upper) or pd.isna(lower) or pd.isna(middle):
                return {'upper': None, 'middle': None, 'lower': None, 'signal': 'NEUTRAL', 'confidence': 0.0}
            
            signal = "NEUTRAL"
            confidence = 0.5
            
            if current_price < lower:
                signal = "BUY"
                confidence = min((lower - current_price) / (middle - lower) if (middle - lower) > 0 else 0.5, 1.0)
            elif current_price > upper:
                signal = "SELL"
                confidence = min((current_price - upper) / (upper - middle) if (upper - middle) > 0 else 0.5, 1.0)
            
            return {
                'upper': upper,
                'middle': middle,
                'lower': lower,
                'current_price': current_price,
                'signal': signal,
                'confidence': confidence
            }
        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands: {e}")
            return {'upper': None, 'middle': None, 'lower': None, 'signal': 'NEUTRAL', 'confidence': 0.0}
    
    def calculate_stochastic(self, high: pd.Series, low: pd.Series, close: pd.Series, k_window: int = 14, d_window: int = 3) -> Dict:
        """Calculate Stochastic Oscillator"""
        try:
            lowest_low = low.rolling(window=k_window).min()
            highest_high = high.rolling(window=k_window).max()
            
            k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
            d_percent = k_percent.rolling(window=d_window).mean()
            
            k_current = k_percent.iloc[-1]
            d_current = d_percent.iloc[-1]
            
            if pd.isna(k_current) or pd.isna(d_current):
                return {'k': None, 'd': None, 'signal': 'NEUTRAL', 'confidence': 0.0}
            
            signal = "NEUTRAL"
            confidence = 0.5
            
            if k_current < 20 and k_current > d_current:
                signal = "BUY"
                confidence = min((20 - k_current) / 20, 1.0)
            elif k_current > 80 and k_current < d_current:
                signal = "SELL"
                confidence = min((k_current - 80) / 20, 1.0)
            
            return {
                'k': k_current,
                'd': d_current,
                'signal': signal,
                'confidence': confidence
            }
        except Exception as e:
            logger.error(f"Error calculating Stochastic: {e}")
            return {'k': None, 'd': None, 'signal': 'NEUTRAL', 'confidence': 0.0}
    
    def calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> Dict:
        """Calculate Average True Range"""
        try:
            tr1 = high - low
            tr2 = abs(high - close.shift())
            tr3 = abs(low - close.shift())
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(window=window).mean()
            
            atr_value = atr.iloc[-1]
            atr_mean = atr.mean()
            
            if pd.isna(atr_value) or pd.isna(atr_mean):
                return {'atr': None, 'volatility': 'UNKNOWN'}
            
            volatility = 'HIGH' if atr_value > atr_mean else 'NORMAL'
            
            return {
                'atr': atr_value,
                'atr_mean': atr_mean,
                'volatility': volatility
            }
        except Exception as e:
            logger.error(f"Error calculating ATR: {e}")
            return {'atr': None, 'volatility': 'UNKNOWN'}
    
    def analyze_volume(self, volume: pd.Series, prices: pd.Series, window: int = 20) -> Dict:
        """Analyze volume trends"""
        try:
            avg_volume = volume.rolling(window=window).mean()
            current_volume = volume.iloc[-1]
            avg_vol = avg_volume.iloc[-1]
            price_change = prices.pct_change().iloc[-1]
            
            if pd.isna(current_volume) or pd.isna(avg_vol) or pd.isna(price_change):
                return {'current': None, 'average': None, 'ratio': None, 'signal': 'NEUTRAL'}
            
            ratio = current_volume / avg_vol if avg_vol > 0 else 1.0
            signal = "NEUTRAL"
            
            if ratio > 1.5:
                if price_change > 0:
                    signal = "BUY"
                elif price_change < 0:
                    signal = "SELL"
            
            return {
                'current': current_volume,
                'average': avg_vol,
                'ratio': ratio,
                'price_change': price_change,
                'signal': signal
            }
        except Exception as e:
            logger.error(f"Error analyzing volume: {e}")
            return {'current': None, 'average': None, 'ratio': None, 'signal': 'NEUTRAL'}
    
    async def analyze(self, symbol: str, data: Dict) -> AgentAnalysis:
        """Enhanced technical analysis with multiple indicators"""
        try:
            # Import data service here to avoid circular import
            from ..services.data_service import data_service
            
            # Fetch historical market data
            market_data = await data_service.get_market_data(symbol, timeframe="1D")
            
            if not market_data or len(market_data) < 50:
                logger.warning(f"Insufficient market data for {symbol}")
                return AgentAnalysis(
                    agent_type=self.agent_type,
                    symbol=symbol,
                    signal=Signal.HOLD,
                    confidence=0.0,
                    reasoning="Insufficient historical data for analysis"
                )
            
            # Convert to pandas Series
            df = pd.DataFrame([{
                'open': bar.open,
                'high': bar.high,
                'low': bar.low,
                'close': bar.close,
                'volume': bar.volume
            } for bar in market_data])
            
            closes = df['close']
            highs = df['high']
            lows = df['low']
            volumes = df['volume']
            
            # Calculate all indicators
            indicators = {
                'rsi': self.calculate_rsi(closes),
                'macd': self.calculate_macd(closes),
                'moving_averages': self.calculate_moving_averages(closes),
                'bollinger_bands': self.calculate_bollinger_bands(closes),
                'stochastic': self.calculate_stochastic(highs, lows, closes),
                'atr': self.calculate_atr(highs, lows, closes),
                'volume': self.analyze_volume(volumes, closes)
            }
            
            # Aggregate signals
            signals = []
            confidence_scores = []
            reasoning_parts = []
            
            for indicator_name, indicator_data in indicators.items():
                if 'signal' in indicator_data and indicator_data['signal'] != 'NEUTRAL':
                    signals.append(indicator_data['signal'])
                    conf = indicator_data.get('confidence', 0.5)
                    confidence_scores.append(conf)
                    
                    # Add to reasoning
                    if indicator_name == 'rsi' and indicator_data.get('value'):
                        reasoning_parts.append(f"RSI {indicator_data['signal'].lower()} ({indicator_data['value']:.1f})")
                    elif indicator_name == 'macd':
                        reasoning_parts.append(f"MACD {indicator_data['signal'].lower()}")
                    elif indicator_name == 'bollinger_bands':
                        reasoning_parts.append(f"BB {indicator_data['signal'].lower()}")
                    elif indicator_name == 'stochastic':
                        reasoning_parts.append(f"Stoch {indicator_data['signal'].lower()}")
                    elif indicator_name == 'volume':
                        reasoning_parts.append(f"Volume {indicator_data['signal'].lower()}")
            
            # Calculate overall recommendation
            buy_count = signals.count('BUY')
            sell_count = signals.count('SELL')
            
            if len(signals) == 0:
                final_signal = Signal.HOLD
                final_confidence = 0.5
                reasoning = "All indicators neutral"
            elif buy_count > sell_count and buy_count >= 2:
                final_signal = Signal.BUY if buy_count < 4 else Signal.STRONG_BUY
                buy_confidences = [c for s, c in zip(signals, confidence_scores) if s == 'BUY']
                final_confidence = sum(buy_confidences) / len(buy_confidences) if buy_confidences else 0.5
            elif sell_count > buy_count and sell_count >= 2:
                final_signal = Signal.SELL if sell_count < 4 else Signal.STRONG_SELL
                sell_confidences = [c for s, c in zip(signals, confidence_scores) if s == 'SELL']
                final_confidence = sum(sell_confidences) / len(sell_confidences) if sell_confidences else 0.5
            else:
                final_signal = Signal.HOLD
                final_confidence = 0.5
            
            reasoning = f"{buy_count} buy, {sell_count} sell signals"
            if reasoning_parts:
                reasoning += f": {'; '.join(reasoning_parts[:3])}"
            
            # Convert indicators to JSON-serializable format
            serializable_indicators = self._convert_to_native_types(indicators)
            
            return AgentAnalysis(
                agent_type=self.agent_type,
                symbol=symbol,
                signal=final_signal,
                confidence=min(final_confidence, 0.95),
                reasoning=reasoning,
                metadata={
                    'indicator_count': len([s for s in signals if s != 'NEUTRAL']),
                    'buy_signals': buy_count,
                    'sell_signals': sell_count,
                    'indicators': serializable_indicators
                }
            )
        except Exception as e:
            logger.error(f"Error in technical analysis for {symbol}: {e}")
            return AgentAnalysis(
                agent_type=self.agent_type,
                symbol=symbol,
                signal=Signal.HOLD,
                confidence=0.0,
                reasoning=f"Analysis error: {str(e)}"
            )


class NewsAnalystAgent(AIAgent):
    """News sentiment analysis agent"""
    
    def __init__(self):
        super().__init__(AgentType.NEWS)
    
    async def analyze(self, symbol: str, data: Dict) -> AgentAnalysis:
        """Analyze news sentiment"""
        news: List[NewsItem] = data.get('news', [])
        
        if not news:
            return AgentAnalysis(
                agent_type=self.agent_type,
                symbol=symbol,
                signal=Signal.HOLD,
                confidence=0.0,
                reasoning="No recent news available"
            )
        
        # Calculate average sentiment
        sentiments = [item.sentiment_score for item in news if item.sentiment_score is not None]
        
        if not sentiments:
            return AgentAnalysis(
                agent_type=self.agent_type,
                symbol=symbol,
                signal=Signal.HOLD,
                confidence=0.3,
                reasoning=f"{len(news)} news items, sentiment unavailable"
            )
        
        avg_sentiment = sum(sentiments) / len(sentiments)
        
        if avg_sentiment > 0.6:
            signal = Signal.STRONG_BUY
            confidence = min(0.85, 0.6 + avg_sentiment * 0.2)
            reasoning = f"Very positive news sentiment ({avg_sentiment:.2f}) from {len(news)} articles"
        elif avg_sentiment > 0.2:
            signal = Signal.BUY
            confidence = 0.7
            reasoning = f"Positive news sentiment ({avg_sentiment:.2f}) from {len(news)} articles"
        elif avg_sentiment < -0.6:
            signal = Signal.STRONG_SELL
            confidence = min(0.85, 0.6 + abs(avg_sentiment) * 0.2)
            reasoning = f"Very negative news sentiment ({avg_sentiment:.2f}) from {len(news)} articles"
        elif avg_sentiment < -0.2:
            signal = Signal.SELL
            confidence = 0.7
            reasoning = f"Negative news sentiment ({avg_sentiment:.2f}) from {len(news)} articles"
        else:
            signal = Signal.HOLD
            confidence = 0.5
            reasoning = f"Neutral news sentiment ({avg_sentiment:.2f}) from {len(news)} articles"
        
        return AgentAnalysis(
            agent_type=self.agent_type,
            symbol=symbol,
            signal=signal,
            confidence=confidence,
            reasoning=reasoning,
            metadata={'news_count': len(news), 'avg_sentiment': avg_sentiment}
        )


class FundamentalAnalystAgent(AIAgent):
    """Fundamental analysis agent"""
    
    def __init__(self):
        super().__init__(AgentType.FUNDAMENTAL)
    
    async def analyze(self, symbol: str, data: Dict) -> AgentAnalysis:
        """Analyze fundamentals"""
        # Simplified fundamental analysis
        # In production, this would analyze P/E ratio, revenue growth, etc.
        
        fundamentals = data.get('fundamentals', {})
        
        if not fundamentals:
            return AgentAnalysis(
                agent_type=self.agent_type,
                symbol=symbol,
                signal=Signal.HOLD,
                confidence=0.0,
                reasoning="No fundamental data available"
            )
        
        # Demo scoring
        score = random.uniform(-1, 1)
        
        if score > 0.5:
            signal = Signal.BUY
            confidence = 0.75
            reasoning = "Strong fundamentals: healthy financials and growth"
        elif score < -0.5:
            signal = Signal.SELL
            confidence = 0.75
            reasoning = "Weak fundamentals: concerning financial metrics"
        else:
            signal = Signal.HOLD
            confidence = 0.6
            reasoning = "Mixed fundamentals: neutral outlook"
        
        return AgentAnalysis(
            agent_type=self.agent_type,
            symbol=symbol,
            signal=signal,
            confidence=confidence,
            reasoning=reasoning
        )


class RiskManagerAgent(AIAgent):
    """Risk management agent"""
    
    def __init__(self, max_position_size: float = 0.1, max_daily_loss: float = 0.05):
        super().__init__(AgentType.RISK)
        self.max_position_size = max_position_size
        self.max_daily_loss = max_daily_loss
    
    async def analyze(self, symbol: str, data: Dict) -> AgentAnalysis:
        """Assess risk"""
        portfolio_value = data.get('portfolio_value', 100000)
        daily_pnl = data.get('daily_pnl', 0)
        current_positions = data.get('current_positions', [])
        proposed_quantity = data.get('proposed_quantity', 0)
        current_price = data.get('current_price', 0)
        
        risks = []
        risk_level = "LOW"
        
        # Check daily loss limit
        daily_loss_pct = abs(daily_pnl) / portfolio_value if portfolio_value > 0 else 0
        if daily_loss_pct > self.max_daily_loss:
            risks.append(f"Daily loss limit exceeded ({daily_loss_pct*100:.1f}%)")
            risk_level = "CRITICAL"
        
        # Check position size
        proposed_value = proposed_quantity * current_price
        position_pct = proposed_value / portfolio_value if portfolio_value > 0 else 0
        if position_pct > self.max_position_size:
            risks.append(f"Position size too large ({position_pct*100:.1f}%)")
            risk_level = "HIGH" if risk_level != "CRITICAL" else risk_level
        
        # Check concentration
        existing_position = next((p for p in current_positions if p.get('symbol') == symbol), None)
        if existing_position:
            risks.append("Already have position in this symbol")
        
        if not risks:
            signal = Signal.BUY  # No risk concerns
            confidence = 0.8
            reasoning = "Risk assessment passed: within all limits"
        elif risk_level == "CRITICAL":
            signal = Signal.STRONG_SELL  # Reject trade
            confidence = 0.95
            reasoning = f"CRITICAL RISK: {'; '.join(risks)}"
        else:
            signal = Signal.HOLD  # Caution
            confidence = 0.7
            reasoning = f"Risk concerns: {'; '.join(risks)}"
        
        return AgentAnalysis(
            agent_type=self.agent_type,
            symbol=symbol,
            signal=signal,
            confidence=confidence,
            reasoning=reasoning,
            metadata={'risk_level': risk_level, 'risks': risks}
        )


class MultiAgentOrchestrator:
    """Orchestrates multiple AI agents to make trading decisions"""
    
    def __init__(self):
        self.agents = [
            TechnicalAnalystAgent(),
            NewsAnalystAgent(),
            FundamentalAnalystAgent(),
            RiskManagerAgent()
        ]
        logger.info(f"Initialized {len(self.agents)} AI agents")
    
    async def get_trading_decision(self, symbol: str, market_data: Dict) -> TradingDecision:
        """Get consensus trading decision from all agents"""
        logger.info(f"Getting trading decision for {symbol}")
        
        # Collect analyses from all agents
        analyses = []
        db = SessionLocal()
        try:
            for agent in self.agents:
                try:
                    analysis = await agent.analyze(symbol, market_data)
                    analyses.append(analysis)
                    logger.debug(f"{agent.agent_type.value}: {analysis.signal.value} (confidence: {analysis.confidence:.2f})")
                    
                    # Get indicators from metadata if available (enhanced technical analyst)
                    # Otherwise use the basic indicators from market_data
                    db_indicators = analysis.metadata.get('indicators', {}) if analysis.metadata else {}
                    if not db_indicators:
                        # Fallback to market_data indicators, converting to dict safely
                        indicators_obj = market_data.get('indicators')
                        if indicators_obj and hasattr(indicators_obj, 'model_dump'):
                            db_indicators = indicators_obj.model_dump(mode='json')
                        elif indicators_obj and hasattr(indicators_obj, 'dict'):
                            db_indicators = indicators_obj.dict()
                        else:
                            db_indicators = {}
                    
                    AnalysisRepository.create_analysis(
                        db,
                        symbol=symbol,
                        agent_type=analysis.agent_type.value,
                        signal=analysis.signal.value,
                        confidence=analysis.confidence,
                        reasoning=analysis.reasoning,
                        indicators=db_indicators,
                        market_conditions={'current_price': market_data.get('current_price')},
                        risk_assessment=analysis.metadata if analysis.metadata else {}
                    )
                except Exception as e:
                    logger.error(f"Error in {agent.agent_type.value} agent: {e}")
        finally:
            db.close()
        
        # Weighted voting
        signal_weights = {
            Signal.STRONG_BUY: 2,
            Signal.BUY: 1,
            Signal.HOLD: 0,
            Signal.SELL: -1,
            Signal.STRONG_SELL: -2
        }
        
        total_score = 0
        total_confidence = 0
        for analysis in analyses:
            weight = signal_weights[analysis.signal]
            # Risk manager has veto power
            if analysis.agent_type == AgentType.RISK and analysis.signal == Signal.STRONG_SELL:
                weight *= 3
            total_score += weight * analysis.confidence
            total_confidence += analysis.confidence
        
        avg_confidence = total_confidence / len(analyses) if analyses else 0
        
        # Determine final action
        if total_score > 1.5:
            action = OrderSide.BUY
            confidence = min(0.9, avg_confidence)
        elif total_score < -1.5:
            action = OrderSide.SELL
            confidence = min(0.9, avg_confidence)
        else:
            # No clear consensus, default to hold (no trade)
            return None
        
        # Calculate quantity (simplified)
        portfolio_value = market_data.get('portfolio_value', 100000)
        current_price = market_data.get('current_price', 1)
        max_position_value = portfolio_value * 0.05  # 5% position
        quantity = max_position_value / current_price if current_price > 0 else 0
        
        # Create risk assessment
        risk_analysis = next((a for a in analyses if a.agent_type == AgentType.RISK), None)
        risk_assessment = {
            'level': risk_analysis.metadata.get('risk_level', 'UNKNOWN') if risk_analysis else 'UNKNOWN',
            'concerns': risk_analysis.metadata.get('risks', []) if risk_analysis else []
        }
        
        decision = TradingDecision(
            symbol=symbol,
            action=action,
            quantity=quantity,
            price=current_price,
            confidence=confidence,
            agent_votes=analyses,
            risk_assessment=risk_assessment
        )
        
        logger.info(f"Decision for {symbol}: {action.value} {quantity:.2f} shares (confidence: {confidence:.2f})")
        return decision


# Global orchestrator instance
orchestrator = MultiAgentOrchestrator()
