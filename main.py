#!/usr/bin/env python3
"""
Railway entry point - Secure version
"""
import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

print("🚀 Starting Telegram Bot on Railway...")
print(f"📁 Working directory: {os.getcwd()}")

try:
    # Import configuration FIRST
    from config import BOT_TOKEN, ANNOUNCEMENT_CHANNEL
    
    print(f"✅ Configuration loaded successfully")
    print(f"   BOT_TOKEN length: {len(BOT_TOKEN)}")
    print(f"   ANNOUNCEMENT_CHANNEL: {ANNOUNCEMENT_CHANNEL}")
    
    # Add current directory to Python path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Import and run bot
    from bot.main import main as bot_main
    bot_main()
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except ValueError as e:
    print(f"❌ Configuration error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Fatal error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)