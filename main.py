#!/usr/bin/env python3
"""
Railway entry point
"""
import os
import sys
import logging

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

print("🚀 Railway: Starting Telegram Translator Bot...")
print(f"📁 Working directory: {os.getcwd()}")
print(f"🐍 Python path: {sys.path}")

try:
    from bot.main import main as bot_main
    print("✅ Successfully imported bot module")
    
    # Run the bot
    bot_main()
    
except Exception as e:
    print(f"❌ Fatal error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)