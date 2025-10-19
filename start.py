#!/usr/bin/env python3
"""
Start script for Railway deployment
"""
import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from bot.main import main
    print("✅ Bot module imported successfully")
    
    if __name__ == "__main__":
        print("🚀 Starting Telegram Translator Bot on Railway...")
        main()
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure all dependencies are installed and paths are correct")
    sys.exit(1)
except Exception as e:
    print(f"❌ Fatal error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)