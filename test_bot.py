#!/usr/bin/env python3
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

try:
    from bot.main import main
    print("✅ Bot module imported successfully!")
    print("🚀 Starting bot...")
    main()
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("📁 Current directory:", os.getcwd())
    print("📁 Contents:", os.listdir('.'))
    if os.path.exists('bot'):
        print("📁 Bot directory contents:", os.listdir('bot'))