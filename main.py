#!/usr/bin/env python3
"""
Railway entry point - This file should be in your project root
"""
import os
import sys
import logging

# Add the current directory to Python path so we can import from bot/
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
    # Import your existing bot main function
    from bot.main import main as bot_main
    print("✅ Successfully imported bot module")
    
    # Run the bot
    bot_main()
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("📂 Files in current directory:", [f for f in os.listdir('.') if not f.startswith('.')])
    if os.path.exists('bot'):
        print("📂 Files in bot directory:", os.listdir('bot'))
    sys.exit(1)
except Exception as e:
    print(f"❌ Fatal error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)