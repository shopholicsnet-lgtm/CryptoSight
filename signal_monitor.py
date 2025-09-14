"""
📈 Signal Monitor - Live trade monitoring and management
Tracks active trades and handles automatic exits based on SL/TP.
"""

import pandas as pd
from datetime import datetime
import time
import threading
from typing import Dict, List, Optional
import logging

from database import DatabaseManager
from risk_manager import RiskManager
from discord_bot import DiscordNotifier
from data_fetcher import DataFetcher

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SignalMonitor:
    def __init__(self, db_manager: DatabaseManager, risk_manager: RiskManager, 
                 discord_notifier: Optional[DiscordNotifier], data_fetcher: DataFetcher):
        self.db_manager = db_manager
        self.risk_manager = risk_manager
        self.discord_notifier = discord_notifier
        self.data_fetcher = data_fetcher
        
        self.monitoring_interval_seconds = 60
        self.is_monitoring = False
        self.monitor_thread = None
        
        self.update_count = 0
        self.error_count = 0
        self.last_update = None
        
    def start_monitoring(self):
        """Starts the live trade monitoring in a background thread."""
        if self.is_monitoring:
            logger.warning("Monitoring is already active.")
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("✅ Signal monitoring thread started.")
        
        if self.discord_notifier:
            self.discord_notifier.send_alert("Monitor Started", "🚀 Live trade monitoring is now active!", "SUCCESS")
    
    def stop_monitoring(self):
        """Stops the live trade monitoring thread."""
        self.is_monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=10)
        
        logger.info("⏹️ Signal monitoring stopped.")
        if self.discord_notifier:
            self.discord_notifier.send_alert("Monitor Stopped", "⏹️ Live trade monitoring has been stopped.", "WARNING")
    
    def _monitoring_loop(self):
        """The main loop that runs in the background to check trades."""
        while self.is_monitoring:
            try:
                active_trades = self.db_manager.get_active_trades()
                
                if not active_trades.empty:
                    logger.info(f"Monitoring {len(active_trades)} active trades...")
                    for _, trade in active_trades.iterrows():
                        if not self.is_monitoring: break
                        self._update_trade(trade)
                
                self.update_count += 1
                self.last_update = datetime.now()
                
            except Exception as e:
                self.error_count += 1
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
            
            # Wait for the next interval, checking periodically to stop faster
            for _ in range(self.monitoring_interval_seconds):
                if not self.is_monitoring: break
                time.sleep(1)
    
    def _update_trade(self, trade: pd.Series):
        """Updates a single trade with the latest market data and checks for exit."""
        try:
            symbol = trade['symbol']
            signal_id = trade['signal_id']
            
            # Get the most recent price
            ticker = self.data_fetcher.get_ticker(symbol)
            if not ticker or 'last' not in ticker:
                logger.warning(f"Could not fetch current price for {symbol}.")
                return

            current_price = ticker['last']
            
            # Let the Risk Manager calculate P&L and check for exits
            position_update = self.risk_manager.update_position(signal_id, current_price)
            if not position_update: return

            # Save the latest stats to the database
            self.db_manager.update_active_trade(
                signal_id=signal_id,
                current_price=current_price,
                profit_loss=position_update.get('unrealized_pnl', 0),
                profit_percentage=position_update.get('pnl_percentage', 0)
            )
            
            # If the Risk Manager signals an exit, execute it
            exit_reason = position_update.get('exit_signal')
            if exit_reason:
                self._execute_exit(trade, current_price, exit_reason)
            
        except Exception as e:
            logger.error(f"Error updating trade for {trade.get('symbol', 'unknown')}: {e}")

    def _execute_exit(self, trade: pd.Series, exit_price: float, exit_reason: str):
        """Handles the process of closing a trade."""
        try:
            signal_id = trade['signal_id']
            symbol = trade['symbol']
            
            logger.info(f"Executing exit for {symbol} at ${exit_price:.4f}. Reason: {exit_reason}")
            
            # Finalize P&L with the Risk Manager and update capital
            close_result = self.risk_manager.close_position(signal_id, exit_price, exit_reason)
            
            # Update the trade's status to 'CLOSED' in the database
            self.db_manager.close_trade(signal_id, exit_price, exit_reason)
            
            # Send notification if available
            if self.discord_notifier and close_result:
                self.discord_notifier.send_trade_closed({
                    'symbol': symbol,
                    'pnl_percentage': close_result.get('pnl_percentage', 0),
                    'exit_reason': exit_reason,
                    'entry_price': trade['entry_price'],
                    'exit_price': exit_price,
                    'realized_pnl': close_result.get('realized_pnl', 0)
                })
        except Exception as e:
            logger.error(f"Failed to execute exit for {trade['symbol']}: {e}", exc_info=True)

    def get_monitoring_status(self) -> Dict:
        """Gets the current status of the monitor for the UI."""
        return {
            'is_monitoring': self.is_monitoring,
            'update_count': self.update_count,
            'error_count': self.error_count,
            'last_update': self.last_update.isoformat() if self.last_update else 'Never'
        }