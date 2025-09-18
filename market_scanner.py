"""
🔍 CryptoBot Pro - Advanced Market Scanner
Fetches top coins and validates them against the exchange's official market list.
"""
import streamlit as st
import ccxt
import requests
import logging
import pandas as pd
from config import config
from strategy_engine import Enhanced7StrategyEngine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MarketScanner:
    def __init__(self):
        self.exchange = self._init_exchange()
        self.coingecko_base = "https://api.coingecko.com/api/v3"
        self.binance_symbols = set()
        
        # Initialize the strategy engine
        self.strategy_engine = Enhanced7StrategyEngine()
        
        if self.exchange:
            try:
                markets = self.exchange.load_markets()
                self.binance_symbols = {m['symbol'].replace('/', '') for m in markets.values() if m['symbol'].endswith('/USDT')}
                logger.info(f"✅ Exchange connection established. Loaded {len(self.binance_symbols)} USDT pairs.")
            except Exception as e:
                logger.error(f"❌ Failed to load markets from exchange: {e}")
        else:
            logger.error("❌ Exchange connection failed during initialization.")
        
        logger.info("🔍 Market Scanner initialized")

    def _init_exchange(self):
        try:
            return ccxt.binance({
                'rateLimit': config.EXCHANGE_RATE_LIMIT,
                'enableRateLimit': True,
                'timeout': config.EXCHANGE_TIMEOUT,
            })
        except Exception as e:
            logger.error(f"❌ Failed to initialize CCXT exchange: {e}")
            return None

    # This is the function that main.py needs. It is guaranteed to exist in this file.
    def get_valid_symbols(self, limit: int = 100) -> list[str]:
        if not self.binance_symbols:
            logger.error("Market scanner not properly connected. Cannot fetch valid symbols.")
            return []
            
        try:
            url = f"{self.coingecko_base}/coins/markets"
            params = {'vs_currency': 'usd', 'order': 'market_cap_desc', 'per_page': limit * 2, 'page': 1}
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            coins_data = response.json()

            validated_symbols = []
            for coin in coins_data:
                symbol_cg = coin.get('symbol', '').upper()
                binance_symbol_candidate = f"{symbol_cg}USDT"
                
                if binance_symbol_candidate in self.binance_symbols and coin.get('total_volume', 0) > config.MIN_VOLUME_USD:
                    validated_symbols.append(binance_symbol_candidate)
                
                if len(validated_symbols) >= limit:
                    break 

            logger.info(f"📊 Found {len(validated_symbols)} valid, high-volume symbols on Binance to analyze.")
            return validated_symbols
            
        except Exception as e:
            logger.error(f"❌ Error fetching or validating coin symbols: {e}")
            return []
    
    def analyze_market_data(self, market_data: dict) -> dict:
        """Analyze market data using the strategy engine"""
        try:
            # Check if we have enough candles for analysis
            min_candles_required = config.MIN_CANDLES  # Fixed: was config.MIN_CANDLES_FOR_SCAN
            
            results = {}
            for symbol, df in market_data.items():
                if df is None or len(df) < min_candles_required:
                    logger.warning(f"Insufficient data for {symbol}: {len(df) if df is not None else 0} candles")
                    continue
                
                # Use the correct method name - run_all_strategies is available in Enhanced7StrategyEngine
                analysis_result = self.strategy_engine.run_all_strategies(df, symbol)
                
                # Use propose_trade_parameters method which is available in Enhanced7StrategyEngine
                if analysis_result.get('signal') != 'HOLD':
                    trade_params = self.strategy_engine.propose_trade_parameters(analysis_result)
                    analysis_result['trade_parameters'] = trade_params
                
                results[symbol] = analysis_result
                
            return results
            
        except Exception as e:
            logger.error(f"❌ Error analyzing market data: {e}")
            return {}