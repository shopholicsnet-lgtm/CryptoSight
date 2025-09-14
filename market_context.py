"""
🌍 Market Context Module - Advanced market regime detection and analysis
Provides market intelligence for adaptive strategy selection
"""
import pandas as pd
import numpy as np
import talib
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class MarketContext:
    """Comprehensive market context analysis"""
    trend_direction: str  # 'bullish', 'bearish', 'sideways'
    trend_strength: float  # 0-100
    volatility_regime: str  # 'low', 'medium', 'high', 'extreme'
    market_phase: str  # 'accumulation', 'markup', 'distribution', 'markdown'
    momentum_quality: float  # 0-100
    volume_profile: str  # 'increasing', 'decreasing', 'stable'
    risk_environment: str  # 'low', 'medium', 'high'
    confidence: float  # 0-100

class MarketContextAnalyzer:
    def __init__(self):
        """Initialize market context analyzer"""
        self.lookback_periods = {
            'short': 20,
            'medium': 50, 
            'long': 100
        }
        
        # Volatility thresholds (daily equivalent)
        self.volatility_thresholds = {
            'low': 0.02,     # 2% daily
            'medium': 0.05,  # 5% daily
            'high': 0.10,    # 10% daily
            'extreme': 0.20  # 20% daily
        }
        
        logger.info("🌍 Market Context Analyzer initialized")
    
    def analyze_market_context(self, df: pd.DataFrame, symbol: Optional[str] = None) -> MarketContext:
        """Comprehensive market context analysis"""
        try:
            if len(df) < self.lookback_periods['long']:
                logger.warning(f"Insufficient data for full context analysis: {len(df)} bars")
                return self._default_context()
            
            # Prepare enhanced data
            df_enhanced = self._prepare_technical_data(df)
            
            # 1. Trend Analysis
            trend_info = self._analyze_trend(df_enhanced)
            
            # 2. Volatility Regime
            volatility_info = self._analyze_volatility(df_enhanced)
            
            # 3. Market Phase Detection
            market_phase = self._detect_market_phase(df_enhanced)
            
            # 4. Momentum Quality
            momentum_quality = self._assess_momentum_quality(df_enhanced)
            
            # 5. Volume Profile
            volume_profile = self._analyze_volume_profile(df_enhanced)
            
            # 6. Risk Environment
            risk_environment = self._assess_risk_environment(df_enhanced, volatility_info)
            
            # 7. Overall Confidence
            confidence = self._calculate_context_confidence(
                trend_info, volatility_info, momentum_quality
            )
            
            context = MarketContext(
                trend_direction=trend_info['direction'],
                trend_strength=trend_info['strength'],
                volatility_regime=volatility_info['regime'],
                market_phase=market_phase,
                momentum_quality=momentum_quality,
                volume_profile=volume_profile,
                risk_environment=risk_environment,
                confidence=confidence
            )
            
            if symbol:
                logger.info(f"{symbol} - Market Context: {context.trend_direction} trend "
                          f"({context.trend_strength:.0f}%), {context.volatility_regime} vol, "
                          f"{context.market_phase} phase")
            
            return context
            
        except Exception as e:
            logger.error(f"Market context analysis error: {e}")
            return self._default_context()
    
    def _prepare_technical_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add comprehensive technical indicators for context analysis"""
        df_enhanced = df.copy()
        
        close = df['close'].to_numpy(dtype=np.float64)
        high = df['high'].to_numpy(dtype=np.float64)
        low = df['low'].to_numpy(dtype=np.float64)
        volume = df['volume'].to_numpy(dtype=np.float64)
        
        # Trend indicators
        df_enhanced['ema_20'] = talib.EMA(close, timeperiod=20)
        df_enhanced['ema_50'] = talib.EMA(close, timeperiod=50)
        df_enhanced['ema_100'] = talib.EMA(close, timeperiod=100)
        df_enhanced['ema_200'] = talib.EMA(close, timeperiod=200)
        
        # Momentum
        df_enhanced['rsi'] = talib.RSI(close, timeperiod=14)
        df_enhanced['adx'] = talib.ADX(high, low, close, timeperiod=14)
        
        # MACD
        macd, macd_signal, macd_hist = talib.MACD(close)
        df_enhanced['macd_hist'] = macd_hist
        
        # Volatility
        df_enhanced['atr'] = talib.ATR(high, low, close, timeperiod=14)
        df_enhanced['bb_upper'], df_enhanced['bb_middle'], df_enhanced['bb_lower'] = talib.BBANDS(close)
        
        # Volume
        df_enhanced['volume_sma'] = talib.SMA(volume, timeperiod=20)
        df_enhanced['obv'] = talib.OBV(close, volume)
        df_enhanced['ad_line'] = talib.AD(high, low, close, volume)
        
        # Price volatility
        df_enhanced['returns'] = df_enhanced['close'].pct_change()
        df_enhanced['volatility'] = df_enhanced['returns'].rolling(20).std() * np.sqrt(6)  # Daily equiv
        
        return df_enhanced
    
    def _analyze_trend(self, df: pd.DataFrame) -> Dict:
        """Analyze trend direction and strength"""
        latest = df.iloc[-1]
        
        # EMA alignment scoring
        ema_score = 0
        
        # Primary trend (EMA 20 vs 50)
        if latest['ema_20'] > latest['ema_50']:
            ema_score += 25
        else:
            ema_score -= 25
        
        # Medium trend (EMA 50 vs 100)
        if latest['ema_50'] > latest['ema_100']:
            ema_score += 35
        else:
            ema_score -= 35
        
        # Long trend (EMA 100 vs 200)
        if latest['ema_100'] > latest['ema_200']:
            ema_score += 40
        else:
            ema_score -= 40
        
        # ADX trend strength
        adx_strength = latest['adx']
        
        # Combine scores
        trend_strength = min(100, max(0, 50 + ema_score + (adx_strength - 25)))
        
        # Determine direction
        if trend_strength >= 60:
            if ema_score > 0:
                direction = 'bullish'
            else:
                direction = 'bearish'
        else:
            direction = 'sideways'
        
        return {
            'direction': direction,
            'strength': trend_strength,
            'adx': adx_strength,
            'ema_score': ema_score
        }
    
    def _analyze_volatility(self, df: pd.DataFrame) -> Dict:
        """Analyze volatility regime"""
        latest_volatility = df['volatility'].iloc[-1]
        
        # Classify regime
        if latest_volatility <= self.volatility_thresholds['low']:
            regime = 'low'
        elif latest_volatility <= self.volatility_thresholds['medium']:
            regime = 'medium'
        elif latest_volatility <= self.volatility_thresholds['high']:
            regime = 'high'
        else:
            regime = 'extreme'
        
        return {
            'regime': regime,
            'current_volatility': latest_volatility
        }
    
    def _detect_market_phase(self, df: pd.DataFrame) -> str:
        """Detect current market phase"""
        try:
            # Simple phase detection based on price and volume trends
            price_trend = self._get_price_trend(df, 20)
            volume_trend = self._get_volume_trend(df, 20)
            
            if price_trend > 0.05 and volume_trend > 0.1:
                return 'markup'
            elif price_trend < -0.05 and volume_trend > 0.1:
                return 'markdown'
            elif abs(price_trend) < 0.02:
                return 'accumulation'
            else:
                return 'transition'
                
        except Exception as e:
            logger.error(f"Market phase detection error: {e}")
            return 'unknown'
    
    def _assess_momentum_quality(self, df: pd.DataFrame) -> float:
        """Assess overall momentum quality (0-100)"""
        latest = df.iloc[-1]
        
        momentum_score = 0
        
        # RSI momentum
        rsi = latest['rsi']
        if 40 <= rsi <= 70:  # Healthy range
            momentum_score += 25
        elif 30 <= rsi <= 80:  # Acceptable range
            momentum_score += 15
        
        # MACD momentum
        if latest['macd_hist'] > 0:
            momentum_score += 20
        
        # ADX trend strength
        adx = latest['adx']
        if adx > 30:
            momentum_score += 25
        elif adx > 20:
            momentum_score += 15
        
        # Price momentum consistency
        returns_5 = df['returns'].tail(5).mean()
        returns_20 = df['returns'].tail(20).mean()
        
        if returns_5 * returns_20 > 0 and abs(returns_5) > 0.001:  # Consistent direction
            momentum_score += 30
        
        return min(100, momentum_score)
    
    def _analyze_volume_profile(self, df: pd.DataFrame) -> str:
        """Analyze volume profile and trend"""
        volume_ma_5 = df['volume'].tail(5).mean()
        volume_ma_20 = df['volume'].tail(20).mean()
        
        if volume_ma_5 > volume_ma_20 * 1.2:
            return 'increasing'
        elif volume_ma_5 < volume_ma_20 * 0.8:
            return 'decreasing'
        else:
            return 'stable'
    
    def _assess_risk_environment(self, df: pd.DataFrame, volatility_info: Dict) -> str:
        """Assess overall risk environment"""
        risk_factors = 0
        
        # Volatility risk
        if volatility_info['regime'] in ['high', 'extreme']:
            risk_factors += 2
        elif volatility_info['regime'] == 'medium':
            risk_factors += 1
        
        # Trend uncertainty
        latest = df.iloc[-1]
        if latest['adx'] < 20:  # Weak trend
            risk_factors += 1
        
        # Risk classification
        if risk_factors <= 1:
            return 'low'
        elif risk_factors <= 2:
            return 'medium'
        else:
            return 'high'
    
    def _calculate_context_confidence(self, trend_info: Dict, volatility_info: Dict, 
                                    momentum_quality: float) -> float:
        """Calculate overall context analysis confidence"""
        confidence = 0
        
        # Trend clarity
        if trend_info['strength'] > 70:
            confidence += 40
        elif trend_info['strength'] > 50:
            confidence += 25
        
        # ADX confirmation
        if trend_info['adx'] > 25:
            confidence += 20
        elif trend_info['adx'] > 20:
            confidence += 10
        
        # Momentum quality
        confidence += momentum_quality * 0.3
        
        # Volatility stability
        if volatility_info['regime'] in ['low', 'medium']:
            confidence += 10
        
        return min(100, confidence)
    
    def _get_price_trend(self, df: pd.DataFrame, periods: int) -> float:
        """Calculate price trend over specified periods"""
        if len(df) < periods:
            return 0
        
        start_price = df['close'].iloc[-periods]
        end_price = df['close'].iloc[-1]
        
        return (end_price - start_price) / start_price
    
    def _get_volume_trend(self, df: pd.DataFrame, periods: int) -> float:
        """Calculate volume trend over specified periods"""
        if len(df) < periods:
            return 0
        
        recent_volume = df['volume'].tail(periods // 2).mean()
        older_volume = df['volume'].iloc[-(periods):-(periods//2)].mean()
        
        if older_volume == 0:
            return 0
        
        return (recent_volume - older_volume) / older_volume
    
    def _default_context(self) -> MarketContext:
        """Return default context when analysis fails"""
        return MarketContext(
            trend_direction='sideways',
            trend_strength=50.0,
            volatility_regime='medium',
            market_phase='unknown',
            momentum_quality=50.0,
            volume_profile='stable',
            risk_environment='medium',
            confidence=30.0
        )