"""
🎯 Trading Bot Main Script - FIXED VERSION
Fully functional with proper async handling and error management
"""
import asyncio
import logging
import pandas as pd
import time
import warnings
import os
import sys
from datetime import datetime, timezone
from typing import Dict, List, Optional

# Suppress warnings
warnings.filterwarnings('ignore')
os.environ['PYTHONWARNINGS'] = 'ignore'

# Setup comprehensive logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

try:
    from data_fetcher import DataFetcher
    from strategy_engine import EnhancedStrategyEngine
    from config import TradingConfig
except ImportError as e:
    logger.error(f"Critical import error: {e}")
    logger.error("Please ensure all required files are present")
    sys.exit(1)

class TradingBot:
    def __init__(self):
        """Initialize the trading bot with comprehensive error handling"""
        try:
            logger.info("🚀 Initializing CryptoSight Trading Bot...")
            
            # Initialize components
            self.data_fetcher = DataFetcher()
            self.strategy_engine = EnhancedStrategyEngine()
            self.config = TradingConfig()
            
            # Performance tracking
            self.performance_stats = {
                'total_signals': 0,
                'successful_scans': 0,
                'failed_scans': 0,
                'total_scan_time': 0.0,
                'last_scan_time': None
            }
            
            logger.info("✅ Trading Bot initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Trading Bot: {e}")
            raise
    
    async def enhanced_market_scan(self, limit: int = 50) -> Dict:
        """
        Enhanced market scan with comprehensive error handling and progress tracking
        """
        scan_start_time = time.time()
        logger.info(f"🔍 Starting enhanced market scan for {limit} symbols...")
        
        try:
            # Step 1: Get top symbols
            logger.info("📊 Step 1: Fetching top cryptocurrency symbols...")
            symbols = await self._get_top_symbols(limit)
            
            if not symbols:
                return self._create_scan_result([], ["Failed to fetch symbols"], scan_start_time)
            
            logger.info(f"✅ Found {len(symbols)} symbols to analyze")
            
            # Step 2: Download market data
            logger.info(f"📈 Step 2: Downloading market data for {len(symbols)} symbols...")
            market_data = await self._download_market_data(symbols)
            
            successful_downloads = len([d for d in market_data.values() if d is not None])
            logger.info(f"✅ Successfully downloaded data for {successful_downloads} symbols")
            
            # Step 3: Analyze with strategy engine
            logger.info(f"🧠 Step 3: Running strategy analysis...")
            signals, errors = await self._analyze_market_data(market_data)
            
            # Step 4: Create final result
            scan_duration = time.time() - scan_start_time
            result = self._create_scan_result(signals, errors, scan_start_time, {
                'symbols_found': len(symbols),
                'data_downloaded': successful_downloads,
                'signals_generated': len(signals),
                'high_quality_signals': len([s for s in signals if s.get('confidence', 0) >= 75]),
                'scan_duration': scan_duration
            })
            
            # Update performance stats
            self._update_performance_stats(result)
            
            logger.info(f"🎯 Scan completed in {scan_duration:.1f}s - Found {len(signals)} signals")
            return result
            
        except Exception as e:
            logger.error(f"❌ Market scan failed: {e}")
            return self._create_scan_result([], [f"Scan failed: {e}"], scan_start_time)
    
    async def _get_top_symbols(self, limit: int) -> List[str]:
        """Get top cryptocurrency symbols with error handling"""
        try:
            symbols = await self.data_fetcher.get_top_symbols(limit)
            
            # Filter out excluded tokens
            excluded = self.config.EXCLUDED_TOKENS
            filtered_symbols = [s for s in symbols if not any(exc in s for exc in excluded)]
            
            logger.info(f"Filtered {len(symbols) - len(filtered_symbols)} excluded tokens")
            return filtered_symbols[:limit]
            
        except Exception as e:
            logger.error(f"Error fetching symbols: {e}")
            return []
    
    async def _download_market_data(self, symbols: List[str]) -> Dict[str, Optional[pd.DataFrame]]:
        """Download market data with progress tracking"""
        try:
            market_data = await self.data_fetcher.bulk_download_data(
                symbols, 
                interval=self.config.PRIMARY_TIMEFRAME,
                limit=200
            )
            
            # Quality check downloaded data
            quality_data = {}
            for symbol, data in market_data.items():
                if data is not None and len(data) >= 50:  # Minimum data requirement
                    quality_data[symbol] = data
                else:
                    logger.warning(f"Insufficient data for {symbol}: {len(data) if data is not None else 0} bars")
            
            return quality_data
            
        except Exception as e:
            logger.error(f"Error downloading market data: {e}")
            return {}
    
    async def _analyze_market_data(self, market_data: Dict) -> tuple[List[Dict], List[str]]:
        """Analyze market data with strategy engine"""
        signals = []
        errors = []
        
        for symbol, data in market_data.items():
            if data is None:
                continue
                
            try:
                logger.debug(f"Analyzing {symbol}...")
                
                # Run strategy analysis
                result = self.strategy_engine.analyze_all_strategies(data, symbol)
                
                # Check if it's a valid signal
                if result.get('signal') in ['BUY', 'SELL']:
                    confidence = result.get('confidence', 0)
                    
                    # Apply minimum confidence filter
                    if confidence >= self.config.MIN_STRATEGY_CONFIDENCE:
                        signals.append(result)
                        logger.info(f"✅ {symbol}: {result['signal']} signal ({confidence:.1f}% confidence)")
                    else:
                        logger.debug(f"❌ {symbol}: Low confidence signal ({confidence:.1f}%)")
                else:
                    logger.debug(f"⏸️ {symbol}: No actionable signal")
                    
            except Exception as e:
                error_msg = f"Analysis failed for {symbol}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        # Sort signals by confidence
        signals.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        return signals, errors
    
    def _create_scan_result(self, signals: List[Dict], errors: List[str], 
                           start_time: float, stats: Optional[Dict] = None) -> Dict:
        """Create standardized scan result"""
        duration = time.time() - start_time
        
        return {
            'signals': signals,
            'errors': errors,
            'scan_time': datetime.now(timezone.utc),
            'duration': duration,
            'stats': stats or {
                'symbols_found': 0,
                'data_downloaded': 0,
                'signals_generated': len(signals),
                'high_quality_signals': len([s for s in signals if s.get('confidence', 0) >= 75]),
                'scan_duration': duration
            }
        }
    
    def _update_performance_stats(self, scan_result: Dict):
        """Update bot performance statistics"""
        self.performance_stats['total_signals'] += len(scan_result['signals'])
        self.performance_stats['total_scan_time'] += scan_result['duration']
        self.performance_stats['last_scan_time'] = scan_result['scan_time']
        
        if scan_result['signals'] or not scan_result['errors']:
            self.performance_stats['successful_scans'] += 1
        else:
            self.performance_stats['failed_scans'] += 1
    
    def get_performance_summary(self) -> Dict:
        """Get performance summary"""
        total_scans = self.performance_stats['successful_scans'] + self.performance_stats['failed_scans']
        
        return {
            'total_scans': total_scans,
            'successful_scans': self.performance_stats['successful_scans'],
            'success_rate': (self.performance_stats['successful_scans'] / total_scans * 100) if total_scans > 0 else 0,
            'total_signals': self.performance_stats['total_signals'],
            'avg_scan_time': self.performance_stats['total_scan_time'] / total_scans if total_scans > 0 else 0,
            'last_scan': self.performance_stats['last_scan_time']
        }
    
    def print_performance_summary(self):
        """Print detailed performance summary"""
        summary = self.get_performance_summary()
        
        logger.info("📊 PERFORMANCE SUMMARY:")
        logger.info(f"  Total Scans: {summary['total_scans']}")
        logger.info(f"  Success Rate: {summary['success_rate']:.1f}%")
        logger.info(f"  Total Signals: {summary['total_signals']}")
        logger.info(f"  Avg Scan Time: {summary['avg_scan_time']:.1f}s")
        
        if summary['last_scan']:
            logger.info(f"  Last Scan: {summary['last_scan'].strftime('%Y-%m-%d %H:%M:%S')}")

