"""Rule-based analysis system to reduce model dependency.

Provides technical analysis and trading signals without relying on LLM outputs.
Includes Indian market-specific patterns and logic.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional


class RuleBasedAnalyzer:
    """Rule-based technical analyzer for Indian markets."""
    
    def __init__(self):
        self.indian_market_rules = {
            "trading_hours": {"open": "09:15", "close": "15:30"},
            "settlement": "T+1",
            "circuit_limits": {"upper": 0.20, "lower": -0.20},
            "min_lot_size": 1,
        }
    
    def analyze_price_action(self, price_data: pd.DataFrame) -> Dict[str, any]:
        """Analyze price action using rule-based signals.
        
        Args:
            price_data: DataFrame with OHLCV data
            
        Returns:
            Dictionary with price action analysis
        """
        if price_data.empty or len(price_data) < 5:
            return {"error": "Insufficient data for analysis"}
        
        df = price_data.copy()
        latest = df.iloc[-1]
        previous = df.iloc[-2]
        
        # Calculate basic price metrics
        price_change = (latest['Close'] - previous['Close']) / previous['Close'] * 100
        high_low_range = latest['High'] - latest['Low']
        volume_avg = df['Volume'].tail(20).mean()
        volume_ratio = latest['Volume'] / volume_avg if volume_avg > 0 else 1
        
        # Indian market specific patterns
        gap_up = latest['Open'] > previous['High'] * 1.02  # 2% gap up
        gap_down = latest['Open'] < previous['Low'] * 0.98   # 2% gap down
        
        return {
            "price_change_pct": round(price_change, 2),
            "high_low_range": round(high_low_range, 2),
            "volume_ratio": round(volume_ratio, 2),
            "gap_up": gap_up,
            "gap_down": gap_down,
            "signal_strength": self._calculate_signal_strength(df),
            "trend_direction": self._determine_trend(df),
        }
    
    def calculate_technical_indicators(self, price_data: pd.DataFrame) -> Dict[str, float]:
        """Calculate key technical indicators using rule-based methods.
        
        Args:
            price_data: DataFrame with OHLCV data
            
        Returns:
            Dictionary with technical indicators
        """
        if price_data.empty or len(price_data) < 10:
            return {"error": "Insufficient data for indicators"}
        
        df = price_data.copy()

        # Moving averages
        df['EMA_10'] = df['Close'].ewm(span=10).mean()
        df['EMA_20'] = df['Close'].ewm(span=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['Close'].ewm(span=12).mean()
        exp2 = df['Close'].ewm(span=26).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
        
        # Bollinger Bands
        sma_20 = df['Close'].rolling(window=20).mean()
        std_20 = df['Close'].rolling(window=20).std()
        df['BB_Upper'] = sma_20 + (std_20 * 2)
        df['BB_Lower'] = sma_20 - (std_20 * 2)
        
        # ATR (Average True Range)
        high_low = df['High'] - df['Low']
        high_close_prev = (df['High'] - df['Close'].shift(1)).abs()
        low_close_prev = (df['Low'] - df['Close'].shift(1)).abs()
        true_range = pd.concat([high_low, high_close_prev, low_close_prev], axis=1).max(axis=1)
        df['ATR'] = true_range.rolling(window=14).mean()
        
        # Volume indicators
        df['VWAP'] = (df['Volume'] * df['Close']).cumsum() / df['Volume'].cumsum()
        df['Volume_SMA'] = df['Volume'].rolling(window=20).mean()
        df['Volume_Ratio'] = np.where(df['Volume_SMA'] > 0, df['Volume'] / df['Volume_SMA'], 1.0)
        
        latest = df.iloc[-1]
        
        return {
            "close": latest['Close'],
            "ema_10": latest['EMA_10'],
            "ema_20": latest['EMA_20'],
            "sma_50": latest['SMA_50'],
            "rsi": latest['RSI'],
            "macd": latest['MACD'],
            "macd_signal": latest['MACD_Signal'],
            "bb_upper": latest['BB_Upper'],
            "bb_lower": latest['BB_Lower'],
            "atr": latest['ATR'],
            "vwap": latest['VWAP'],
            "volume_sma": latest['Volume_SMA'],
            "volume_ratio": latest['Volume_Ratio'],
        }
    
    def generate_trading_signals(self, indicators: Dict[str, float]) -> Dict[str, any]:
        """Generate trading signals based on technical indicators.
        
        Args:
            indicators: Dictionary with technical indicator values
            
        Returns:
            Dictionary with trading signals
        """
        signals = {
            "buy_signals": [],
            "sell_signals": [],
            "hold_signals": [],
            "risk_level": "medium",
            "confidence": 0.5,
        }
        
        # Trend signals
        if indicators['ema_10'] > indicators['ema_20'] and indicators['close'] > indicators['sma_50']:
            signals["buy_signals"].append("Bullish trend (EMA crossover)")
            signals["confidence"] += 0.2
        
        if indicators['ema_10'] < indicators['ema_20'] and indicators['close'] < indicators['sma_50']:
            signals["sell_signals"].append("Bearish trend (EMA crossover)")
            signals["confidence"] -= 0.2
        
        # RSI signals
        if indicators['rsi'] < 30:
            signals["buy_signals"].append("Oversold (RSI < 30)")
            signals["confidence"] += 0.15
        elif indicators['rsi'] > 70:
            signals["sell_signals"].append("Overbought (RSI > 70)")
            signals["confidence"] -= 0.15
        
        # MACD signals
        if indicators['macd'] > indicators['macd_signal'] and indicators['macd'] > 0:
            signals["buy_signals"].append("MACD bullish crossover")
            signals["confidence"] += 0.1
        
        if indicators['macd'] < indicators['macd_signal'] and indicators['macd'] < 0:
            signals["sell_signals"].append("MACD bearish crossover")
            signals["confidence"] -= 0.1
        
        # Bollinger Band signals
        if indicators['close'] < indicators['bb_lower']:
            signals["buy_signals"].append("Below Bollinger Lower Band")
            signals["confidence"] += 0.1
        elif indicators['close'] > indicators['bb_upper']:
            signals["sell_signals"].append("Above Bollinger Upper Band")
            signals["confidence"] -= 0.1
        
        # Volume confirmation
        volume_ratio = indicators.get("volume_ratio", 1.0)
        if volume_ratio > 1.5:
            signals["confidence"] += 0.1
        
        # Risk assessment
        atr_pct = (indicators['atr'] / indicators['close']) * 100 if indicators['close'] > 0 else 0
        if atr_pct > 3:
            signals["risk_level"] = "high"
        elif atr_pct < 1:
            signals["risk_level"] = "low"
        
        # Clamp confidence
        signals["confidence"] = max(0, min(1, signals["confidence"]))
        
        return signals
    
    def calculate_support_resistance(self, price_data: pd.DataFrame) -> Dict[str, List[float]]:
        """Calculate support and resistance levels.
        
        Args:
            price_data: DataFrame with OHLCV data
            
        Returns:
            Dictionary with support and resistance levels
        """
        if price_data.empty or len(price_data) < 20:
            return {"error": "Insufficient data for S/R analysis"}
        
        # Find local maxima and minima
        highs = price_data['High'].rolling(window=5, center=True).max()
        lows = price_data['Low'].rolling(window=5, center=True).min()
        
        # Get significant levels
        resistance_levels = []
        support_levels = []
        
        for i in range(2, len(highs) - 2):
            if highs.iloc[i] == highs.iloc[i-2:i+3].max():
                resistance_levels.append(highs.iloc[i])
        
        for i in range(2, len(lows) - 2):
            if lows.iloc[i] == lows.iloc[i-2:i+3].min():
                support_levels.append(lows.iloc[i])
        
        # Get recent levels (last 50 periods)
        recent_resistance = sorted(set(resistance_levels[-50:]), reverse=True)[:5]
        recent_support = sorted(set(support_levels[-50:]))[:5]
        
        return {
            "resistance": recent_resistance,
            "support": recent_support,
        }
    
    def generate_entry_exit_points(self, indicators: Dict[str, float], 
                                support_resistance: Dict[str, List[float]]) -> Dict[str, any]:
        """Generate entry and exit points with stop-loss levels.
        
        Args:
            indicators: Dictionary with technical indicators
            support_resistance: Dictionary with S/R levels
            
        Returns:
            Dictionary with entry/exit recommendations
        """
        current_price = indicators['close']
        atr = indicators['atr']
        
        # Calculate stop-loss levels
        stop_loss_buy = current_price - (atr * 1.5)
        stop_loss_sell = current_price + (atr * 1.5)
        
        # Calculate targets
        if support_resistance.get("resistance") and len(support_resistance["resistance"]) > 0:
            nearest_resistance = min(support_resistance["resistance"])
            target_buy = nearest_resistance
        
        if support_resistance.get("support") and len(support_resistance["support"]) > 0:
            nearest_support = max(support_resistance["support"])
            target_sell = nearest_support
        
        return {
            "entry_buy": current_price,
            "stop_loss_buy": round(stop_loss_buy, 2),
            "target_buy": round(target_buy, 2) if 'target_buy' in locals() else None,
            "entry_sell": current_price,
            "stop_loss_sell": round(stop_loss_sell, 2),
            "target_sell": round(target_sell, 2) if 'target_sell' in locals() else None,
            "risk_reward_ratio": self._calculate_risk_reward(current_price, stop_loss_buy, target_buy) if 'target_buy' in locals() else None,
        }
    
    def _calculate_signal_strength(self, price_data: pd.DataFrame) -> float:
        """Calculate overall signal strength based on multiple factors."""
        if len(price_data) < 10:
            return 0.5
        
        # Price momentum
        price_momentum = (price_data['Close'].iloc[-1] - price_data['Close'].iloc[-5]) / price_data['Close'].iloc[-5]
        
        # Volume trend
        volume_trend = price_data['Volume'].tail(10).mean() / price_data['Volume'].tail(50).mean()
        
        # Volatility
        volatility = price_data['Close'].tail(20).std() / price_data['Close'].tail(20).mean()
        
        # Combine signals
        strength = 0.5  # Base strength
        
        if price_momentum > 0.02:  # 2% positive momentum
            strength += 0.2
        elif price_momentum < -0.02:
            strength -= 0.2
        
        if volume_trend > 1.2:  # High volume
            strength += 0.15
        
        if volatility > 0.03:  # High volatility
            strength += 0.1
        
        return max(0, min(1, strength))
    
    def _determine_trend(self, price_data: pd.DataFrame) -> str:
        """Determine trend direction based on moving averages."""
        if len(price_data) < 20:
            return "neutral"

        df = price_data.copy()
        if 'EMA_10' not in df:
            df['EMA_10'] = df['Close'].ewm(span=10).mean()
        if 'EMA_20' not in df:
            df['EMA_20'] = df['Close'].ewm(span=20).mean()
        if 'SMA_50' not in df:
            df['SMA_50'] = df['Close'].rolling(window=50).mean()

        latest = df.iloc[-1]
        if pd.isna(latest['EMA_10']) or pd.isna(latest['EMA_20']) or pd.isna(latest['SMA_50']):
            return "neutral"

        if latest['EMA_10'] > latest['EMA_20'] > latest['SMA_50']:
            return "strong_uptrend"
        elif latest['EMA_10'] < latest['EMA_20'] < latest['SMA_50']:
            return "strong_downtrend"
        elif latest['EMA_10'] > latest['EMA_20']:
            return "uptrend"
        elif latest['EMA_10'] < latest['EMA_20']:
            return "downtrend"
        else:
            return "neutral"
    
    def _calculate_risk_reward(self, entry: float, stop_loss: float, target: float) -> float:
        """Calculate risk-reward ratio."""
        risk = abs(entry - stop_loss)
        reward = abs(target - entry)
        return reward / risk if risk > 0 else 0


def create_rule_based_report(symbol: str, price_data: pd.DataFrame) -> str:
    """Create comprehensive rule-based analysis report.
    
    Args:
        symbol: Stock symbol
        price_data: DataFrame with OHLCV data
        
    Returns:
        Formatted analysis report
    """
    analyzer = RuleBasedAnalyzer()
    
    # Perform analysis
    price_action = analyzer.analyze_price_action(price_data)
    indicators = analyzer.calculate_technical_indicators(price_data)
    signals = analyzer.generate_trading_signals(indicators)
    support_resistance = analyzer.calculate_support_resistance(price_data)
    entry_exit = analyzer.generate_entry_exit_points(indicators, support_resistance)
    
    # Generate report
    report = f"""
