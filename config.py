"""
🎯 CryptoBot Pro - Enhanced Configuration with Environment Variables
Optimized for maximum profit with controlled risk
"""

import os
from typing import Dict, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class TradingConfig:
    """Professional trading configuration for consistent profits"""
    
    # =============================================================================
    # 💰 PROFIT & RISK SETTINGS (CORE SYSTEM)
    # =============================================================================
    ACCOUNT_BALANCE: float = float(os.getenv('ACCOUNT_BALANCE', '10000.0'))
    MAX_RISK_PER_TRADE: float = float(os.getenv('MAX_RISK_PER_TRADE', '2.0'))
    MAX_DAILY_LOSS: float = float(os.getenv('MAX_DAILY_LOSS', '6.0'))
    MAX_CONCURRENT_TRADES: int = int(os.getenv('MAX_CONCURRENT_TRADES', '3'))
    
    # Profit Targets (Aggressive but achievable)
    MIN_PROFIT_TARGET: float = 4.0            
    PREFERRED_PROFIT_TARGET: float = 6.0      
    MAX_PROFIT_TARGET: float = 10.0           
    
    # Stop Loss Settings
    DEFAULT_STOP_LOSS: float = 2.5            
    TIGHT_STOP_LOSS: float = 1.5              
    LOOSE_STOP_LOSS: float = 4.0              
    
    # =============================================================================
    # 🎯 STRATEGY SETTINGS (7 BULLETPROOF STRATEGIES)
    # =============================================================================
    
    # Strategy Confidence Thresholds
    MIN_STRATEGY_CONFIDENCE: float = 65.0     
    HIGH_CONFIDENCE_THRESHOLD: float = 80.0   
    STRATEGY_CONSENSUS_REQUIRED: int = 2      
    
    # Volume Requirements
    MIN_VOLUME_USD: float = 20_000_000        
    VOLUME_SURGE_MULTIPLIER: float = 1.5      
    HIGH_VOLUME_THRESHOLD: float = 2.0        
    
    # Volatility Filters
    MIN_VOLATILITY: float = 3.0               
    MAX_VOLATILITY: float = 25.0              
    VOLATILITY_SWEET_SPOT: float = 6.0        
    
    # Technical Indicator Settings
    RSI_OVERSOLD: float = 30.0                
    RSI_OVERBOUGHT: float = 70.0              
    RSI_NEUTRAL_LOW: float = 40.0             
    RSI_NEUTRAL_HIGH: float = 60.0            
    
    # Moving Average Settings
    EMA_FAST: int = 9                         
    EMA_SLOW: int = 21                        
    SMA_TREND: int = 50                       
    SMA_LONG_TERM: int = 200                  
    
    # =============================================================================
    # 📊 MARKET SCANNING SETTINGS
    # =============================================================================
    SCAN_INTERVAL_MINUTES: int = 15           
    MAX_COINS_TO_SCAN: int = 100              
    MIN_CANDLES: int = 50                     # Minimum candles required for analysis
    PREFERRED_QUOTE_CURRENCIES: List[str] = ['USDT']
    
    # Excluded Tokens (Avoid these)
    EXCLUDED_TOKENS: List[str] = [
        'UP', 'DOWN', 'BULL', 'BEAR',         
        '3L', '3S', '5L', '5S',               
        'BUSD', 'USDC', 'TUSD',               
        'USDT'                                
    ]
    
    # =============================================================================
    # 📄 TIMEFRAME SETTINGS
    # =============================================================================
    PRIMARY_TIMEFRAME: str = '4h'             
    CONFIRMATION_TIMEFRAMES: List[str] = ['1h', '1d']  
    SIGNAL_TIMEOUT_HOURS: Dict[str, int] = {
        '1h': 4,                              
        '4h': 12,                             
        '1d': 24                              
    }
    
    # =============================================================================
    # 🔗 EXCHANGE SETTINGS
    # =============================================================================
    EXCHANGE_NAME: str = 'binance'
    EXCHANGE_RATE_LIMIT: int = 1000           
    EXCHANGE_TIMEOUT: int = 15000             
    
    # API Keys (Set via environment variables for security)
    API_KEY: str = os.getenv('BINANCE_API_KEY', '')
    API_SECRET: str = os.getenv('BINANCE_API_SECRET', '')
    
    # =============================================================================
    # 📱 DISCORD NOTIFICATION SETTINGS
    # =============================================================================
    DISCORD_WEBHOOK_URL: str = os.getenv('DISCORD_WEBHOOK_URL', '')
    
    # Notification Preferences
    NOTIFY_NEW_SIGNALS: bool = True           
    NOTIFY_TP_HITS: bool = True               
    NOTIFY_STOP_LOSSES: bool = True           
    NOTIFY_DAILY_SUMMARY: bool = True         
    
    # =============================================================================
    # 🎯 STRATEGY-SPECIFIC SETTINGS
    # =============================================================================
    
    # 1. Breakout Bull Strategy
    BREAKOUT_VOLUME_MULTIPLIER: float = 1.8   
    BREAKOUT_RESISTANCE_BUFFER: float = 0.5   
    
    # 2. Momentum Surge Strategy  
    MOMENTUM_MIN_PERCENTAGE: float = 4.0      
    MOMENTUM_TIMEFRAME_HOURS: int = 6         
    
    # 3. Support Bounce Strategy
    SUPPORT_PROXIMITY: float = 1.0            
    BOUNCE_VOLUME_CONFIRMATION: float = 1.3   
    
    # 4. Volume Explosion Strategy
    VOLUME_EXPLOSION_MULTIPLIER: float = 3.0  
    VOLUME_MOMENTUM_MIN: float = 2.0          
    
    # 5. Breakdown Bear Strategy
    BREAKDOWN_VOLUME_MULTIPLIER: float = 1.8  
    BREAKDOWN_SUPPORT_BUFFER: float = 0.5     
    
    # 6. Momentum Crash Strategy
    CRASH_MOMENTUM_MIN: float = -4.0          
    CRASH_EMA_BREAK_CONFIRMATION: bool = True 
    
    # 7. Resistance Reject Strategy
    RESISTANCE_PROXIMITY: float = 1.0         
    REJECTION_VOLUME_CONFIRMATION: float = 1.3 
    
    # =============================================================================
    # 📈 PERFORMANCE MONITORING
    # =============================================================================
    TARGET_WIN_RATE: float = 65.0            
    TARGET_PROFIT_FACTOR: float = 2.0        
    MAX_DRAWDOWN_TOLERANCE: float = 10.0     
    
    # Performance Review Intervals
    DAILY_REVIEW_HOUR: int = 0                
    WEEKLY_REVIEW_DAY: int = 0                
    
    # =============================================================================
    # 🛡️ SAFETY FEATURES
    # =============================================================================
    ENABLE_PAPER_TRADING: bool = os.getenv('PAPER_TRADING', 'True').lower() == 'true'
    ENABLE_RISK_ALERTS: bool = True           
    ENABLE_PERFORMANCE_TRACKING: bool = True  
    
    # Emergency Settings
    EMERGENCY_STOP_LOSS: float = 15.0         
    MAX_CONSECUTIVE_LOSSES: int = 5           
    
    # Database Settings
    DATABASE_PATH: str = os.getenv('DATABASE_PATH', 'trading_bot.db')
    
    @classmethod
    def get_strategy_settings(cls) -> Dict:
        """Get all strategy-specific settings"""
        return {
            'breakout_bull': {
                'volume_multiplier': cls.BREAKOUT_VOLUME_MULTIPLIER,
                'resistance_buffer': cls.BREAKOUT_RESISTANCE_BUFFER,
                'min_confidence': 75.0
            },
            'momentum_surge': {
                'min_percentage': cls.MOMENTUM_MIN_PERCENTAGE,
                'timeframe_hours': cls.MOMENTUM_TIMEFRAME_HOURS,
                'min_confidence': 80.0
            },
            'support_bounce': {
                'proximity': cls.SUPPORT_PROXIMITY,
                'volume_confirmation': cls.BOUNCE_VOLUME_CONFIRMATION,
                'min_confidence': 70.0
            },
            'volume_explosion': {
                'multiplier': cls.VOLUME_EXPLOSION_MULTIPLIER,
                'momentum_min': cls.VOLUME_MOMENTUM_MIN,
                'min_confidence': 85.0
            },
            'breakdown_bear': {
                'volume_multiplier': cls.BREAKDOWN_VOLUME_MULTIPLIER,
                'support_buffer': cls.BREAKDOWN_SUPPORT_BUFFER,
                'min_confidence': 75.0
            },
            'momentum_crash': {
                'momentum_min': cls.CRASH_MOMENTUM_MIN,
                'ema_break_required': cls.CRASH_EMA_BREAK_CONFIRMATION,
                'min_confidence': 80.0
            },
            'resistance_reject': {
                'proximity': cls.RESISTANCE_PROXIMITY,
                'volume_confirmation': cls.REJECTION_VOLUME_CONFIRMATION,
                'min_confidence': 70.0
            }
        }
    
    from typing import Tuple

    @classmethod
    def validate_config(cls) -> Tuple[List[str], List[str]]:
        """Validate configuration settings"""
        errors = []
        warnings = []
        
        # Critical validations
        if cls.MAX_RISK_PER_TRADE > 5.0:
            errors.append("Risk per trade too high (>5%) - Very dangerous!")
        
        if cls.ACCOUNT_BALANCE <= 0:
            errors.append("Account balance must be positive")
        
        if cls.MIN_PROFIT_TARGET < 2.0:
            warnings.append("Minimum profit target very low (<2%)")
        
        # API Configuration warnings
        if not cls.API_KEY and not cls.ENABLE_PAPER_TRADING:
            warnings.append("No API key configured - only paper trading available")
            
        if not cls.DISCORD_WEBHOOK_URL:
            warnings.append("No Discord webhook - notifications disabled")
        
        # Risk/Reward validation
        if cls.MIN_PROFIT_TARGET < cls.DEFAULT_STOP_LOSS * 2:
            warnings.append(f"Poor risk/reward ratio: {cls.MIN_PROFIT_TARGET}% profit vs {cls.DEFAULT_STOP_LOSS}% stop")
        
        return errors, warnings
    
    @classmethod
    def print_config_summary(cls):
        """Print configuration summary"""
        print("\n" + "="*60)
        print("🎯 CryptoSight v3.0 Configuration Summary")
        print("="*60)
        
        print(f"💰 Account Balance: ${cls.ACCOUNT_BALANCE:,.2f}")
        print(f"📊 Risk Per Trade: {cls.MAX_RISK_PER_TRADE}%")
        print(f"🎯 Profit Target: {cls.MIN_PROFIT_TARGET}-{cls.MAX_PROFIT_TARGET}%")
        print(f"⏱️  Primary Timeframe: {cls.PRIMARY_TIMEFRAME}")
        print(f"🔍 Max Coins to Scan: {cls.MAX_COINS_TO_SCAN}")
        print(f"📝 Paper Trading: {'✅ Enabled' if cls.ENABLE_PAPER_TRADING else '❌ Disabled'}")
        print(f"🔔 Discord Alerts: {'✅ Configured' if cls.DISCORD_WEBHOOK_URL else '❌ Not configured'}")
        print(f"🔑 API Keys: {'✅ Configured' if cls.API_KEY else '❌ Not configured'}")
        
        errors, warnings = cls.validate_config()
        
        if errors:
            print("\n❌ ERRORS (Must Fix):")
            for error in errors:
                print(f"  - {error}")
        
        if warnings:
            print("\n⚠️  WARNINGS:")
            for warning in warnings:
                print(f"  - {warning}")
        
        if not errors and not warnings:
            print("\n✅ Configuration is valid!")
        
        print("="*60 + "\n")

# Create global config instance
config = TradingConfig()

# Print configuration summary if run directly
if __name__ == "__main__":
    config.print_config_summary()