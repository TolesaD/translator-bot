#!/usr/bin/env python3
"""
Test script to verify the setup works
"""
import os
import sys

print("🧪 Testing setup...")
print("Python version:", sys.version)
print("Current directory:", os.getcwd())
print("Files in directory:", os.listdir('.'))

# Test imports
try:
    import telegram
    print("✅ python-telegram-bot imported")
except ImportError as e:
    print("❌ python-telegram-bot import failed:", e)

try:
    from dotenv import load_dotenv
    print("✅ python-dotenv imported")
except ImportError as e:
    print("❌ python-dotenv import failed:", e)

# Test bot import
try:
    sys.path.append('bot')
    from bot.main import main
    print("✅ Bot main imported successfully")
except ImportError as e:
    print("❌ Bot import failed:", e)
    print("Bot directory exists:", os.path.exists('bot'))
    if os.path.exists('bot'):
        print("Files in bot directory:", os.listdir('bot'))