# Rule-Based Technical Analysis for {symbol}
## Market Analysis (Indian Market Context)

### Price Action Analysis
- Current Price: ₹{indicators.get('close', 'N/A'):,.2f}
- Price Change: {price_action.get('price_change_pct', 0):+.2f}%
- Volume Ratio: {price_action.get('volume_ratio', 1):.2f}x average
- Gap Up: {'Yes' if price_action.get('gap_up') else 'No'}
- Gap Down: {'Yes' if price_action.get('gap_down') else 'No'}

### Technical Indicators
- EMA 10/20: ₹{indicators.get('ema_10', 0):.2f} / ₹{indicators.get('ema_20', 0):.2f}
- SMA 50: ₹{indicators.get('sma_50', 0):.2f}
- RSI: {indicators.get('rsi', 0):.1f}
- MACD: {indicators.get('macd', 0):.4f}
- ATR: ₹{indicators.get('atr', 0):.2f}
- Bollinger Bands: ₹{indicators.get('bb_lower', 0):.2f} - ₹{indicators.get('bb_upper', 0):.2f}

### Trading Signals
**Buy Signals ({len(signals.get('buy_signals', []))}):**
{chr(10).join(f"- {signal}" for signal in signals.get('buy_signals', []))}

**Sell Signals ({len(signals.get('sell_signals', []))}):**
{chr(10).join(f"- {signal}" for signal in signals.get('sell_signals', []))}

