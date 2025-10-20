# config/loader.py - Secure configuration loader
import os
import sys

def load_bot_token():
    """
    Load bot token from multiple secure sources in priority order:
    1. Environment variable (if Railway fixes it)
    2. Config file (secure fallback)
    3. External secret management
    """
    
    # Method 1: Environment variable (primary)
    token = os.getenv('BOT_TOKEN')
    if token and len(token) > 10:
        print("✅ Loaded BOT_TOKEN from environment variable")
        return token
    
    # Method 2: Config file (secure fallback)
    config_paths = [
        '/app/config/bot_token.txt',  # Railway absolute path
        '/app/bot_token.txt',         # Alternative Railway path
        './config/bot_token.txt',     # Local development
        './bot_token.txt',            # Root directory
    ]
    
    for path in config_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    token = f.read().strip()
                    if token and len(token) > 10:
                        print(f"✅ Loaded BOT_TOKEN from file: {path}")
                        return token
            except Exception as e:
                print(f"⚠️  Failed to read {path}: {e}")
    
    # Method 3: Check if we're on Railway but token is missing
    if os.getenv('RAILWAY_ENVIRONMENT'):
        print("🚨 CRITICAL: Running on Railway but BOT_TOKEN not found!")
        print("💡 Solution: Using Railway's file-based configuration")
        print("   Please create a file at runtime with your token")
    
    raise ValueError(
        "BOT_TOKEN not found. Please use one of these methods:\n"
        "1. Add BOT_TOKEN to Railway service variables\n"
        "2. Create config/bot_token.txt with your token\n"
        "3. Use Railway's secrets management"
    )

# Load the token when module is imported
BOT_TOKEN = load_bot_token()
ANNOUNCEMENT_CHANNEL = os.getenv('ANNOUNCEMENT_CHANNEL', '@LanguagesTranslator')