#!/usr/bin/env python3
"""
Railway entry point - File-based configuration
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
    # Try to create token file from environment variable (if it exists)
    token_from_env = os.getenv('BOT_TOKEN')
    if token_from_env:
        print("🔧 Setting up token file from environment...")
        os.makedirs('/app/config', exist_ok=True)
        with open('/app/config/bot_token.txt', 'w') as f:
            f.write(token_from_env.strip())
        print("✅ Token file created from environment variable")
    
    # Import configuration
    from config.loader import BOT_TOKEN, ANNOUNCEMENT_CHANNEL
    
    print(f"✅ Configuration loaded successfully")
    print(f"   BOT_TOKEN: [HIDDEN - length: {len(BOT_TOKEN)}]")
    print(f"   ANNOUNCEMENT_CHANNEL: {ANNOUNCEMENT_CHANNEL}")
    
    # Add current directory to Python path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Import and run bot
    from bot.main import main as bot_main
    bot_main()
    
except Exception as e:
    print(f"❌ Fatal error: {e}")
    
    # Provide detailed help
    print("\n🔧 SETUP INSTRUCTIONS:")
    print("Since Railway environment variables aren't working, use file-based config:")
    print("")
    print("METHOD 1: Create config file manually")
    print("   1. Create directory: /app/config")
    print("   2. Create file: /app/config/bot_token.txt")
    print("   3. Add your token: 7747855846:AAFWjqqZXNBpwFFjrAQi3fjT5qwBbjcJCNs")
    print("")
    print("METHOD 2: Use build command in Railway")
    print("   Add this build command in Railway:")
    print('   echo "7747855846:AAFWjqqZXNBpwFFjrAQi3fjT5qwBbjcJCNs" > /app/config/bot_token.txt')
    print("")
    print("METHOD 3: Use startup script")
    print("   Create start.sh with:")
    print('   echo "$BOT_TOKEN" > /app/config/bot_token.txt')
    print('   python main.py')
    
    sys.exit(1)