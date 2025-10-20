#!/usr/bin/env python3
"""
Railway entry point - Simple and reliable
"""
import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

print("=" * 50)
print("🚀 Starting Telegram Bot on Railway")
print("=" * 50)

def get_bot_token():
    """Get bot token from file with fallbacks"""
    
    # Check for token file first
    token_paths = [
        '/app/config/bot_token.txt',
        './config/bot_token.txt', 
        './bot_token.txt'
    ]
    
    for path in token_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    token = f.read().strip()
                    if token and len(token) > 10:
                        print(f"✅ Loaded token from: {path}")
                        print(f"   Token length: {len(token)}")
                        return token
            except Exception as e:
                print(f"⚠️  Failed to read {path}: {e}")
    
    # If no token file, try environment variable
    token = os.getenv('BOT_TOKEN')
    if token:
        print("✅ Loaded token from environment variable")
        return token
    
    # Last resort: Direct token (this will be replaced during build)
    # This is TEMPORARY and will be removed once the build script works
    emergency_token = "7747855846:AAFWjqqZXNBpwFFjrAQi3fjT5qwBbjcJCNs"
    print("🚨 USING EMERGENCY TOKEN - SETUP FILE-BASED CONFIG")
    return emergency_token

try:
    # Get the bot token
    BOT_TOKEN = get_bot_token()
    
    if not BOT_TOKEN or len(BOT_TOKEN) < 10:
        raise ValueError("Invalid bot token")
    
    # Set as environment variable for the bot
    os.environ['BOT_TOKEN'] = BOT_TOKEN
    
    print("✅ Token validation successful")
    print("🤖 Starting bot...")
    
    # Add current directory to Python path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Import and run bot
    from bot.main import main as bot_main
    bot_main()
    
except Exception as e:
    print(f"❌ Fatal error: {e}")
    print("\n🔧 QUICK FIX: Add this build command in Railway:")
    print('   mkdir -p /app/config && echo "7747855846:AAFWjqqZXNBpwFFjrAQi3fjT5qwBbjcJCNs" > /app/config/bot_token.txt')
    sys.exit(1)