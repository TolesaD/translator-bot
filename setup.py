#!/usr/bin/env python3
import os
import sys

def setup_environment():
    """Interactive setup script for environment variables"""
    print("🤖 Telegram Translator Bot Setup")
    print("=" * 40)
    
    env_vars = {}
    
    # Get bot token
    bot_token = input("Enter your Telegram Bot Token: ").strip()
    if not bot_token:
        print("❌ Bot token is required!")
        sys.exit(1)
    env_vars['BOT_TOKEN'] = bot_token
    
    # Get MongoDB URI
    mongodb_uri = input("Enter your MongoDB Atlas connection URI: ").strip()
    if not mongodb_uri:
        print("❌ MongoDB URI is required!")
        sys.exit(1)
    env_vars['MONGODB_URI'] = mongodb_uri
    
    # Optional variables
    default_lang = input("Enter default language code (en): ").strip() or "en"
    env_vars['DEFAULT_LANGUAGE'] = default_lang
    
    max_history = input("Enter max history entries (10): ").strip() or "10"
    env_vars['MAX_HISTORY'] = max_history
    
    # Write .env file
    with open('.env', 'w') as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")
    
    print("✅ Environment file created successfully!")
    print("📁 You can now run: python -m bot.main")

if __name__ == '__main__':
    setup_environment()