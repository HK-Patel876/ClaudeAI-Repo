"""
Backtesting Engine for AI Trading System
Tests historical performance of 75+ indicators and AI predictions
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger
from dataclasses import dataclass, asdict
import json

from .ai_engine_core import ai_core
from .data_service import data_service


@dataclass
class Trade:
    """Individual trade record"""
    entry_time: str
    exit_time: Optional[str]
    symbol: str
    signal: str
    entry_price: float
    exit_price: Optional[float]
    quantity: float
    stop_loss: float
    take_profit: float
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None
    status: str = "open"  # open, win, loss, stopped
    confidence: float = 0.0
    hold_time_hours: Optional[float] = None


@dataclass
class BacktestResult:
    """Complete backtest results"""
    symbol: str
    start_date: str
    end_date: str
    initial_capital: float
    final_capital: float
    total_return_pct: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    profit_factor: float
    sharpe_ratio: float
    max_drawdown: float
    max_drawdown_pct: float
    avg_hold_time_hours: float
    trades_per_day: float
    best_signal_type: str
    signal_performance: Dict[str, Dict]
    equity_curve: List[Dict]
    trades: List[Dict]


class BacktestingEngine:
    """
    Advanced backtesting engine that tests AI trading signals
    against historical data
    """

    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.commission_pct = 0.001  # 0.1% commission per trade
        logger.info(f"Backtesting engine initialized with ${initial_capital:,.2f}")

    async def run_backtest(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        position_size_pct: float = 0.1,  # 10% of capital per trade
        use_stop_loss: bool = True,
        use_take_profit: bool = True,
        min_confidence: float = 0.6
    ) -> BacktestResult:
        """
        Run complete backtest for a symbol over date range

        Args:
            symbol: Trading symbol
            start_date: Start date for backtest
            end_date: End date for backtest
            position_size_pct: Percentage of capital per trade
            use_stop_loss: Whether to use stop losses
            use_take_profit: Whether to use take profits
            min_confidence: Minimum signal confidence to trade
        """
        logger.info(f"Starting backtest for {symbol} from {start_date} to {end_date}")

        # Get historical data
        historical_data = await self._get_historical_data(symbol, start_date, end_date)

        if not historical_data or len(historical_data) < 100:
            raise ValueError(f"Insufficient historical data for {symbol}")

        # Initialize tracking variables
        capital = self.initial_capital
        trades: List[Trade] = []
        equity_curve = [{"date": start_date.isoformat(), "equity": capital}]
        open_position: Optional[Trade] = None

        # Process each day
        df = pd.DataFrame(historical_data)
        df['date'] = pd.to_datetime(df['timestamp'])

        logger.info(f"Processing {len(df)} data points for backtest")

        for i in range(60, len(df)):  # Start at 60 to have enough data for indicators
            current_data = df.iloc[:i+1].copy()
            current_row = df.iloc[i]
            current_price = current_row['close']
            current_date = current_row['date']

            # Check if we need to exit open position
            if open_position:
                exit_signal, exit_reason = self._check_exit_conditions(
                    open_position, current_price, use_stop_loss, use_take_profit
                )

                if exit_signal:
                    # Close position
                    open_position.exit_time = current_date.isoformat()
                    open_position.exit_price = current_price

                    # Calculate P&L
                    if open_position.signal in ['BUY', 'STRONG_BUY']:
                        pnl = (current_price - open_position.entry_price) * open_position.quantity
                    else:
                        pnl = (open_position.entry_price - current_price) * open_position.quantity

                    # Subtract commission
                    pnl -= (open_position.entry_price * open_position.quantity * self.commission_pct)
                    pnl -= (current_price * open_position.quantity * self.commission_pct)

                    open_position.pnl = pnl
                    open_position.pnl_pct = (pnl / (open_position.entry_price * open_position.quantity)) * 100
                    open_position.status = exit_reason

                    # Calculate hold time
                    entry_time = pd.to_datetime(open_position.entry_time)
                    exit_time = pd.to_datetime(open_position.exit_time)
                    open_position.hold_time_hours = (exit_time - entry_time).total_seconds() / 3600

                    # Update capital
                    capital += pnl

                    trades.append(open_position)
                    open_position = None

                    # Record equity
                    equity_curve.append({
                        "date": current_date.isoformat(),
                        "equity": capital
                    })

            # Check for new entry signals (only if no open position)
            if not open_position and i % 5 == 0:  # Check every 5 bars to avoid overtrading
                try:
                    # Get AI signal
                    signal = await ai_core.analyze_symbol(
                        symbol=symbol,
                        df=current_data,
                        current_price=current_price,
                        asset_type='stocks'
                    )

                    # Only trade if confidence is high enough
                    if signal.confidence >= min_confidence and signal.signal != 'NEUTRAL':
                        # Calculate position size
                        position_value = capital * position_size_pct
                        quantity = position_value / current_price

                        # Create new trade
                        open_position = Trade(
                            entry_time=current_date.isoformat(),
                            exit_time=None,
                            symbol=symbol,
                            signal=signal.signal,
                            entry_price=current_price,
                            exit_price=None,
                            quantity=quantity,
                            stop_loss=signal.stop_loss,
                            take_profit=signal.take_profit,
                            confidence=signal.confidence
                        )

                except Exception as e:
                    logger.debug(f"Error generating signal at {current_date}: {e}")
                    continue

        # Close any remaining open position
        if open_position:
            open_position.exit_time = df.iloc[-1]['date'].isoformat()
            open_position.exit_price = df.iloc[-1]['close']
            open_position.status = "end_of_period"

            if open_position.signal in ['BUY', 'STRONG_BUY']:
                pnl = (open_position.exit_price - open_position.entry_price) * open_position.quantity
            else:
                pnl = (open_position.entry_price - open_position.exit_price) * open_position.quantity

            pnl -= (open_position.entry_price * open_position.quantity * self.commission_pct)
            pnl -= (open_position.exit_price * open_position.quantity * self.commission_pct)

            open_position.pnl = pnl
            open_position.pnl_pct = (pnl / (open_position.entry_price * open_position.quantity)) * 100
            capital += pnl
            trades.append(open_position)

        # Calculate performance metrics
        result = self._calculate_metrics(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.initial_capital,
            final_capital=capital,
            trades=trades,
            equity_curve=equity_curve
        )

        logger.info(f"Backtest complete: {result.total_trades} trades, {result.win_rate:.1f}% win rate, {result.total_return_pct:.2f}% return")

        return result

    def _check_exit_conditions(
        self,
        trade: Trade,
        current_price: float,
        use_stop_loss: bool,
        use_take_profit: bool
    ) -> Tuple[bool, str]:
        """Check if position should be exited"""

        if trade.signal in ['BUY', 'STRONG_BUY']:
            # Long position
            if use_stop_loss and current_price <= trade.stop_loss:
                return True, "stopped"
            if use_take_profit and current_price >= trade.take_profit:
                return True, "win"
        else:
            # Short position
            if use_stop_loss and current_price >= trade.stop_loss:
                return True, "stopped"
            if use_take_profit and current_price <= trade.take_profit:
                return True, "win"

        return False, ""

    async def _get_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict]:
        """Fetch historical OHLCV data"""
        try:
            # Try to get data from data service
            data = await data_service.get_market_data(symbol, timeframe="1D")

            # Filter by date range
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]

            return df.to_dict('records')
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            # Generate synthetic data for demo
            return self._generate_synthetic_data(symbol, start_date, end_date)

    def _generate_synthetic_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict]:
        """Generate synthetic OHLCV data for backtesting demo"""
        dates = pd.date_range(start=start_date, end=end_date, freq='D')

        # Start price
        base_price = 100.0

        data = []
        price = base_price

        for date in dates:
            # Random walk with slight upward bias
            change = np.random.normal(0.001, 0.02)  # 0.1% drift, 2% volatility
            price = price * (1 + change)

            # Generate OHLC
            high = price * (1 + abs(np.random.normal(0, 0.01)))
            low = price * (1 - abs(np.random.normal(0, 0.01)))
            open_price = price * (1 + np.random.normal(0, 0.005))
            close = price
            volume = np.random.uniform(1000000, 10000000)

            data.append({
                'timestamp': date.isoformat(),
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume
            })

        return data

    def _calculate_metrics(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float,
        final_capital: float,
        trades: List[Trade],
        equity_curve: List[Dict]
    ) -> BacktestResult:
        """Calculate comprehensive performance metrics"""

        if not trades:
            return BacktestResult(
                symbol=symbol,
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                initial_capital=initial_capital,
                final_capital=final_capital,
                total_return_pct=0.0,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0.0,
                avg_win=0.0,
                avg_loss=0.0,
                largest_win=0.0,
                largest_loss=0.0,
                profit_factor=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                max_drawdown_pct=0.0,
                avg_hold_time_hours=0.0,
                trades_per_day=0.0,
                best_signal_type="N/A",
                signal_performance={},
                equity_curve=equity_curve,
                trades=[]
            )

        # Basic metrics
        total_return_pct = ((final_capital - initial_capital) / initial_capital) * 100

        # Winning and losing trades
        winning_trades = [t for t in trades if t.pnl and t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl and t.pnl < 0]

        win_rate = (len(winning_trades) / len(trades)) * 100 if trades else 0

        avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.pnl for t in losing_trades]) if losing_trades else 0

        largest_win = max([t.pnl for t in winning_trades]) if winning_trades else 0
        largest_loss = min([t.pnl for t in losing_trades]) if losing_trades else 0

        # Profit factor
        total_profit = sum([t.pnl for t in winning_trades]) if winning_trades else 0
        total_loss = abs(sum([t.pnl for t in losing_trades])) if losing_trades else 1
        profit_factor = total_profit / total_loss if total_loss > 0 else 0

        # Sharpe ratio
        returns = [t.pnl_pct for t in trades if t.pnl_pct]
        sharpe_ratio = (np.mean(returns) / np.std(returns)) * np.sqrt(252) if len(returns) > 1 else 0

        # Max drawdown
        equity_values = [e['equity'] for e in equity_curve]
        peak = equity_values[0]
        max_dd = 0
        max_dd_pct = 0

        for equity in equity_values:
            if equity > peak:
                peak = equity
            dd = peak - equity
            dd_pct = (dd / peak) * 100 if peak > 0 else 0
            max_dd = max(max_dd, dd)
            max_dd_pct = max(max_dd_pct, dd_pct)

        # Average hold time
        hold_times = [t.hold_time_hours for t in trades if t.hold_time_hours]
        avg_hold_time_hours = np.mean(hold_times) if hold_times else 0

        # Trades per day
        days = (end_date - start_date).days
        trades_per_day = len(trades) / days if days > 0 else 0

        # Performance by signal type
        signal_performance = {}
        for signal_type in ['STRONG_BUY', 'BUY', 'SELL', 'STRONG_SELL']:
            signal_trades = [t for t in trades if t.signal == signal_type]
            if signal_trades:
                signal_wins = [t for t in signal_trades if t.pnl and t.pnl > 0]
                signal_performance[signal_type] = {
                    'total_trades': len(signal_trades),
                    'win_rate': (len(signal_wins) / len(signal_trades)) * 100,
                    'avg_pnl': np.mean([t.pnl for t in signal_trades]),
                    'total_pnl': sum([t.pnl for t in signal_trades])
                }

        # Find best signal type
        best_signal_type = max(
            signal_performance.items(),
            key=lambda x: x[1]['win_rate']
        )[0] if signal_performance else "N/A"

        return BacktestResult(
            symbol=symbol,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            initial_capital=initial_capital,
            final_capital=final_capital,
            total_return_pct=total_return_pct,
            total_trades=len(trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            largest_win=largest_win,
            largest_loss=largest_loss,
            profit_factor=profit_factor,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_dd,
            max_drawdown_pct=max_dd_pct,
            avg_hold_time_hours=avg_hold_time_hours,
            trades_per_day=trades_per_day,
            best_signal_type=best_signal_type,
            signal_performance=signal_performance,
            equity_curve=equity_curve,
            trades=[asdict(t) for t in trades]
        )


# Global backtesting engine instance
backtesting_engine = BacktestingEngine()