### Support & Resistance Levels
**Resistance Levels:**
{chr(10).join(f"- ₹{level:,.2f}" for level in support_resistance.get('resistance', []))}

**Support Levels:**
{chr(10).join(f"- ₹{level:,.2f}" for level in support_resistance.get('support', []))}

### Entry & Exit Strategy
**For Buy Position:**
- Entry: ₹{entry_exit.get('entry_buy', 0):.2f}
- Stop Loss: ₹{entry_exit.get('stop_loss_buy', 0):.2f}
- Target: ₹{entry_exit.get('target_buy', 'N/A'):,.2f}
- Risk/Reward: {entry_exit.get('risk_reward_ratio', 0):.2f}

**For Sell Position:**
- Entry: ₹{entry_exit.get('entry_sell', 0):.2f}
- Stop Loss: ₹{entry_exit.get('stop_loss_sell', 0):.2f}
- Target: ₹{entry_exit.get('target_sell', 'N/A'):,.2f}

### Risk Assessment
- Risk Level: {signals.get('risk_level', 'medium').title()}
- Signal Confidence: {signals.get('confidence', 0):.1%}

### Indian Market Considerations
- Trading Hours: 9:15 AM - 3:30 PM IST
- Settlement: T+1 (next day)
- Circuit Limits: ±20% price movement
- Volume Confirmation: Check for delivery percentage

