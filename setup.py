#!/usr/bin/env python3
"""
Main entry point for Railway deployment
"""
import os
import sys
import logging

# Add the bot directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    print("🚀 Starting Telegram Translator Bot on Railway...")
    
    try:
        # Import and run the actual bot
        from bot.main import main as bot_main
        bot_main()
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Current Python path:", sys.path)
        print("Current directory:", os.getcwd())
        print("Files in current directory:", os.listdir('.'))
        if os.path.exists('bot'):
            print("Files in bot directory:", os.listdir('bot'))
        raise

if __name__ == '__main__':
    main()