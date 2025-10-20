#!/usr/bin/env python3
"""
Railway entry point - Debug environment variables
"""
import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

print("=" * 60)
print("🚀 Railway Environment Debug")
print("=" * 60)

# Debug: Show ALL environment variables
print("🔍 ALL ENVIRONMENT VARIABLES:")
for key, value in sorted(os.environ.items()):
    if any(secret_word in key.lower() for secret_word in ['token', 'key', 'secret', 'password']):
        print(f"   {key}: [HIDDEN - length: {len(value)}]")
    else:
        print(f"   {key}: {value}")

print("=" * 60)

# Check specifically for BOT_TOKEN
bot_token = os.getenv('BOT_TOKEN')
if bot_token:
    print(f"✅ BOT_TOKEN FOUND! Length: {len(bot_token)}")
    print(f"   First 10 chars: {bot_token[:10]}...")
else:
    print("❌ BOT_TOKEN NOT FOUND IN ENVIRONMENT!")
    print("💡 Please check your Railway service variables:")

print("=" * 60)

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from bot.main import main as bot_main
    print("✅ Successfully imported bot module")
    
    # Run the bot only if token exists
    if bot_token:
        bot_main()
    else:
        print("❌ Cannot start bot without BOT_TOKEN")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Fatal error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)