async def main():
    """Main function for standalone execution"""
    try:
        logger.info("🚀 Starting CryptoSight Trading Bot...")
        
        bot = TradingBot()
        
        # Run market scan
        results = await bot.enhanced_market_scan(50)
        
        # Display results
        logger.info("\n" + "="*60)
        logger.info("📊 SCAN RESULTS SUMMARY")
        logger.info("="*60)
        
        stats = results.get('stats', {})
        logger.info(f"Symbols Found: {stats.get('symbols_found', 0)}")
        logger.info(f"Data Downloaded: {stats.get('data_downloaded', 0)}")
        logger.info(f"Signals Generated: {stats.get('signals_generated', 0)}")
        logger.info(f"High Quality Signals: {stats.get('high_quality_signals', 0)}")
        logger.info(f"Scan Duration: {stats.get('scan_duration', 0):.1f}s")
        
        # Display signals
        signals = results.get('signals', [])
        if signals:
            logger.info(f"\n🎯 FOUND {len(signals)} TRADING SIGNALS:")
            for i, signal in enumerate(signals[:5], 1):  # Show top 5
                logger.info(f"\n📈 SIGNAL #{i}:")
                logger.info(f"  Symbol: {signal.get('symbol', 'Unknown')}")
                logger.info(f"  Action: {signal.get('signal', 'Unknown')}")
                logger.info(f"  Confidence: {signal.get('confidence', 0):.1f}%")
                logger.info(f"  Entry: ${signal.get('entry_price', 0):.4f}")
                logger.info(f"  Stop Loss: ${signal.get('stop_loss', 0):.4f}")
                logger.info(f"  Take Profit: ${signal.get('take_profit', 0):.4f}")
                logger.info(f"  R/R Ratio: {signal.get('risk_reward_ratio', 0):.2f}")
        else:
            logger.info("🤷 No trading signals found")
        
        # Display errors if any
        errors = results.get('errors', [])
        if errors:
            logger.warning(f"\n⚠️ ENCOUNTERED {len(errors)} ERRORS:")
            for error in errors[:3]:  # Show first 3 errors
                logger.warning(f"  - {error}")
        
        # Performance summary
        bot.print_performance_summary()
        
    except KeyboardInterrupt:
        logger.info("🛑 Trading bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())