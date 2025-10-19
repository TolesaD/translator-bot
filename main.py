#!/usr/bin/env python3
"""
Railway entry point
"""
import os
import sys

print("🚀 Railway: Starting Telegram Translator Bot...")
print(f"📁 Working directory: {os.getcwd()}")

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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