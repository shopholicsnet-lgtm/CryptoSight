"""
🛡️ Risk Manager - Professional Risk Management System
Protects capital with dynamic position sizing and risk controls
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime, timedelta

class RiskManager:
    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.max_risk_per_trade = 0.02  # 2% max risk per trade
        self.max_daily_risk = 0.06  # 6% max daily risk
        self.max_portfolio_risk = 0.20  # 20% max portfolio risk
        self.max_drawdown_limit = 0.15  # 15% max drawdown
        self.min_confidence_threshold = 0.60  # 60% minimum confidence
        self.logger = logging.getLogger(__name__)
        
        # Risk tracking
        self.daily_risk_used = 0.0
        self.current_positions = {}
        self.daily_pnl = 0.0
        self.peak_capital = initial_capital
        
    def validate_signal(self, signal_data: Dict, market_volatility: float = 0.03) -> Dict:
        """
        Comprehensive signal validation with risk assessment
        """
        validation_result = {
            'approved': False,
            'risk_score': 0,
            'position_size': 0,
            'adjusted_stop_loss': 0,
            'adjusted_take_profit': 0,
            'risk_amount': 0,
            'warnings': [],
            'rejection_reasons': []
        }
        
        try:
            # Basic validation
            if signal_data['signal'] == 'HOLD':
                validation_result['rejection_reasons'].append("HOLD signal - no trade")
                return validation_result
            
            confidence = signal_data.get('confidence', 0)
            entry_price = signal_data.get('entry_price', 0)
            stop_loss = signal_data.get('stop_loss', 0)
            take_profit = signal_data.get('take_profit', 0)
            
            # Confidence check
            if confidence < self.min_confidence_threshold * 100:
                validation_result['rejection_reasons'].append(
                    f"Low confidence: {confidence:.1f}% < {self.min_confidence_threshold*100:.1f}%"
                )
                return validation_result
            
            # Price validation
            if entry_price <= 0 or stop_loss <= 0 or take_profit <= 0:
                validation_result['rejection_reasons'].append("Invalid price levels")
                return validation_result
            
            # Risk/reward validation
            if signal_data['signal'] == 'BUY':
                risk_per_unit = abs(entry_price - stop_loss)
                reward_per_unit = abs(take_profit - entry_price)
            else:  # SELL
                risk_per_unit = abs(stop_loss - entry_price)
                reward_per_unit = abs(entry_price - take_profit)
            
            risk_reward_ratio = reward_per_unit / risk_per_unit if risk_per_unit > 0 else 0
            
            if risk_reward_ratio < 1.5:  # Minimum 1.5:1 risk/reward
                validation_result['rejection_reasons'].append(
                    f"Poor risk/reward ratio: {risk_reward_ratio:.2f} < 1.5"
                )
                return validation_result
            
            # Calculate position size
            risk_percentage = risk_per_unit / entry_price
            max_position_value = (self.current_capital * self.max_risk_per_trade) / risk_percentage
            position_size = max_position_value / entry_price
            risk_amount = position_size * risk_per_unit
            
            # Daily risk limit check
            if self.daily_risk_used + risk_amount > self.current_capital * self.max_daily_risk:
                validation_result['rejection_reasons'].append(
                    f"Daily risk limit exceeded: {self.daily_risk_used + risk_amount:.2f} > {self.current_capital * self.max_daily_risk:.2f}"
                )
                return validation_result
            
            # Portfolio risk limit check
            total_portfolio_risk = sum([pos['risk_amount'] for pos in self.current_positions.values()]) + risk_amount
            if total_portfolio_risk > self.current_capital * self.max_portfolio_risk:
                validation_result['rejection_reasons'].append(
                    f"Portfolio risk limit exceeded: {total_portfolio_risk:.2f} > {self.current_capital * self.max_portfolio_risk:.2f}"
                )
                return validation_result
            
            # Drawdown check
            current_drawdown = (self.peak_capital - self.current_capital) / self.peak_capital
            if current_drawdown > self.max_drawdown_limit:
                validation_result['rejection_reasons'].append(
                    f"Maximum drawdown exceeded: {current_drawdown:.2%} > {self.max_drawdown_limit:.2%}"
                )
                return validation_result
            
            # Volatility adjustment
            volatility_multiplier = min(2.0, max(0.5, market_volatility / 0.03))  # Adjust based on 3% baseline
            adjusted_position_size = position_size / volatility_multiplier
            adjusted_risk_amount = adjusted_position_size * risk_per_unit
            
            # Risk score calculation (0-100)
            risk_score = self._calculate_risk_score(
                confidence, risk_reward_ratio, market_volatility, 
                adjusted_risk_amount / self.current_capital
            )
            
            # Warnings
            warnings = []
            if risk_reward_ratio < 2.0:
                warnings.append(f"Low R:R ratio: {risk_reward_ratio:.2f}")
            if market_volatility > 0.05:
                warnings.append(f"High volatility: {market_volatility:.1%}")
            if confidence < 70:
                warnings.append(f"Moderate confidence: {confidence:.1f}%")
            
            # Final approval
            validation_result.update({
                'approved': True,
                'risk_score': risk_score,
                'position_size': adjusted_position_size,
                'adjusted_stop_loss': stop_loss,
                'adjusted_take_profit': take_profit,
                'risk_amount': adjusted_risk_amount,
                'risk_reward_ratio': risk_reward_ratio,
                'warnings': warnings,
                'position_value': adjusted_position_size * entry_price,
                'risk_percentage': (adjusted_risk_amount / self.current_capital) * 100
            })
            
            return validation_result
            
        except Exception as e:
            validation_result['rejection_reasons'].append(f"Validation error: {e}")
            self.logger.error(f"Risk validation error: {e}")
            return validation_result
    
    def _calculate_risk_score(self, confidence: float, risk_reward: float, 
                            volatility: float, risk_percentage: float) -> int:
        """Calculate overall risk score (0-100, higher is better)"""
        
        # Base score from confidence
        score = confidence
        
        # Risk/reward bonus
        if risk_reward >= 3.0:
            score += 15
        elif risk_reward >= 2.0:
            score += 10
        elif risk_reward >= 1.5:
            score += 5
        
        # Volatility penalty
        if volatility > 0.05:
            score -= 10
        elif volatility > 0.04:
            score -= 5
        
        # Risk percentage penalty
        if risk_percentage > 0.015:  # > 1.5%
            score -= 10
        elif risk_percentage > 0.01:  # > 1%
            score -= 5
        
        return max(0, min(100, int(score)))
    
    def add_position(self, signal_id: int, symbol: str, signal_data: Dict, 
                    validation_result: Dict):
        """Add new position to risk tracking"""
        try:
            position = {
                'signal_id': signal_id,
                'symbol': symbol,
                'signal_type': signal_data['signal'],
                'entry_price': signal_data['entry_price'],
                'position_size': validation_result['position_size'],
                'stop_loss': validation_result['adjusted_stop_loss'],
                'take_profit': validation_result['adjusted_take_profit'],
                'risk_amount': validation_result['risk_amount'],
                'position_value': validation_result['position_value'],
                'entry_time': datetime.now(),
                'unrealized_pnl': 0.0
            }
            
            self.current_positions[signal_id] = position
            self.daily_risk_used += validation_result['risk_amount']
            
            self.logger.info(f"Position added: {symbol} - Risk: ${validation_result['risk_amount']:.2f}")
            
        except Exception as e:
            self.logger.error(f"Error adding position: {e}")
    
    def update_position(self, signal_id: int, current_price: float) -> Dict:
        """Update position with current market price"""
        try:
            if signal_id not in self.current_positions:
                return {}
            
            position = self.current_positions[signal_id]
            entry_price = position['entry_price']
            position_size = position['position_size']
            signal_type = position['signal_type']
            
            # Calculate unrealized P&L
            if signal_type == 'BUY':
                unrealized_pnl = (current_price - entry_price) * position_size
                pnl_percentage = ((current_price - entry_price) / entry_price) * 100
            else:  # SELL
                unrealized_pnl = (entry_price - current_price) * position_size
                pnl_percentage = ((entry_price - current_price) / entry_price) * 100
            
            position['unrealized_pnl'] = unrealized_pnl
            position['current_price'] = current_price
            position['pnl_percentage'] = pnl_percentage
            
            # Check exit conditions
            exit_signal = self._check_exit_conditions(position, current_price)
            
            return {
                'unrealized_pnl': unrealized_pnl,
                'pnl_percentage': pnl_percentage,
                'exit_signal': exit_signal,
                'position_value': position_size * current_price,
                'risk_amount': position['risk_amount']
            }
            
        except Exception as e:
            self.logger.error(f"Error updating position: {e}")
            return {}
    
    def _check_exit_conditions(self, position: Dict, current_price: float) -> Optional[str]:
        """Check if position should be closed"""
        try:
            signal_type = position['signal_type']
            stop_loss = position['stop_loss']
            take_profit = position['take_profit']
            entry_time = position['entry_time']
            
            # Stop loss check
            if signal_type == 'BUY' and current_price <= stop_loss:
                return 'STOP_LOSS'
            elif signal_type == 'SELL' and current_price >= stop_loss:
                return 'STOP_LOSS'
            
            # Take profit check
            if signal_type == 'BUY' and current_price >= take_profit:
                return 'TAKE_PROFIT'
            elif signal_type == 'SELL' and current_price <= take_profit:
                return 'TAKE_PROFIT'
            
            # Time-based exit (24 hours for daily signals)
            hours_elapsed = (datetime.now() - entry_time).total_seconds() / 3600
            if hours_elapsed > 24:
                return 'TIME_EXIT'
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error checking exit conditions: {e}")
            return None
    
    def close_position(self, signal_id: int, exit_price: float, exit_reason: str) -> Dict:
        """Close position and update capital"""
        try:
            if signal_id not in self.current_positions:
                return {}
            
            position = self.current_positions[signal_id]
            entry_price = position['entry_price']
            position_size = position['position_size']
            signal_type = position['signal_type']
            
            # Calculate realized P&L
            if signal_type == 'BUY':
                realized_pnl = (exit_price - entry_price) * position_size
                pnl_percentage = ((exit_price - entry_price) / entry_price) * 100
            else:  # SELL
                realized_pnl = (entry_price - exit_price) * position_size
                pnl_percentage = ((entry_price - exit_price) / entry_price) * 100
            
            # Update capital
            self.current_capital += realized_pnl
            self.daily_pnl += realized_pnl
            
            # Update peak capital if new high
            if self.current_capital > self.peak_capital:
                self.peak_capital = self.current_capital
            
            # Remove from current positions
            del self.current_positions[signal_id]
            
            result = {
                'realized_pnl': realized_pnl,
                'pnl_percentage': pnl_percentage,
                'exit_price': exit_price,
                'exit_reason': exit_reason,
                'new_capital': self.current_capital,
                'trade_duration': datetime.now() - position['entry_time']
            }
            
            self.logger.info(f"Position closed: {position['symbol']} - P&L: ${realized_pnl:.2f} ({pnl_percentage:.2f}%)")
            return result
            
        except Exception as e:
            self.logger.error(f"Error closing position: {e}")
            return {}
    
    def get_portfolio_status(self) -> Dict:
        """Get current portfolio risk status"""
        try:
            total_position_value = sum([pos['position_value'] for pos in self.current_positions.values()])
            total_risk_amount = sum([pos['risk_amount'] for pos in self.current_positions.values()])
            total_unrealized_pnl = sum([pos.get('unrealized_pnl', 0) for pos in self.current_positions.values()])
            
            current_drawdown = (self.peak_capital - self.current_capital) / self.peak_capital
            
            return {
                'current_capital': self.current_capital,
                'initial_capital': self.initial_capital,
                'total_return': ((self.current_capital - self.initial_capital) / self.initial_capital) * 100,
                'peak_capital': self.peak_capital,
                'current_drawdown': current_drawdown * 100,
                'daily_pnl': self.daily_pnl,
                'active_positions': len(self.current_positions),
                'total_position_value': total_position_value,
                'total_risk_amount': total_risk_amount,
                'total_unrealized_pnl': total_unrealized_pnl,
                'portfolio_risk_used': (total_risk_amount / self.current_capital) * 100,
                'daily_risk_used': (self.daily_risk_used / self.current_capital) * 100,
                'risk_limits': {
                    'max_risk_per_trade': self.max_risk_per_trade * 100,
                    'max_daily_risk': self.max_daily_risk * 100,
                    'max_portfolio_risk': self.max_portfolio_risk * 100,
                    'max_drawdown_limit': self.max_drawdown_limit * 100
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting portfolio status: {e}")
            return {}
    
    def reset_daily_limits(self):
        """Reset daily risk limits (call at start of new trading day)"""
        self.daily_risk_used = 0.0
        self.daily_pnl = 0.0
        self.logger.info("Daily risk limits reset")
    
    def adjust_risk_parameters(self, performance_data: Dict):
        """Dynamically adjust risk parameters based on performance"""
        try:
            win_rate = performance_data.get('win_rate', 50)
            total_return = performance_data.get('total_return', 0)
            
            # Increase risk if performing well
            if win_rate > 70 and total_return > 10:
                self.max_risk_per_trade = min(0.025, self.max_risk_per_trade * 1.1)  # Max 2.5%
                self.logger.info("Risk increased due to good performance")
            
            # Decrease risk if performing poorly
            elif win_rate < 40 or total_return < -5:
                self.max_risk_per_trade = max(0.01, self.max_risk_per_trade * 0.9)  # Min 1%
                self.logger.info("Risk decreased due to poor performance")
            
        except Exception as e:
            self.logger.error(f"Error adjusting risk parameters: {e}")
    
    def get_risk_metrics(self) -> Dict:
        """Calculate detailed risk metrics"""
        try:
            positions = list(self.current_positions.values())
            
            if not positions:
                return {
                    'var_95': 0,
                    'max_position_correlation': 0,
                    'concentration_risk': 0,
                    'leverage_ratio': 0
                }
            
            # Value at Risk (simplified)
            position_values = [pos['position_value'] for pos in positions]
            risk_amounts = [pos['risk_amount'] for pos in positions]
            
            var_95 = np.percentile(risk_amounts, 95) if risk_amounts else 0
            
            # Concentration risk (largest position as % of portfolio)
            concentration_risk = max(position_values) / self.current_capital * 100 if position_values else 0
            
            # Leverage ratio
            total_position_value = sum(position_values)
            leverage_ratio = total_position_value / self.current_capital if self.current_capital > 0 else 0
            
            return {
                'var_95': var_95,
                'concentration_risk': concentration_risk,
                'leverage_ratio': leverage_ratio,
                'total_positions': len(positions),
                'avg_position_size': np.mean(position_values) if position_values else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating risk metrics: {e}")
            return {}