### Recommendation
**Signal: {'BUY' if signals.get('confidence', 0) > 0.6 else 'HOLD' if signals.get('confidence', 0) > 0.4 else 'SELL'}**

**Confidence: {signals.get('confidence', 0):.0%}**

*This analysis is generated using rule-based algorithms and does not rely on LLM predictions.*
*For Indian markets, always consider broader NIFTY/BANKNIFTY trends and global cues.*
"""
    
    return report


def create_rule_based_payload(symbol: str, price_data: pd.DataFrame) -> Dict[str, any]:
    """Return a structured deterministic payload for hybrid decisioning."""
    analyzer = RuleBasedAnalyzer()
    indicators = analyzer.calculate_technical_indicators(price_data)
    signals = analyzer.generate_trading_signals(indicators)
    support_resistance = analyzer.calculate_support_resistance(price_data)
    entry_exit = analyzer.generate_entry_exit_points(indicators, support_resistance)
    trend = analyzer._determine_trend(price_data)
    return {
        "symbol": symbol,
        "trend": trend,
        "confidence": signals.get("confidence", 0.5),
        "risk_level": signals.get("risk_level", "medium"),
        "buy_signals": signals.get("buy_signals", []),
        "sell_signals": signals.get("sell_signals", []),
        "support": support_resistance.get("support", []),
        "resistance": support_resistance.get("resistance", []),
        "entry_exit": entry_exit,
        "indicators": indicators,
    }
