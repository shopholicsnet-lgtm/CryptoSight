"""
🔔 Discord Bot - Real-time trading notifications
Sends professional trading alerts to Discord channels
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Optional
import logging

class DiscordNotifier:
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url
        self.logger = logging.getLogger(__name__)
        self.enabled = bool(webhook_url)
        
        # Emoji mappings
        self.emojis = {
            'BUY': '🚀',
            'SELL': '📉', 
            'HOLD': '⏸️',
            'PROFIT': '💰',
            'LOSS': '🔻',
            'WARNING': '⚠️',
            'INFO': 'ℹ️',
            'SUCCESS': '✅',
            'ERROR': '❌'
        }
        
        # Color mappings (Discord embed colors)
        self.colors = {
            'BUY': 0x00ff00,    # Green
            'SELL': 0xff0000,   # Red
            'PROFIT': 0x00ff00, # Green
            'LOSS': 0xff0000,   # Red
            'WARNING': 0xffff00, # Yellow
            'INFO': 0x0099ff,   # Blue
            'NEUTRAL': 0x808080  # Gray
        }
    
    def send_signal_alert(self, signal_data: Dict, risk_validation: Optional[Dict] = None) -> bool:
        """Send new trading signal alert"""
        if not self.enabled or not self.webhook_url:
            return False
        
        try:
            signal_type = signal_data['signal']
            symbol = signal_data['symbol']
            confidence = signal_data['confidence']
            entry_price = signal_data['entry_price']
            
            # Create rich embed
            embed = {
                "title": f"{self.emojis[signal_type]} NEW {signal_type} SIGNAL",
                "description": f"**{symbol}** - High confidence signal detected!",
                "color": self.colors[signal_type],
                "timestamp": datetime.now().isoformat(),
                "fields": [
                    {
                        "name": "📊 Signal Details",
                        "value": f"**Symbol:** {symbol}\n**Action:** {signal_type}\n**Confidence:** {confidence:.1f}%",
                        "inline": True
                    },
                    {
                        "name": "💵 Price Levels",
                        "value": f"**Entry:** ${entry_price:.4f}\n**Stop Loss:** ${signal_data.get('stop_loss', 0):.4f}\n**Take Profit:** ${signal_data.get('take_profit', 0):.4f}",
                        "inline": True
                    }
                ],
                "footer": {
                    "text": "🎯 CryptoSight v3.0 - AI Trading Bot",
                    "icon_url": "https://i.imgur.com/your-bot-icon.png"
                }
            }
            
            # Add risk information if available
            if risk_validation:
                risk_field = {
                    "name": "🛡️ Risk Management",
                    "value": f"**Risk Score:** {risk_validation.get('risk_score', 0)}/100\n**Position Size:** {risk_validation.get('position_size', 0):.2f}\n**Risk Amount:** ${risk_validation.get('risk_amount', 0):.2f}",
                    "inline": False
                }
                embed["fields"].append(risk_field)
            
            # Add strategy breakdown
            if 'strategies' in signal_data:
                strategy_text = ""
                for strategy, data in signal_data['strategies'].items():
                    if data['signal'] == signal_type:
                        strategy_text += f"• {strategy}: {data['confidence']:.0f}%\n"
                
                if strategy_text:
                    embed["fields"].append({
                        "name": "🧠 Active Strategies",
                        "value": strategy_text[:1024],  # Discord field limit
                        "inline": False
                    })
            
            # Add reasoning
            if signal_data.get('reason'):
                embed["fields"].append({
                    "name": "📝 Analysis",
                    "value": signal_data['reason'][:1024],
                    "inline": False
                })
            
            payload = {
                "username": "CryptoSight Bot",
                "avatar_url": "https://i.imgur.com/your-bot-avatar.png",
                "embeds": [embed]
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            self.logger.info(f"Signal alert sent: {symbol} - {signal_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending signal alert: {e}")
            return False
    
    def send_trade_update(self, trade_data: Dict) -> bool:
        """Send trade status update"""
        if not self.enabled or not self.webhook_url:
            return False
        
        try:
            symbol = trade_data['symbol']
            pnl = trade_data.get('pnl_percentage', 0)
            status = trade_data.get('status', 'ACTIVE')
            
            # Determine color and emoji based on P&L
            if pnl > 0:
                color = self.colors['PROFIT']
                emoji = self.emojis['PROFIT']
            elif pnl < 0:
                color = self.colors['LOSS']
                emoji = self.emojis['LOSS']
            else:
                color = self.colors['NEUTRAL']
                emoji = self.emojis['INFO']
            
            embed = {
                "title": f"{emoji} Trade Update - {symbol}",
                "description": f"Current P&L: **{pnl:+.2f}%**",
                "color": color,
                "timestamp": datetime.now().isoformat(),
                "fields": [
                    {
                        "name": "📊 Trade Status",
                        "value": f"**Status:** {status}\n**Duration:** {trade_data.get('duration', 'N/A')}\n**Current Price:** ${trade_data.get('current_price', 0):.4f}",
                        "inline": True
                    }
                ],
                "footer": {
                    "text": "🎯 CryptoSight v3.0 - Live Monitoring"
                }
            }
            
            payload = {
                "username": "CryptoSight Monitor",
                "embeds": [embed]
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending trade update: {e}")
            return False
    
    def send_trade_closed(self, trade_result: Dict) -> bool:
        """Send trade closure notification"""
        if not self.enabled or not self.webhook_url:
            return False
        
        try:
            symbol = trade_result['symbol']
            pnl = trade_result['pnl_percentage']
            exit_reason = trade_result['exit_reason']
            
            # Determine outcome
            if pnl > 0:
                outcome = "PROFIT"
                emoji = "💰"
                color = self.colors['PROFIT']
            else:
                outcome = "LOSS"
                emoji = "🔻"
                color = self.colors['LOSS']
            
            embed = {
                "title": f"{emoji} Trade Closed - {symbol}",
                "description": f"**{outcome}:** {pnl:+.2f}%",
                "color": color,
                "timestamp": datetime.now().isoformat(),
                "fields": [
                    {
                        "name": "📊 Final Results",
                        "value": f"**P&L:** {pnl:+.2f}%\n**Exit Reason:** {exit_reason}\n**Duration:** {trade_result.get('duration', 'N/A')}",
                        "inline": True
                    },
                    {
                        "name": "💵 Price Levels",
                        "value": f"**Entry:** ${trade_result.get('entry_price', 0):.4f}\n**Exit:** ${trade_result.get('exit_price', 0):.4f}\n**Profit:** ${trade_result.get('realized_pnl', 0):.2f}",
                        "inline": True
                    }
                ],
                "footer": {
                    "text": "🎯 CryptoSight v3.0 - Trade Complete"
                }
            }
            
            payload = {
                "username": "CryptoSight Results",
                "embeds": [embed]
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            self.logger.info(f"Trade closure alert sent: {symbol} - {pnl:+.2f}%")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending trade closure: {e}")
            return False
    
    def send_performance_summary(self, performance_data: Dict) -> bool:
        """Send daily/weekly performance summary"""
        if not self.enabled or not self.webhook_url:
            return False
        
        try:
            win_rate = performance_data.get('win_rate', 0)
            total_return = performance_data.get('total_return', 0)
            total_trades = performance_data.get('total_trades', 0)
            
            # Performance grade
            if win_rate >= 70 and total_return >= 5:
                grade = "A+"
                emoji = "🏆"
                color = self.colors['PROFIT']
            elif win_rate >= 60 and total_return >= 3:
                grade = "A"
                emoji = "🥇"
                color = self.colors['PROFIT']
            elif win_rate >= 50 and total_return >= 1:
                grade = "B"
                emoji = "📈"
                color = self.colors['INFO']
            else:
                grade = "C"
                emoji = "📊"
                color = self.colors['WARNING']
            
            embed = {
                "title": f"{emoji} Performance Summary - Grade {grade}",
                "description": f"Trading performance overview",
                "color": color,
                "timestamp": datetime.now().isoformat(),
                "fields": [
                    {
                        "name": "📊 Key Metrics",
                        "value": f"**Total Return:** {total_return:+.2f}%\n**Win Rate:** {win_rate:.1f}%\n**Total Trades:** {total_trades}",
                        "inline": True
                    },
                    {
                        "name": "💰 Profit Analysis",
                        "value": f"**Avg Profit:** {performance_data.get('avg_profit', 0):.2f}%\n**Avg Loss:** {performance_data.get('avg_loss', 0):.2f}%\n**Profit Factor:** {performance_data.get('profit_factor', 0):.2f}",
                        "inline": True
                    }
                ],
                "footer": {
                    "text": "🎯 CryptoSight v3.0 - Performance Report"
                }
            }
            
            payload = {
                "username": "CryptoSight Analytics",
                "embeds": [embed]
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending performance summary: {e}")
            return False
    
    def send_alert(self, title: str, message: str, alert_type: str = 'INFO') -> bool:
        """Send general alert"""
        if not self.enabled or not self.webhook_url:
            return False
        
        try:
            embed = {
                "title": f"{self.emojis.get(alert_type, 'ℹ️')} {title}",
                "description": message,
                "color": self.colors.get(alert_type, self.colors['INFO']),
                "timestamp": datetime.now().isoformat(),
                "footer": {
                    "text": "🎯 CryptoSight v3.0"
                }
            }
            
            payload = {
                "username": "CryptoSight Alert",
                "embeds": [embed]
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending alert: {e}")
            return False
    
    def send_system_status(self, status_data: Dict) -> bool:
        """Send system health status"""
        if not self.enabled or not self.webhook_url:
            return False
        
        try:
            active_trades = status_data.get('active_trades', 0)
            capital = status_data.get('current_capital', 0)
            daily_pnl = status_data.get('daily_pnl', 0)
            
            embed = {
                "title": "🤖 System Status Report",
                "description": "Trading bot operational status",
                "color": self.colors['INFO'],
                "timestamp": datetime.now().isoformat(),
                "fields": [
                    {
                        "name": "💼 Portfolio Status",
                        "value": f"**Capital:** ${capital:.2f}\n**Daily P&L:** ${daily_pnl:+.2f}\n**Active Trades:** {active_trades}",
                        "inline": True
                    },
                    {
                        "name": "🛡️ Risk Status",
                        "value": f"**Portfolio Risk:** {status_data.get('portfolio_risk_used', 0):.1f}%\n**Daily Risk:** {status_data.get('daily_risk_used', 0):.1f}%\n**Drawdown:** {status_data.get('current_drawdown', 0):.1f}%",
                        "inline": True
                    }
                ],
                "footer": {
                    "text": "🎯 CryptoSight v3.0 - System Monitor"
                }
            }
            
            payload = {
                "username": "CryptoSight System",
                "embeds": [embed]
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending system status: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test Discord webhook connection"""
        if not self.enabled or not self.webhook_url:
            return False
        
        return self.send_alert(
            "Connection Test",
            "🎯 CryptoSight Discord integration is working!",
            "SUCCESS"
        )