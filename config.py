# config.py - Secure configuration without hardcoding
import os
import sys

class Config:
    """Secure configuration management"""
    
    @staticmethod
    def get_bot_token():
        """
        Get bot token from multiple secure sources in order of priority:
        1. Railway Environment Variables (primary)
        2. Railway Secrets (alternative)
        3. External configuration (fallback)
        """
        
        # Primary: Railway Environment Variable
        token = os.getenv('BOT_TOKEN')
        if token:
            print("✅ Loaded BOT_TOKEN from Railway environment variable")
            return token
        
        # Secondary: Check for common alternative names
        alternative_names = ['TELEGRAM_BOT_TOKEN', 'BOT_TOKEN', 'TELEGRAM_TOKEN']
        for name in alternative_names:
            token = os.getenv(name)
            if token:
                print(f"✅ Loaded BOT_TOKEN from alternative name: {name}")
                return token
        
        # Railway-specific: Check if we're on Railway but token is missing
        if os.getenv('RAILWAY_ENVIRONMENT'):
            print("🚨 Running on Railway but BOT_TOKEN not found!")
            print("💡 Railway Setup Instructions:")
            print("   1. Go to your service → Variables")
            print("   2. Add: BOT_TOKEN = your_actual_token")
            print("   3. Make sure it's at SERVICE level, not PROJECT level")
            print("   4. Redeploy your application")
        
        raise ValueError(
            "BOT_TOKEN not found in any environment variables. "
            "Please add it to your Railway service variables."
        )

# Export the token
BOT_TOKEN = Config.get_bot_token()
ANNOUNCEMENT_CHANNEL = os.getenv('ANNOUNCEMENT_CHANNEL', '')