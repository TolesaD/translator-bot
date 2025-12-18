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

    @staticmethod
    def get_admin_ids():
        """Get admin user IDs from environment variable"""
        admin_ids_str = os.getenv('ADMIN_IDS', '')
        if admin_ids_str:
            try:
                # Parse comma-separated list of user IDs
                admin_ids = [int(id.strip()) for id in admin_ids_str.split(',') if id.strip()]
                return admin_ids
            except ValueError:
                print(f"⚠️  Invalid ADMIN_IDS format: {admin_ids_str}")
                return []
        return []

    @staticmethod
    def get_required_channels():
        """Get list of required channels users must join"""
        channels_str = os.getenv('REQUIRED_CHANNELS', '')
        if channels_str:
            # Parse comma-separated list of channel usernames
            channels = [channel.strip() for channel in channels_str.split(',') if channel.strip()]
            # Ensure @ prefix
            channels = [f"@{channel}" if not channel.startswith('@') else channel for channel in channels]
            return channels
        return []

    @staticmethod
    def get_announcement_channel():
        """Get announcement channel for broadcast messages"""
        channel = os.getenv('ANNOUNCEMENT_CHANNEL', '')
        if channel and not channel.startswith('@'):
            channel = f"@{channel}"
        return channel

# Export configurations
BOT_TOKEN = Config.get_bot_token()
ADMIN_IDS = Config.get_admin_ids()
REQUIRED_CHANNELS = Config.get_required_channels()
ANNOUNCEMENT_CHANNEL = Config.get_announcement_channel()
BROADCAST_CHANNEL = ANNOUNCEMENT_CHANNEL  # Alias for backward compatibility

# Print configuration for debugging
print(f"📊 Config loaded:")
print(f"   - BOT_TOKEN length: {len(BOT_TOKEN) if BOT_TOKEN else 'NOT FOUND'}")
print(f"   - ADMIN_IDS: {ADMIN_IDS}")
print(f"   - REQUIRED_CHANNELS: {REQUIRED_CHANNELS}")
print(f"   - ANNOUNCEMENT_CHANNEL: {ANNOUNCEMENT_CHANNEL}")