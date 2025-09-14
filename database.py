"""
💾 Database Manager - Simple, reliable database operations
Handles trade signals, performance tracking, and historical data
"""

import sqlite3
import pandas as pd
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import os

class DatabaseManager:
    def __init__(self, db_path: str = "trading_bot.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Signals table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS signals (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        signal_type TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        entry_price REAL NOT NULL,
                        stop_loss REAL,
                        take_profit REAL,
                        strategies TEXT,
                        reasoning TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'ACTIVE',
                        exit_price REAL,
                        exit_reason TEXT,
                        exit_timestamp DATETIME,
                        profit_loss REAL,
                        profit_percentage REAL
                    )
                """)
                
                # Performance table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS performance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date DATE NOT NULL,
                        total_signals INTEGER DEFAULT 0,
                        successful_signals INTEGER DEFAULT 0,
                        failed_signals INTEGER DEFAULT 0,
                        total_profit_loss REAL DEFAULT 0.0,
                        win_rate REAL DEFAULT 0.0,
                        avg_profit REAL DEFAULT 0.0,
                        avg_loss REAL DEFAULT 0.0,
                        max_drawdown REAL DEFAULT 0.0,
                        sharpe_ratio REAL DEFAULT 0.0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Market data cache table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS market_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        timeframe TEXT NOT NULL,
                        timestamp DATETIME NOT NULL,
                        open_price REAL NOT NULL,
                        high_price REAL NOT NULL,
                        low_price REAL NOT NULL,
                        close_price REAL NOT NULL,
                        volume REAL NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(symbol, timeframe, timestamp)
                    )
                """)
                
                # Strategy performance table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS strategy_performance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        strategy_name TEXT NOT NULL,
                        total_signals INTEGER DEFAULT 0,
                        successful_signals INTEGER DEFAULT 0,
                        win_rate REAL DEFAULT 0.0,
                        avg_confidence REAL DEFAULT 0.0,
                        avg_profit REAL DEFAULT 0.0,
                        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Active trades monitoring
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS active_trades (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        signal_id INTEGER NOT NULL,
                        symbol TEXT NOT NULL,
                        signal_type TEXT NOT NULL,
                        entry_price REAL NOT NULL,
                        current_price REAL,
                        stop_loss REAL,
                        take_profit REAL,
                        profit_loss REAL DEFAULT 0.0,
                        profit_percentage REAL DEFAULT 0.0,
                        duration_hours REAL DEFAULT 0.0,
                        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (signal_id) REFERENCES signals (id)
                    )
                """)
                
                conn.commit()
                self.logger.info("Database initialized successfully")
                
        except Exception as e:
            self.logger.error(f"Database initialization error: {e}")
            raise
    
    def save_signal(self, signal_data: Dict) -> int:
        """Save a new trading signal to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Convert strategies dict to JSON string
                strategies_json = json.dumps(signal_data.get('strategies', {}))
                
                cursor.execute("""
                    INSERT INTO signals (
                        symbol, signal_type, confidence, entry_price, 
                        stop_loss, take_profit, strategies, reasoning
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    signal_data['symbol'],
                    signal_data['signal'],
                    signal_data['confidence'],
                    signal_data['entry_price'],
                    signal_data.get('stop_loss'),
                    signal_data.get('take_profit'),
                    strategies_json,
                    signal_data.get('reason', '')
                ))
                
                signal_id = cursor.lastrowid
                
                if signal_id is None:
                    self.logger.error("Failed to get signal ID after insert")
                    return -1
                
                # Add to active trades if not HOLD
                if signal_data['signal'] != 'HOLD':
                    cursor.execute("""
                        INSERT INTO active_trades (
                            signal_id, symbol, signal_type, entry_price, 
                            stop_loss, take_profit
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        signal_id,
                        signal_data['symbol'],
                        signal_data['signal'],
                        signal_data['entry_price'],
                        signal_data.get('stop_loss'),
                        signal_data.get('take_profit')
                    ))
                
                conn.commit()
                self.logger.info(f"Signal saved: {signal_data['symbol']} - {signal_data['signal']}")
                return signal_id
                
        except Exception as e:
            self.logger.error(f"Error saving signal: {e}")
            return -1
    
    def get_active_trades(self) -> pd.DataFrame:
        """Get all active trades"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT at.*, s.timestamp as entry_timestamp
                    FROM active_trades at
                    JOIN signals s ON at.signal_id = s.id
                    ORDER BY at.last_updated DESC
                """
                return pd.read_sql_query(query, conn)
        except Exception as e:
            self.logger.error(f"Error getting active trades: {e}")
            return pd.DataFrame()
    
    def update_active_trade(self, signal_id: int, current_price: float, 
                           profit_loss: float, profit_percentage: float):
        """Update active trade with current market data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Calculate duration
                cursor.execute("""
                    SELECT s.timestamp 
                    FROM signals s 
                    JOIN active_trades at ON s.id = at.signal_id 
                    WHERE at.signal_id = ?
                """, (signal_id,))
                
                result = cursor.fetchone()
                if result:
                    entry_time = datetime.fromisoformat(result[0])
                    duration_hours = (datetime.now() - entry_time).total_seconds() / 3600
                else:
                    duration_hours = 0
                
                cursor.execute("""
                    UPDATE active_trades 
                    SET current_price = ?, profit_loss = ?, profit_percentage = ?, 
                        duration_hours = ?, last_updated = CURRENT_TIMESTAMP
                    WHERE signal_id = ?
                """, (current_price, profit_loss, profit_percentage, duration_hours, signal_id))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error updating active trade: {e}")
    
    def close_trade(self, signal_id: int, exit_price: float, exit_reason: str):
        """Close an active trade"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get trade details
                cursor.execute("""
                    SELECT entry_price, signal_type FROM signals WHERE id = ?
                """, (signal_id,))
                
                result = cursor.fetchone()
                if not result:
                    return False
                
                entry_price, signal_type = result
                
                # Calculate final P&L
                if signal_type == 'BUY':
                    profit_percentage = ((exit_price - entry_price) / entry_price) * 100
                else:  # SELL
                    profit_percentage = ((entry_price - exit_price) / entry_price) * 100
                
                # Update signal table
                cursor.execute("""
                    UPDATE signals 
                    SET status = 'CLOSED', exit_price = ?, exit_reason = ?, 
                        exit_timestamp = CURRENT_TIMESTAMP, profit_percentage = ?
                    WHERE id = ?
                """, (exit_price, exit_reason, profit_percentage, signal_id))
                
                # Remove from active trades
                cursor.execute("DELETE FROM active_trades WHERE signal_id = ?", (signal_id,))
                
                conn.commit()
                self.logger.info(f"Trade closed: Signal {signal_id}, P&L: {profit_percentage:.2f}%")
                return True
                
        except Exception as e:
            self.logger.error(f"Error closing trade: {e}")
            return False
    
    def get_recent_signals(self, hours: int = 24, status: Optional[str] = None) -> pd.DataFrame:
        """Get recent signals within specified hours"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT * FROM signals 
                    WHERE timestamp >= datetime('now', '-{} hours')
                """.format(hours)
                
                if status:
                    query += f" AND status = '{status}'"
                
                query += " ORDER BY timestamp DESC"
                
                return pd.read_sql_query(query, conn)
        except Exception as e:
            self.logger.error(f"Error getting recent signals: {e}")
            return pd.DataFrame()
    
    def calculate_performance_metrics(self, days: int = 7) -> Dict:
        """Calculate performance metrics for the last N days"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get closed trades from last N days
                query = """
                    SELECT profit_percentage, signal_type, confidence, exit_reason
                    FROM signals 
                    WHERE status = 'CLOSED' 
                    AND timestamp >= datetime('now', '-{} days')
                """.format(days)
                
                df = pd.read_sql_query(query, conn)
                
                if df.empty:
                    return {
                        'total_trades': 0,
                        'win_rate': 0,
                        'avg_profit': 0,
                        'avg_loss': 0,
                        'total_return': 0,
                        'profitable_trades': 0,
                        'losing_trades': 0
                    }
                
                # Calculate metrics
                profitable_trades = len(df[df['profit_percentage'] > 0])
                losing_trades = len(df[df['profit_percentage'] < 0])
                total_trades = len(df)
                
                win_rate = (profitable_trades / total_trades) * 100 if total_trades > 0 else 0
                avg_profit = df[df['profit_percentage'] > 0]['profit_percentage'].mean() if profitable_trades > 0 else 0
                avg_loss = df[df['profit_percentage'] < 0]['profit_percentage'].mean() if losing_trades > 0 else 0
                total_return = df['profit_percentage'].sum()
                
                return {
                    'total_trades': total_trades,
                    'win_rate': round(win_rate, 2),
                    'avg_profit': round(avg_profit, 2),
                    'avg_loss': round(avg_loss, 2),
                    'total_return': round(total_return, 2),
                    'profitable_trades': profitable_trades,
                    'losing_trades': losing_trades,
                    'profit_factor': round(abs(avg_profit * profitable_trades / (avg_loss * losing_trades)), 2) if losing_trades > 0 and avg_loss != 0 else 0
                }
                
        except Exception as e:
            self.logger.error(f"Error calculating performance: {e}")
            return {}
    
    def save_market_data(self, symbol: str, timeframe: str, data: pd.DataFrame):
        """Save market data to cache"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Prepare data
                data_to_save = data.copy()
                data_to_save['symbol'] = symbol
                data_to_save['timeframe'] = timeframe
                data_to_save['timestamp'] = data_to_save.index
                
                # Rename columns to match database
                column_mapping = {
                    'open': 'open_price',
                    'high': 'high_price', 
                    'low': 'low_price',
                    'close': 'close_price'
                }
                data_to_save = data_to_save.rename(columns=column_mapping)
                
                # Select only required columns
                required_cols = ['symbol', 'timeframe', 'timestamp', 'open_price', 
                               'high_price', 'low_price', 'close_price', 'volume']
                data_to_save = data_to_save[required_cols]
                
                # Insert data (ignore duplicates)
                data_to_save.to_sql('market_data', conn, if_exists='append', 
                                   index=False)
                
        except Exception as e:
            self.logger.error(f"Error saving market data: {e}")
    
    def get_market_data(self, symbol: str, timeframe: str, 
                       hours_back: int = 168) -> pd.DataFrame:
        """Get cached market data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT timestamp, open_price, high_price, low_price, 
                           close_price, volume
                    FROM market_data 
                    WHERE symbol = ? AND timeframe = ?
                    AND timestamp >= datetime('now', '-{} hours')
                    ORDER BY timestamp ASC
                """.format(hours_back)
                
                df = pd.read_sql_query(query, conn, params=(symbol, timeframe))
                
                if not df.empty:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df.set_index('timestamp', inplace=True)
                    
                    # Rename columns back
                    column_mapping = {
                        'open_price': 'open',
                        'high_price': 'high',
                        'low_price': 'low', 
                        'close_price': 'close'
                    }
                    df = df.rename(columns=column_mapping)
                
                return df
                
        except Exception as e:
            self.logger.error(f"Error getting market data: {e}")
            return pd.DataFrame()
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old data to keep database size manageable"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Clean old market data
                cursor.execute("""
                    DELETE FROM market_data 
                    WHERE created_at < datetime('now', '-{} days')
                """.format(days_to_keep))
                
                # Keep closed signals for longer (90 days)
                cursor.execute("""
                    DELETE FROM signals 
                    WHERE status = 'CLOSED' 
                    AND timestamp < datetime('now', '-90 days')
                """)
                
                conn.commit()
                self.logger.info(f"Cleaned up data older than {days_to_keep} days")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up data: {e}")
    
    def get_strategy_performance(self) -> pd.DataFrame:
        """Get performance breakdown by strategy"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT strategies, profit_percentage, confidence, signal_type
                    FROM signals 
                    WHERE status = 'CLOSED' 
                    AND timestamp >= datetime('now', '-30 days')
                """
                
                df = pd.read_sql_query(query, conn)
                
                if df.empty:
                    return pd.DataFrame()
                
                # Parse strategies JSON and analyze
                strategy_performance = []
                
                for _, row in df.iterrows():
                    try:
                        strategies = json.loads(row['strategies'])
                        for strategy_name, strategy_data in strategies.items():
                            if strategy_data.get('signal') == row['signal_type']:
                                strategy_performance.append({
                                    'strategy': strategy_name,
                                    'profit': row['profit_percentage'],
                                    'confidence': strategy_data.get('confidence', 0)
                                })
                    except:
                        continue
                
                if strategy_performance:
                    return pd.DataFrame(strategy_performance)
                
                return pd.DataFrame()
                
        except Exception as e:
            self.logger.error(f"Error getting strategy performance: {e}")
            return pd.DataFrame()
    
    def export_data(self, output_path: Optional[str] = None) -> str:
        """Export all data to CSV files"""
        try:
            if not output_path:
                output_path = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            os.makedirs(output_path, exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                # Export all tables
                tables = ['signals', 'performance', 'market_data', 'active_trades']
                
                for table in tables:
                    df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
                    df.to_csv(f"{output_path}/{table}.csv", index=False)
                
            self.logger.info(f"Data exported to {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error exporting data: {e}")
            return ""