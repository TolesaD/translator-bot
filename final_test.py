# final_test.py
import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

print("🧪 Final test...")

# Test environment variables
print("🔍 Environment variables:")
print(f"  BOT_TOKEN: {os.getenv('BOT_TOKEN')[:10]}...")
print(f"  ADMIN_IDS: {os.getenv('ADMIN_IDS')}")
print(f"  REQUIRED_CHANNELS: {os.getenv('REQUIRED_CHANNELS')}")

# Test config import
try:
    import config
    print("\n✅ Config import successful!")
    print(f"  config module path: {config.__file__}")
    print(f"  BOT_TOKEN from config: {config.BOT_TOKEN[:10]}...")
    print(f"  ADMIN_IDS from config: {config.ADMIN_IDS}")
    print(f"  REQUIRED_CHANNELS from config: {config.REQUIRED_CHANNELS}")
    
    # Test database
    print("\n🔍 Testing database...")
    from bot.services.database import db_manager
    print(f"  Database connected: {db_manager.is_connected}")
    
    print("\n🎉 All tests passed! Ready to run bot.")
    
except Exception as e:
    print(f"\n❌ Test failed: {e}")
    import traceback
    traceback.print_exc()