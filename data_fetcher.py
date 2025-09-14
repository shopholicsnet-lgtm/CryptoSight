"""
📊 Data Fetcher - FIXED VERSION
Comprehensive market data fetching with all required methods
"""
import ccxt
import pandas as pd
import numpy as np
import logging
import asyncio
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataFetcher:
    def __init__(self):
        """Initialize with comprehensive error handling"""
        self.exchange = None
        self.rate_limiter = None
        self._initialize_exchange()
        
    def _initialize_exchange(self):
        """Initialize exchange connection with proper error handling"""
        try:
            self.exchange = ccxt.binance({
                'rateLimit': 1200,
                'enableRateLimit': True,
                'timeout': 15000,
                'options': {'adjustForTimeDifference': True}
            })
            
            # Test connection
            self.exchange.load_markets()
            logger.info("✅ Binance exchange connection established")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize exchange: {e}")
            self.exchange = None
    
    async def get_top_symbols(self, limit: int = 50) -> List[str]:
        """Get top cryptocurrency symbols by volume"""
        if not self.exchange:
            logger.error("Exchange not initialized")
            return []
        
        try:
            logger.info(f"Fetching top {limit} symbols by volume...")
            
            # Get all tickers
            tickers = self.exchange.fetch_tickers()
            
            # Filter USDT pairs only
            usdt_pairs = []
            for symbol, ticker in tickers.items():
                if symbol.endswith('/USDT'):
                    quote_volume = ticker.get('quoteVolume', 0)
                    if isinstance(quote_volume, (int, float)) and quote_volume > 1000000:  # Min 1M volume
                        usdt_pairs.append((symbol, float(quote_volume)))
            
            # Sort by volume (descending)
            usdt_pairs.sort(key=lambda x: x[1], reverse=True)
            
            # Convert to the format expected by the rest of the system
            symbols = [pair[0].replace('/', '') for pair in usdt_pairs[:limit]]
            
            logger.info(f"✅ Successfully fetched {len(symbols)} high-volume USDT pairs")
            return symbols
            
        except Exception as e:
            logger.error(f"❌ Error fetching top symbols: {e}")
            return []
    
    async def bulk_download_data(self, symbols: List[str], interval: str = "4h", limit: int = 200) -> Dict[str, Optional[pd.DataFrame]]:
        """Download OHLCV data for multiple symbols"""
        if not self.exchange:
            logger.error("Exchange not initialized")
            return {}
        
        # Map intervals to ccxt format
        timeframe_map = {
            "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
            "1h": "1h", "2h": "2h", "4h": "4h", "6h": "6h",
            "8h": "8h", "12h": "12h", "1d": "1d", "3d": "3d",
            "1w": "1w", "1M": "1M"
        }
        
        ccxt_timeframe = timeframe_map.get(interval, "4h")
        
        logger.info(f"Downloading {ccxt_timeframe} data for {len(symbols)} symbols...")
        
        results = {}
        successful_downloads = 0
        
        for i, symbol in enumerate(symbols, 1):
            try:
                # Add rate limiting
                if i > 1:
                    await asyncio.sleep(0.1)  # Small delay between requests
                
                # Convert symbol format (BTCUSDT -> BTC/USDT)
                ccxt_symbol = f"{symbol[:-4]}/{symbol[-4:]}" if not '/' in symbol else symbol
                
                logger.debug(f"Downloading {ccxt_symbol} ({i}/{len(symbols)})...")
                
                # Fetch OHLCV data
                ohlcv_data = self.exchange.fetch_ohlcv(ccxt_symbol, ccxt_timeframe, limit=limit)
                
                if ohlcv_data and len(ohlcv_data) > 0:
                    # Convert to DataFrame
                    df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df.set_index('timestamp', inplace=True)
                    
                    # Ensure data types
                    for col in ['open', 'high', 'low', 'close', 'volume']:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    
                    # Remove any NaN rows
                    df = df.dropna()
                    
                    if len(df) >= 50:  # Minimum data requirement
                        results[symbol] = df
                        successful_downloads += 1
                        logger.debug(f"✅ {symbol}: {len(df)} bars downloaded")
                    else:
                        results[symbol] = None
                        logger.warning(f"❌ {symbol}: Insufficient data ({len(df)} bars)")
                else:
                    results[symbol] = None
                    logger.warning(f"❌ {symbol}: No data received")
                    
            except Exception as e:
                results[symbol] = None
                logger.warning(f"❌ {symbol}: Download failed - {e}")
        
        logger.info(f"✅ Bulk download complete: {successful_downloads}/{len(symbols)} successful")
        return results
    
    def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current ticker information for a symbol"""
        if not self.exchange:
            logger.error("Exchange not initialized")
            return None
        
        try:
            # Convert symbol format if needed
            ccxt_symbol = f"{symbol[:-4]}/{symbol[-4:]}" if not '/' in symbol else symbol
            
            ticker = self.exchange.fetch_ticker(ccxt_symbol)
            return dict(ticker)
            
        except Exception as e:
            logger.warning(f"Could not fetch ticker for {symbol}: {e}")
            return None
    
    def get_ohlcv(self, symbol: str, timeframe: str = '4h', limit: int = 200) -> Optional[pd.DataFrame]:
        """Get OHLCV data for a single symbol"""
        if not self.exchange:
            logger.error("Exchange not initialized")
            return None
        
        try:
            # Convert symbol format if needed
            ccxt_symbol = f"{symbol[:-4]}/{symbol[-4:]}" if not '/' in symbol else symbol
            
            # Fetch data
            ohlcv_data = self.exchange.fetch_ohlcv(ccxt_symbol, timeframe, limit=limit)
            
            if not ohlcv_data:
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Ensure proper data types
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Remove NaN rows
            df = df.dropna()
            
            return df if len(df) > 0 else None
            
        except Exception as e:
            logger.warning(f"Could not fetch OHLCV for {symbol}: {e}")
            return None
    
    def get_market_summary(self) -> Dict[str, Any]:
        """Get overall market summary"""
        if not self.exchange:
            return {}
        
        try:
            tickers = self.exchange.fetch_tickers()
            
            # Calculate market stats
            usdt_pairs = [t for s, t in tickers.items() if s.endswith('/USDT')]
            
            if not usdt_pairs:
                return {}
            
            total_volume = sum(float(vol) for t in usdt_pairs if (vol := t.get('quoteVolume', 0)) is not None and isinstance(vol, (int, float)))
            price_changes = [t.get('percentage', 0) for t in usdt_pairs if t.get('percentage') is not None]
            # Filter to ensure only numeric values
            numeric_price_changes = [p for p in price_changes if isinstance(p, (int, float))]
            
            return {
                'total_pairs': len(usdt_pairs),
                'total_volume_24h': total_volume,
                'avg_price_change': np.mean(numeric_price_changes) if numeric_price_changes else 0,
                'gainers': len([p for p in numeric_price_changes if p > 0]),
                'losers': len([p for p in numeric_price_changes if p < 0]),
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error getting market summary: {e}")
            return {}
    
    def test_connection(self) -> bool:
        """Test exchange connection"""
        if not self.exchange:
            return False
        
        try:
            # Try to fetch a simple ticker
            self.exchange.fetch_ticker('BTC/USDT')
            logger.info("✅ Exchange connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ Exchange connection test failed: {e}")
            return False
    
    def get_exchange_info(self) -> Dict[str, Any]:
        """Get exchange information and limits"""
        if not self.exchange:
            return {}
        
        try:
            return {
                'name': self.exchange.name,
                'rate_limit': self.exchange.rateLimit,
                'has_fetch_ohlcv': self.exchange.has.get('fetchOHLCV', False),
                'has_fetch_tickers': self.exchange.has.get('fetchTickers', False),
                'timeframes': list(self.exchange.timeframes.keys()) if hasattr(self.exchange, 'timeframes') else [],
                'status': 'connected' if self.exchange else 'disconnected'
            }
            
        except Exception as e:
            logger.error(f"Error getting exchange info: {e}")
            return {'status': 'error', 'error': str(e)}

# Test functionality
async def test_data_fetcher():
    """Test the data fetcher functionality"""
    logger.info("🧪 Testing DataFetcher...")
    
    fetcher = DataFetcher()
    
    # Test connection
    if not fetcher.test_connection():
        logger.error("❌ Connection test failed")
        return
    
    # Test getting top symbols
    symbols = await fetcher.get_top_symbols(5)
    logger.info(f"✅ Top symbols test: {symbols}")
    
    if symbols:
        # Test bulk download
        data = await fetcher.bulk_download_data(symbols[:2], "1h", 100)
        logger.info(f"✅ Bulk download test: {len(data)} datasets")
        
        # Test single ticker
        ticker = fetcher.get_ticker(symbols[0])
        if ticker:
            logger.info(f"✅ Ticker test: {symbols[0]} = ${ticker.get('last', 0):.2f}")
    
    logger.info("🧪 DataFetcher tests completed")

if __name__ == "__main__":
    asyncio.run(test_data_fetcher())