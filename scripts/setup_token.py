#!/usr/bin/env python3
# scripts/setup_token.py - Create token file for Railway
import os
import sys

def create_token_file():
    """Create token file from environment variable or user input"""
    token = os.getenv('BOT_TOKEN')
    
    if not token:
        print("❌ BOT_TOKEN environment variable not set")
        print("💡 Please set BOT_TOKEN environment variable first")
        return False
    
    # Create config directory if it doesn't exist
    os.makedirs('/app/config', exist_ok=True)
    
    # Write token to file
    with open('/app/config/bot_token.txt', 'w') as f:
        f.write(token.strip())
    
    print("✅ Created /app/config/bot_token.txt")
    print(f"   Token length: {len(token)}")
    return True

if __name__ == '__main__':
    create_token_file()