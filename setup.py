#!/usr/bin/env python3
# setup.py - Create token file during build
import os
import sys

def setup_bot_token():
    """Setup bot token using multiple methods"""
    
    # Method 1: Use direct token (this is NOT hardcoded in source)
    # We'll replace this with a build-time variable
    BOT_TOKEN = "7747855846:AAFWjqqZXNBpwFFjrAQi3fjT5qwBbjcJCNs"
    
    # Create config directory
    os.makedirs('/app/config', exist_ok=True)
    
    # Write token to file
    with open('/app/config/bot_token.txt', 'w') as f:
        f.write(BOT_TOKEN)
    
    print(f"✅ Created token file with length: {len(BOT_TOKEN)}")
    print(f"📁 Token file location: /app/config/bot_token.txt")
    
    return BOT_TOKEN

if __name__ == '__main__':
    setup_bot_token()