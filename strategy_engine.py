"""
🧠 Strategy Engine - FIXED VERSION
Clean, efficient strategy analysis without redundancy
"""
import pandas as pd
import numpy as np
import talib
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class MarketRegime:
    """Market regime classification"""
    trend: str          # 'bullish', 'bearish', 'sideways'
    volatility: str     # 'low', 'medium', 'high'
    strength: float     # 0-100
    confidence: float   # 0-100

@dataclass
class SignalQuality:
    """Signal quality assessment"""
    technical_score: float      # 0-100
    volume_score: float        # 0-100
    momentum_score: float      # 0-100
    overall_score: float       # 0-100

class EnhancedStrategyEngine:
    def __init__(self):
        """Initialize strategy engine with optimized settings"""
        self.min_strategies_required = 2
        self.min_overall_confidence = 65.0
        self.min_risk_reward_ratio = 1.5
        
        # Strategy registry
        self.strategies = {
            'breakout_momentum': self._breakout_momentum_strategy,
            'trend_following': self._trend_following_strategy,
            'volume_surge': self._volume_surge_strategy,
            'momentum_reversal': self._momentum_reversal_strategy,
            'support_resistance': self._support_resistance_strategy
        }
        
        logger.info("🧠 Enhanced Strategy Engine initialized")
    
    def analyze_all_strategies(self, df: pd.DataFrame, symbol: str) -> Dict:
        """Main analysis method - runs all strategies and generates consensus"""
        try:
            # Basic validation
            if len(df) < 50:
                return {'signal': 'HOLD', 'reason': 'Insufficient data', 'confidence': 0}
            
            # Enhance dataframe with technical indicators
            df_enhanced = self._add_technical_indicators(df)
            
            # Detect market regime
            market_regime = self._detect_market_regime(df_enhanced)
            
            # Run all strategies
            strategy_results = {}
            qualified_signals = {'BUY': [], 'SELL': []}
            
            for strategy_name, strategy_func in self.strategies.items():
                try:
                    result = strategy_func(df_enhanced, market_regime)
                    strategy_results[strategy_name] = result
                    
                    # Collect qualified signals
                    if result['signal'] in ['BUY', 'SELL'] and result['confidence'] >= 50:
                        qualified_signals[result['signal']].append({
                            'strategy': strategy_name,
                            'confidence': result['confidence'],
                            'data': result
                        })
                        
                except Exception as e:
                    logger.error(f"Strategy {strategy_name} failed: {e}")
                    strategy_results[strategy_name] = {'signal': 'HOLD', 'confidence': 0, 'error': str(e)}
            
            # Generate consensus
            consensus = self._generate_consensus(qualified_signals, market_regime)
            
            if consensus['signal'] == 'HOLD':
                return consensus
            
            # Calculate signal quality
            signal_quality = self._calculate_signal_quality(
                qualified_signals[consensus['signal']], df_enhanced
            )
            
            # Calculate price levels
            levels = self._calculate_price_levels(df_enhanced, consensus['signal'])
            
            # Final validation
            if levels['risk_reward_ratio'] < self.min_risk_reward_ratio:
                return {
                    'signal': 'HOLD',
                    'reason': f'Poor R/R ratio: {levels["risk_reward_ratio"]:.2f}',
                    'confidence': 0
                }
            
            # Return comprehensive result
            return {
                'symbol': symbol,
                'signal': consensus['signal'],
                'confidence': consensus['confidence'],
                'entry_price': float(df_enhanced.iloc[-1]['close']),
                'stop_loss': levels['stop_loss'],
                'take_profit': levels['take_profit'],
                'risk_reward_ratio': levels['risk_reward_ratio'],
                'reason': consensus['reason'],
                'supporting_strategies': len(qualified_signals[consensus['signal']]),
                'strategies': strategy_results,
                'market_regime': {
                    'trend': market_regime.trend,
                    'volatility': market_regime.volatility,
                    'strength': market_regime.strength
                },
                'signal_quality': {
                    'technical_score': signal_quality.technical_score,
                    'volume_score': signal_quality.volume_score,
                    'momentum_score': signal_quality.momentum_score,
                    'overall_score': signal_quality.overall_score
                }
            }
            
        except Exception as e:
            logger.error(f"Analysis failed for {symbol}: {e}")
            return {'signal': 'HOLD', 'reason': f'Analysis error: {e}', 'confidence': 0}
    
    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add essential technical indicators"""
        try:
            df_enhanced = df.copy()
            
            # Convert to numpy arrays for TA-Lib
            close = df['close'].values.astype(np.float64)
            high = df['high'].values.astype(np.float64)
            low = df['low'].values.astype(np.float64)
            volume = df['volume'].values.astype(np.float64)
            
            # Moving averages
            df_enhanced['ema_9'] = talib.EMA(close, timeperiod=9)
            df_enhanced['ema_21'] = talib.EMA(close, timeperiod=21)
            df_enhanced['ema_50'] = talib.EMA(close, timeperiod=50)
            df_enhanced['sma_20'] = talib.SMA(close, timeperiod=20)
            
            # Oscillators
            df_enhanced['rsi'] = talib.RSI(close, timeperiod=14)
            df_enhanced['stoch_k'], df_enhanced['stoch_d'] = talib.STOCH(high, low, close)
            
            # MACD
            macd, macd_signal, macd_hist = talib.MACD(close)
            df_enhanced['macd'] = macd
            df_enhanced['macd_signal'] = macd_signal
            df_enhanced['macd_hist'] = macd_hist
            
            # Bollinger Bands
            df_enhanced['bb_upper'], df_enhanced['bb_middle'], df_enhanced['bb_lower'] = talib.BBANDS(close)
            
            # Volume indicators
            df_enhanced['volume_sma'] = talib.SMA(volume, timeperiod=20)
            df_enhanced['volume_ratio'] = df_enhanced['volume'] / df_enhanced['volume_sma']
            
            # Volatility
            df_enhanced['atr'] = talib.ATR(high, low, close, timeperiod=14)
            
            # Trend strength
            df_enhanced['adx'] = talib.ADX(high, low, close, timeperiod=14)
            
            return df_enhanced
            
        except Exception as e:
            logger.error(f"Error adding technical indicators: {e}")
            return df
    
    def _detect_market_regime(self, df: pd.DataFrame) -> MarketRegime:
        """Detect current market regime"""
        try:
            latest = df.iloc[-1]
            
            # Trend detection
            ema_9 = latest['ema_9']
            ema_21 = latest['ema_21']
            ema_50 = latest['ema_50']
            price = latest['close']
            adx = latest['adx']
            
            # Determine trend
            if price > ema_9 > ema_21 > ema_50:
                trend = 'bullish'
                strength = min(100, adx * 2)
            elif price < ema_9 < ema_21 < ema_50:
                trend = 'bearish'
                strength = min(100, adx * 2)
            else:
                trend = 'sideways'
                strength = 50
            
            # Volatility assessment
            atr = latest['atr']
            atr_pct = (atr / price) * 100
            
            if atr_pct < 2:
                volatility = 'low'
            elif atr_pct < 5:
                volatility = 'medium'
            else:
                volatility = 'high'
            
            # Confidence based on trend clarity
            if adx > 25:
                confidence = 80
            elif adx > 20:
                confidence = 65
            else:
                confidence = 50
            
            return MarketRegime(trend, volatility, strength, confidence)
            
        except Exception as e:
            logger.error(f"Error detecting market regime: {e}")
            return MarketRegime('sideways', 'medium', 50, 50)
    
    def _generate_consensus(self, qualified_signals: Dict, market_regime: MarketRegime) -> Dict:
        """Generate consensus from qualified signals"""
        buy_count = len(qualified_signals['BUY'])
        sell_count = len(qualified_signals['SELL'])
        
        # Require at least 2 strategies for strong consensus
        if buy_count >= 2 and buy_count > sell_count:
            confidences = [s['confidence'] for s in qualified_signals['BUY']]
            avg_confidence = np.mean(confidences)
            
            if avg_confidence >= self.min_overall_confidence:
                strategies = [s['strategy'] for s in qualified_signals['BUY']]
                return {
                    'signal': 'BUY',
                    'confidence': avg_confidence,
                    'reason': f"{buy_count} bullish strategies: {', '.join(strategies)}"
                }
        
        elif sell_count >= 2 and sell_count > buy_count:
            confidences = [s['confidence'] for s in qualified_signals['SELL']]
            avg_confidence = np.mean(confidences)
            
            if avg_confidence >= self.min_overall_confidence:
                strategies = [s['strategy'] for s in qualified_signals['SELL']]
                return {
                    'signal': 'SELL',
                    'confidence': avg_confidence,
                    'reason': f"{sell_count} bearish strategies: {', '.join(strategies)}"
                }
        
        # Single high-confidence strategy
        elif buy_count == 1 and qualified_signals['BUY'][0]['confidence'] >= 80:
            signal = qualified_signals['BUY'][0]
            return {
                'signal': 'BUY',
                'confidence': signal['confidence'],
                'reason': f"High confidence: {signal['strategy']}"
            }
        
        elif sell_count == 1 and qualified_signals['SELL'][0]['confidence'] >= 80:
            signal = qualified_signals['SELL'][0]
            return {
                'signal': 'SELL',
                'confidence': signal['confidence'],
                'reason': f"High confidence: {signal['strategy']}"
            }
        
        return {
            'signal': 'HOLD',
            'confidence': 0,
            'reason': f'No consensus: {buy_count} BUY vs {sell_count} SELL strategies'
        }
    
    def _calculate_signal_quality(self, winning_signals: List, df: pd.DataFrame) -> SignalQuality:
        """Calculate overall signal quality"""
        try:
            latest = df.iloc[-1]
            
            # Technical score (average strategy confidence)
            technical_score = np.mean([s['confidence'] for s in winning_signals])
            
            # Volume score
            volume_ratio = latest['volume_ratio']
            if volume_ratio >= 2.0:
                volume_score = 100
            elif volume_ratio >= 1.5:
                volume_score = 80
            elif volume_ratio >= 1.2:
                volume_score = 60
            else:
                volume_score = 40
            
            # Momentum score
            rsi = latest['rsi']
            adx = latest['adx']
            
            momentum_score = 0
            if 40 <= rsi <= 70:
                momentum_score += 50
            elif 30 <= rsi <= 80:
                momentum_score += 30
            
            if adx > 25:
                momentum_score += 50
            elif adx > 20:
                momentum_score += 30
            
            # Overall score
            overall_score = (technical_score * 0.4 + volume_score * 0.3 + momentum_score * 0.3)
            
            return SignalQuality(float(technical_score), float(volume_score), float(momentum_score), float(overall_score))
            
        except Exception as e:
            logger.error(f"Error calculating signal quality: {e}")
            return SignalQuality(60, 60, 60, 60)
    
    def _calculate_price_levels(self, df: pd.DataFrame, signal_type: str) -> Dict:
        """Calculate stop loss and take profit levels"""
        try:
            latest = df.iloc[-1]
            price = latest['close']
            atr = latest['atr']
            
            if signal_type == 'BUY':
                stop_loss = price - (atr * 2.0)
                take_profit = price + (atr * 3.0)
            else:  # SELL
                stop_loss = price + (atr * 2.0)
                take_profit = price - (atr * 3.0)
            
            risk = abs(price - stop_loss)
            reward = abs(take_profit - price)
            risk_reward_ratio = reward / risk if risk > 0 else 0
            
            return {
                'stop_loss': float(stop_loss),
                'take_profit': float(take_profit),
                'risk_reward_ratio': float(risk_reward_ratio)
            }
            
        except Exception as e:
            logger.error(f"Error calculating price levels: {e}")
            price = float(df.iloc[-1]['close'])
            multiplier = 0.97 if signal_type == 'BUY' else 1.03
            return {
                'stop_loss': price * multiplier,
                'take_profit': price * (1.06 if signal_type == 'BUY' else 0.94),
                'risk_reward_ratio': 2.0
            }
    
    # =========================================================================
    # STRATEGY IMPLEMENTATIONS
    # =========================================================================
    
    def _breakout_momentum_strategy(self, df: pd.DataFrame, market_regime: MarketRegime) -> Dict:
        """Breakout with momentum confirmation"""
        try:
            latest = df.iloc[-1]
            confidence = 0
            reasons = []
            
            # Price breakout above Bollinger Band
            if latest['close'] > latest['bb_upper']:
                confidence += 35
                reasons.append("BB breakout")
            elif latest['close'] > latest['bb_middle']:
                confidence += 20
                reasons.append("Above BB middle")
            
            # Volume confirmation
            if latest['volume_ratio'] > 1.5:
                confidence += 25
                reasons.append(f"Volume surge {latest['volume_ratio']:.1f}x")
            elif latest['volume_ratio'] > 1.2:
                confidence += 15
                reasons.append("Good volume")
            
            # Momentum confirmation
            if latest['rsi'] > 55 and latest['rsi'] < 75:
                confidence += 20
                reasons.append("RSI momentum")
            
            # Trend alignment
            if latest['close'] > latest['ema_21']:
                confidence += 20
                reasons.append("Trend aligned")
            
            signal = 'BUY' if confidence >= 60 else 'HOLD'
            
            return {
                'signal': signal,
                'confidence': confidence,
                'reason': f"Breakout: {', '.join(reasons)}"
            }
            
        except Exception as e:
            return {'signal': 'HOLD', 'confidence': 0, 'reason': f"Error: {e}"}
    
    def _momentum_reversal_strategy(self, df: pd.DataFrame, market_regime: MarketRegime) -> Dict:
        """Momentum reversal strategy based on oversold/overbought conditions"""
        try:
            latest = df.iloc[-1]
            confidence = 0
            reasons = []
            
            # RSI reversal signals
            if latest['rsi'] < 30:
                confidence += 40
                reasons.append("RSI oversold")
                signal_type = 'BUY'
            elif latest['rsi'] > 70:
                confidence += 40
                reasons.append("RSI overbought")
                signal_type = 'SELL'
            else:
                return {'signal': 'HOLD', 'confidence': 0, 'reason': "RSI in neutral zone"}
            
            # Stochastic confirmation
            if signal_type == 'BUY' and latest['stoch_k'] < 20:
                confidence += 25
                reasons.append("Stoch oversold")
            elif signal_type == 'SELL' and latest['stoch_k'] > 80:
                confidence += 25
                reasons.append("Stoch overbought")
            
            # MACD divergence
            if signal_type == 'BUY' and latest['macd_hist'] > 0:
                confidence += 20
                reasons.append("MACD bullish")
            elif signal_type == 'SELL' and latest['macd_hist'] < 0:
                confidence += 20
                reasons.append("MACD bearish")
            
            # Volume confirmation
            if latest['volume_ratio'] > 1.2:
                confidence += 15
                reasons.append("Volume support")
            
            return {
                'signal': signal_type if confidence >= 65 else 'HOLD',
                'confidence': confidence,
                'reason': f"Reversal: {', '.join(reasons)}"
            }
            
        except Exception as e:
            return {'signal': 'HOLD', 'confidence': 0, 'reason': f"Error: {e}"}
    
    def _support_resistance_strategy(self, df: pd.DataFrame, market_regime: MarketRegime) -> Dict:
        """Support and resistance level strategy"""
        try:
            latest = df.iloc[-1]
            confidence = 0
            reasons = []
            
            # Calculate recent highs and lows for support/resistance
            recent_data = df.tail(20)
            resistance = recent_data['high'].max()
            support = recent_data['low'].min()
            current_price = latest['close']
            
            signal_type = None
            
            # Near resistance - potential sell
            resistance_distance = ((resistance - current_price) / current_price) * 100
            if resistance_distance < 2:
                confidence += 35
                reasons.append("Near resistance")
                signal_type = 'SELL'
            
            # Near support - potential buy
            support_distance = ((current_price - support) / current_price) * 100
            if support_distance < 2:
                confidence += 35
                reasons.append("Near support")
                signal_type = 'BUY'
            
            # If neither near support nor resistance
            if not reasons or signal_type is None:
                return {'signal': 'HOLD', 'confidence': 0, 'reason': "Not near key levels"}
            
            # Volume confirmation
            if latest['volume_ratio'] > 1.3:
                confidence += 25
                reasons.append("High volume")
            elif latest['volume_ratio'] > 1.1:
                confidence += 15
                reasons.append("Good volume")
            
            # RSI confirmation
            if signal_type == 'BUY' and latest['rsi'] < 45:
                confidence += 20
                reasons.append("RSI support")
            elif signal_type == 'SELL' and latest['rsi'] > 55:
                confidence += 20
                reasons.append("RSI resistance")
            
            # Bollinger Band confirmation
            if signal_type == 'BUY' and current_price <= latest['bb_lower']:
                confidence += 20
                reasons.append("BB support")
            elif signal_type == 'SELL' and current_price >= latest['bb_upper']:
                confidence += 20
                reasons.append("BB resistance")
            
            return {
                'signal': signal_type if confidence >= 60 else 'HOLD',
                'confidence': confidence,
                'reason': f"S/R: {', '.join(reasons)}"
            }
            
        except Exception as e:
            return {'signal': 'HOLD', 'confidence': 0, 'reason': f"Error: {e}"}
    
    def _trend_following_strategy(self, df: pd.DataFrame, market_regime: MarketRegime) -> Dict:
        """EMA-based trend following"""
        try:
            latest = df.iloc[-1]
            confidence = 0
            reasons = []
            
            # EMA alignment for bullish trend
            if latest['ema_9'] > latest['ema_21'] > latest['ema_50']:
                confidence += 40
                reasons.append("Bullish EMA alignment")
                signal_type = 'BUY'
            elif latest['ema_9'] < latest['ema_21'] < latest['ema_50']:
                confidence += 40
                reasons.append("Bearish EMA alignment")
                signal_type = 'SELL'
            else:
                return {'signal': 'HOLD', 'confidence': 0, 'reason': "No clear trend"}
            
            # Price position relative to EMAs
            if signal_type == 'BUY' and latest['close'] > latest['ema_9']:
                confidence += 25
                reasons.append("Price above EMAs")
            elif signal_type == 'SELL' and latest['close'] < latest['ema_9']:
                confidence += 25
                reasons.append("Price below EMAs")
            
            # ADX trend strength
            if latest['adx'] > 25:
                confidence += 25
                reasons.append("Strong trend")
            elif latest['adx'] > 20:
                confidence += 15
                reasons.append("Medium trend")
            
            # Volume support
            if latest['volume_ratio'] > 1.1:
                confidence += 10
                reasons.append("Volume support")
            
            return {
                'signal': signal_type if confidence >= 60 else 'HOLD',
                'confidence': confidence,
                'reason': f"Trend: {', '.join(reasons)}"
            }
            
        except Exception as e:
            return {'signal': 'HOLD', 'confidence': 0, 'reason': f"Error: {e}"}
    
    def _volume_surge_strategy(self, df: pd.DataFrame, market_regime: MarketRegime) -> Dict:
        """Volume-based momentum strategy"""
        try:
            latest = df.iloc[-1]
            confidence = 0
            reasons = []
            
            # Volume surge detection
            if latest['volume_ratio'] >= 3.0:
                confidence += 50
                reasons.append(f"Volume explosion {latest['volume_ratio']:.1f}x")
            elif latest['volume_ratio'] >= 2.0:
                confidence += 35
                reasons.append(f"High volume {latest['volume_ratio']:.1f}x")
            elif latest['volume_ratio'] >= 1.5:
                confidence += 20
                reasons.append("Above average volume")
            else:
                return {'signal': 'HOLD', 'confidence': 0, 'reason': "Insufficient volume"}
            
            # Price movement direction
            price_change = ((latest['close'] - latest['open']) / latest['open']) * 100
            
            if price_change > 1.0:
                confidence += 30
                reasons.append(f"Strong price gain {price_change:.1f}%")
                signal_type = 'BUY'
            elif price_change < -1.0:
                confidence += 30
                reasons.append(f"Strong price drop {price_change:.1f}%")
                signal_type = 'SELL'
            else:
                confidence += 10
                signal_type = 'BUY' if price_change > 0 else 'SELL'
            
            # Momentum confirmation
            if signal_type == 'BUY' and latest['rsi'] > 50:
                confidence += 20
                reasons.append("Bullish momentum")
            elif signal_type == 'SELL' and latest['rsi'] < 50:
                confidence += 20
                reasons.append("Bearish momentum")
            
            return {
                'signal': signal_type if confidence >= 70 else 'HOLD',
                'confidence': confidence,
                'reason': f"Volume: {', '.join(reasons)}"
            }
            
        except Exception as e:
            return {'signal': 'HOLD', 'confidence': 0, 'reason': f"Error: {e}"}
        