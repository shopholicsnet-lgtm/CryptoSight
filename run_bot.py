#!/usr/bin/env python3
"""
🚀 CryptoSight v3.0 Startup Script
Quick launcher with dependency checking and configuration validation
"""

import sys
import os
import subprocess
import importlib.util

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version}")
    return True

def check_dependencies():
    """Check if all required packages are installed"""
    required_packages = [
        'pandas', 'numpy', 'streamlit', 'plotly', 'ccxt', 
        'talib', 'requests', 'python-dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'python-dotenv':
                import dotenv
            else:
                importlib.import_module(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📦 Installing missing packages...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install"
            ] + missing_packages)
            print("✅ All packages installed successfully!")
        except subprocess.CalledProcessError:
            print("❌ Failed to install packages automatically")
            print("Please run: pip install -r requirements.txt")
            return False
    
    return True

def check_talib():
    """Special check for TA-Lib since it's tricky to install"""
    try:
        import talib
        print("✅ TA-Lib is working correctly")
        return True
    except ImportError:
        print("❌ TA-Lib not found or not working")
        print("\n📋 TA-Lib Installation Guide:")
        print("Windows: pip install TA-Lib (may need Visual Studio Build Tools)")
        print("Linux: sudo apt-get install build-essential && pip install TA-Lib") 
        print("Mac: brew install ta-lib && pip install TA-Lib")
        print("\nAlternative: Use 'ta' library instead")
        return False

def create_env_file():
    """Create .env file if it doesn't exist"""
    if not os.path.exists('.env'):
        print("📝 Creating .env file...")
        env_content = """# CryptoSight v3.0 Configuration
# Fill in your actual values

# Binance API (Optional for paper trading)
BINANCE_API_KEY=
BINANCE_API_SECRET=

# Discord Notifications (Optional)
DISCORD_WEBHOOK_URL=

# Trading Settings
ACCOUNT_BALANCE=10000.0
MAX_RISK_PER_TRADE=2.0
PAPER_TRADING=True

# Database
DATABASE_PATH=trading_bot.db
"""
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ Created .env file - please edit it with your settings")
    else:
        print("✅ .env file exists")

def validate_config():
    """Validate configuration"""
    try:
        from config import config
        config.print_config_summary()
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def run_streamlit():
    """Launch the Streamlit application"""
    try:
        print("\n🚀 Starting CryptoSight v3.0...")
        print("📱 Opening web interface at http://localhost:8501")
        print("\n💡 Tips:")
        print("- Start with paper trading enabled")
        print("- Configure Discord webhook for alerts")
        print("- Begin with 50-100 symbol scans")
        print("- Monitor performance metrics regularly")
        print("\n⚠️  Risk Warning:")
        print("- Cryptocurrency trading involves significant risk")
        print("- Only trade with funds you can afford to lose")
        print("- Always use proper risk management")
        print("- Past performance doesn't guarantee future results")
        
        # Launch Streamlit
        subprocess.run([
        sys.executable, "-m", "streamlit", "run", 
        "dashboard.py", "--theme.base=dark"
    ])
        
    except KeyboardInterrupt:
        print("\n👋 CryptoSight stopped by user")
    except Exception as e:
        print(f"❌ Failed to start application: {e}")

def main():
    """Main startup sequence"""
    print("=" * 60)
    print("🎯 CryptoSight v3.0 - Professional Trading Bot")
    print("=" * 60)
    
    # System checks
    if not check_python_version():
        return
    
    print("\n📦 Checking dependencies...")
    if not check_dependencies():
        return
    
    print("\n🔧 Checking TA-Lib...")
    if not check_talib():
        choice = input("\nContinue without TA-Lib? (y/n): ").lower()
        if choice != 'y':
            return
    
    print("\n⚙️ Setting up configuration...")
    create_env_file()
    
    if not validate_config():
        return
    
    print("\n" + "=" * 60)
    print("✅ All systems ready!")
    print("=" * 60)
    
    # Launch application
    run_streamlit()

if __name__ == "__main__":
    main()