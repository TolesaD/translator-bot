import os
import sys

def load_bot_token():
    """Load bot token with multiple fallback methods"""
    # Method 1: Environment variable
    token = os.getenv('BOT_TOKEN')
    if token:
        return token
    
    # Method 2: Check common Railway paths
    possible_paths = [
        '/etc/railway/secrets/BOT_TOKEN',
        '/run/secrets/BOT_TOKEN',
        '/app/BOT_TOKEN',
        './BOT_TOKEN'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    token = f.read().strip()
                    if token:
                        print(f"✅ Loaded BOT_TOKEN from file: {path}")
                        return token
            except Exception as e:
                print(f"⚠️  Failed to read {path}: {e}")
    
    # Method 3: Check if we're in a Railway-like environment
    if os.getenv('RAILWAY_PROJECT_ID'):
        print("🚨 Running on Railway but BOT_TOKEN not found!")
        print("💡 Please add BOT_TOKEN to your Railway service variables")
    
    raise ValueError("BOT_TOKEN not found in any location")

BOT_TOKEN = load_bot_token()