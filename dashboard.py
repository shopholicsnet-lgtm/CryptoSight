"""
📊 CryptoSight Streamlit Dashboard - FIXED VERSION
Fully functional dashboard with proper error handling and content display
"""
import streamlit as st
import asyncio
import pandas as pd
import time
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import logging
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from main import TradingBot
    from config import TradingConfig
except ImportError as e:
    st.error(f"Import Error: {e}")
    st.stop()

# Configure page
st.set_page_config(
    page_title="CryptoSight Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1e88e5;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border: 2px solid #1e88e5;
    }
    .signal-card {
        background-color: #e8f5e8;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #4caf50;
        margin: 0.5rem 0;
    }
    .error-card {
        background-color: #ffebee;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #f44336;
    }
</style>
""", unsafe_allow_html=True)

class DashboardManager:
    def __init__(self):
        self.bot = None
        self.last_scan_time = None
        self.last_signals = []
        self.scan_in_progress = False
        
    def initialize_bot(self):
        """Initialize trading bot with error handling"""
        try:
            if self.bot is None:
                with st.spinner("Initializing trading bot..."):
                    self.bot = TradingBot()
                st.success("✅ Trading bot initialized successfully!")
                return True
        except Exception as e:
            st.error(f"❌ Failed to initialize bot: {e}")
            return False
        return True
    
    def run_market_scan(self):
        """Run market scan with proper error handling"""
        if not self.initialize_bot():
            return None
            
        if self.bot is None:
            st.error("❌ Bot is not initialized. Cannot run market scan.")
            return None
            
        try:
            self.scan_in_progress = True
            
            # Create progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Update progress
            status_text.text("🔍 Fetching top crypto symbols...")
            progress_bar.progress(20)
            time.sleep(0.5)
            
            status_text.text("📊 Downloading market data...")
            progress_bar.progress(40)
            time.sleep(0.5)
            
            status_text.text("🧠 Running strategy analysis...")
            progress_bar.progress(60)
            
            # Run the actual scan
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                results = loop.run_until_complete(self.bot.enhanced_market_scan())
            finally:
                loop.close()
            
            progress_bar.progress(80)
            status_text.text("✅ Processing results...")
            time.sleep(0.5)
            
            progress_bar.progress(100)
            status_text.text("🎯 Scan completed!")
            time.sleep(0.5)
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
            self.last_scan_time = datetime.now()
            self.last_signals = results.get('signals', [])
            self.scan_in_progress = False
            
            return results
            
        except Exception as e:
            self.scan_in_progress = False
            st.error(f"❌ Scan failed: {e}")
            return None
    
    def display_signals(self, signals):
        """Display trading signals in a nice format"""
        if not signals:
            st.info("🤷 No trading signals found in this scan")
            return
        
        st.subheader(f"🎯 Found {len(signals)} Trading Signals")
        
        # Create tabs for different signal types
        buy_signals = [s for s in signals if s.get('signal') == 'BUY']
        sell_signals = [s for s in signals if s.get('signal') == 'SELL']
        
        tab1, tab2, tab3 = st.tabs([
            f"🚀 BUY Signals ({len(buy_signals)})",
            f"📉 SELL Signals ({len(sell_signals)})", 
            f"📊 All Signals ({len(signals)})"
        ])
        
        with tab1:
            self._display_signal_list(buy_signals, "BUY")
            
        with tab2:
            self._display_signal_list(sell_signals, "SELL")
            
        with tab3:
            self._display_signal_table(signals)
    
    def _display_signal_list(self, signals, signal_type):
        """Display signals in expandable cards"""
        if not signals:
            st.info(f"No {signal_type} signals found")
            return
            
        for i, signal in enumerate(signals, 1):
            confidence = signal.get('confidence', 0)
            symbol = signal.get('symbol', 'Unknown')
            
            # Color coding based on confidence
            if confidence >= 80:
                emoji = "🔥"
                confidence_color = "🟢"
            elif confidence >= 70:
                emoji = "⚡"
                confidence_color = "🟡"
            else:
                emoji = "📈" if signal_type == "BUY" else "📉"
                confidence_color = "🟠"
            
            with st.expander(f"{emoji} {signal_type} #{i}: {symbol} - {confidence_color} {confidence:.1f}%"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Entry Price", f"${signal.get('entry_price', 0):.4f}")
                    st.metric("Confidence", f"{confidence:.1f}%")
                
                with col2:
                    st.metric("Stop Loss", f"${signal.get('stop_loss', 0):.4f}")
                    st.metric("Take Profit", f"${signal.get('take_profit', 0):.4f}")
                
                with col3:
                    st.metric("Risk/Reward", f"{signal.get('risk_reward_ratio', 0):.2f}")
                    st.metric("Supporting Strategies", signal.get('supporting_strategies', 0))
                
                # Additional details
                if signal.get('reason'):
                    st.write("**Analysis:**")
                    st.write(signal['reason'])
                
                # Market context
                market_regime = signal.get('market_regime', {})
                if market_regime:
                    st.write("**Market Context:**")
                    st.write(f"Trend: {market_regime.get('trend', 'Unknown')}")
                    st.write(f"Volatility: {market_regime.get('volatility', 'Unknown')}")
    
    def _display_signal_table(self, signals):
        """Display all signals in a table format"""
        if not signals:
            return
            
        # Create DataFrame for table display
        table_data = []
        for signal in signals:
            table_data.append({
                'Symbol': signal.get('symbol', ''),
                'Signal': signal.get('signal', ''),
                'Confidence': f"{signal.get('confidence', 0):.1f}%",
                'Entry': f"${signal.get('entry_price', 0):.4f}",
                'Stop Loss': f"${signal.get('stop_loss', 0):.4f}",
                'Take Profit': f"${signal.get('take_profit', 0):.4f}",
                'R/R': f"{signal.get('risk_reward_ratio', 0):.2f}",
                'Strategies': signal.get('supporting_strategies', 0)
            })
        
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True)
    
    def display_performance_chart(self):
        """Display performance visualization"""
        if not self.last_signals:
            return
            
        # Create confidence distribution chart
        confidences = [s.get('confidence', 0) for s in self.last_signals]
        
        if confidences:
            fig = px.histogram(
                x=confidences,
                nbins=10,
                title="Signal Confidence Distribution",
                labels={'x': 'Confidence %', 'y': 'Number of Signals'}
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

def main():
    """Main dashboard application"""
    
    # Header
    st.markdown('<h1 class="main-header">🎯 CryptoSight Trading Bot Dashboard</h1>', unsafe_allow_html=True)
    
    # Initialize dashboard manager
    if 'dashboard' not in st.session_state:
        st.session_state.dashboard = DashboardManager()
    
    dashboard = st.session_state.dashboard
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Trading settings
        st.subheader("Trading Settings")
        paper_trading = st.checkbox("Paper Trading Mode", value=True)
        max_risk = st.slider("Max Risk per Trade (%)", 1, 10, 2)
        scan_limit = st.slider("Symbols to Scan", 20, 200, 50)
        
        st.subheader("Strategy Settings")
        min_confidence = st.slider("Minimum Confidence (%)", 50, 90, 65)
        min_volume = st.number_input("Min Volume (USD)", value=10000000, step=1000000)
        
        st.divider()
        
        # System status
        st.subheader("📊 System Status")
        config = TradingConfig()
        
        if dashboard.bot:
            st.success("🟢 Bot: Active")
        else:
            st.error("🔴 Bot: Not Initialized")
        
        st.info(f"💰 Account: ${config.ACCOUNT_BALANCE:,.2f}")
        st.info(f"📝 Paper Mode: {'✅' if config.ENABLE_PAPER_TRADING else '❌'}")
        
        if dashboard.last_scan_time:
            time_ago = datetime.now() - dashboard.last_scan_time
            st.info(f"⏰ Last Scan: {time_ago.seconds//60}m ago")
        else:
            st.info("⏰ Last Scan: Never")
    
    # Main content area
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Status", 
            "🟢 Active" if dashboard.bot else "🔴 Inactive",
            help="Trading bot status"
        )
    
    with col2:
        signals_count = len(dashboard.last_signals) if dashboard.last_signals else 0
        st.metric(
            "Signals Found", 
            signals_count,
            help="Number of signals from last scan"
        )
    
    with col3:
        high_conf_signals = len([s for s in dashboard.last_signals if s.get('confidence', 0) >= 75]) if dashboard.last_signals else 0
        st.metric(
            "High Confidence", 
            high_conf_signals,
            help="Signals with >75% confidence"
        )
    
    with col4:
        if dashboard.last_scan_time:
            time_diff = datetime.now() - dashboard.last_scan_time
            last_scan_text = f"{time_diff.seconds//60}m ago"
        else:
            last_scan_text = "Never"
        
        st.metric(
            "Last Scan", 
            last_scan_text,
            help="Time since last market scan"
        )
    
    st.divider()
    
    # Scan controls
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        scan_button = st.button(
            "🔍 Run Market Scan", 
            type="primary", 
            disabled=dashboard.scan_in_progress,
            use_container_width=True
        )
    
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    with col3:
        if st.button("📊 View Config", use_container_width=True):
            st.balloons()
            config.print_config_summary()
    
    # Run scan if button clicked
    if scan_button and not dashboard.scan_in_progress:
        with st.spinner("🔍 Running market scan..."):
            scan_results = dashboard.run_market_scan()
            
            if scan_results:
                st.success(f"✅ Scan completed! Found {len(scan_results.get('signals', []))} signals")
                
                # Display scan stats
                stats = scan_results.get('stats', {})
                if stats:
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Symbols Found", stats.get('symbols_found', 0))
                    with col2:
                        st.metric("Data Downloaded", stats.get('data_downloaded', 0))
                    with col3:
                        st.metric("Signals Generated", stats.get('signals_generated', 0))
                    with col4:
                        st.metric("Scan Duration", f"{scan_results.get('duration', 0):.1f}s")
            else:
                st.error("❌ Scan failed. Please check the logs.")
    
    # Display results
    if dashboard.last_signals:
        st.divider()
        dashboard.display_signals(dashboard.last_signals)
        
        # Performance visualization
        st.divider()
        st.subheader("📈 Analysis")
        dashboard.display_performance_chart()
    
    # Recent activity section
    st.divider()
    st.subheader("📈 Recent Activity")
    
    if dashboard.last_signals:
        if dashboard.last_scan_time:
            st.write(f"**Last scan completed:** {dashboard.last_scan_time.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            st.write("**Last scan completed:** Unknown")
        st.write(f"**Signals found:** {len(dashboard.last_signals)}")
        
        # Quick stats
        buy_signals = len([s for s in dashboard.last_signals if s.get('signal') == 'BUY'])
        sell_signals = len([s for s in dashboard.last_signals if s.get('signal') == 'SELL'])
        avg_confidence = sum(s.get('confidence', 0) for s in dashboard.last_signals) / len(dashboard.last_signals)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("BUY Signals", buy_signals)
        with col2:
            st.metric("SELL Signals", sell_signals)
        with col3:
            st.metric("Avg Confidence", f"{avg_confidence:.1f}%")
    else:
        st.info("No recent activity. Run a market scan to see results.")
    
    # Footer
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        🎯 CryptoSight v3.0 - Professional Trading Bot<br>
        ⚠️ <b>Risk Warning:</b> Trading involves significant risk. Only trade with funds you can afford to lose.
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()