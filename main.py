import os
import logging
import sys
from dotenv import load_dotenv

# Load environment variables from .env file (for local development)
load_dotenv()

# Configure logger
logger = logging.getLogger(__name__)

def debug_environment():
    """Debug function to check environment variables"""
    print("🔍 Debugging Environment Variables:")
    print(f"   Current directory: {os.getcwd()}")
    print(f"   Python path: {sys.path}")
    
    # Check for BOT_TOKEN in different possible names
    possible_names = ['BOT_TOKEN', 'TELEGRAM_BOT_TOKEN', 'BOT_TOKEN', 'TOKEN']
    bot_token = None
    
    for name in possible_names:
        value = os.getenv(name)
        if value:
            print(f"   ✅ Found {name}: {value[:10]}... (length: {len(value)})")
            bot_token = value
            break
        else:
            print(f"   ❌ {name}: Not found")
    
    # List all environment variables (without sensitive values)
    print("   📋 All environment variables:")
    for key in sorted(os.environ.keys()):
        if any(secret in key.lower() for secret in ['token', 'key', 'secret', 'password', 'auth']):
            if os.environ[key]:
                print(f"      {key}: [HIDDEN - length: {len(os.environ[key])}]")
            else:
                print(f"      {key}: [EMPTY]")
        else:
            print(f"      {key}: {os.environ[key]}")
    
    return bot_token

def get_bot_token():
    """Get bot token from environment with comprehensive checking"""
    bot_token = debug_environment()
    
    if not bot_token:
        raise ValueError(
            "❌ BOT_TOKEN not found in environment variables.\n"
            "Please check your Railway project settings:\n"
            "1. Go to your Railway project dashboard\n"
            "2. Click on 'Variables' tab\n"
            "3. Add: BOT_TOKEN=your_actual_bot_token\n"
            "4. Redeploy your application"
        )
    
    # Validate token format (basic check)
    if ':' not in bot_token:
        raise ValueError(f"❌ Invalid BOT_TOKEN format. Token should contain a colon ':'. Got: {bot_token[:20]}...")
    
    print(f"✅ Valid BOT_TOKEN found (length: {len(bot_token)})")
    return bot_token

def setup_bot():
    """Setup and return the bot application"""
    print("🤖 Setting up Telegram Translator Bot...")
    
    # Get bot token with comprehensive checking
    bot_token = get_bot_token()
    
    from telegram.ext import Application
    
    # Create application
    application = Application.builder().token(bot_token).build()
    
    # Store announcement channel in bot_data for access in handlers
    announcement_channel = os.getenv('ANNOUNCEMENT_CHANNEL')
    if announcement_channel:
        application.bot_data['announcement_channel'] = announcement_channel
        print(f"✅ Announcement channel set: {announcement_channel}")
    else:
        print("⚠️  No announcement channel set")
    
    return application

def setup_handlers(application):
    """Setup all bot handlers"""
    print("🔄 Setting up handlers...")
    
    try:
        # Import handlers using absolute imports
        from bot.handlers.text_handler import setup_handlers as setup_text_handlers
        from bot.handlers.voice_handler import setup_handlers as setup_voice_handlers
        from bot.handlers.document_handler import setup_handlers as setup_document_handlers
        from bot.handlers.inline_handler import setup_handlers as setup_inline_handlers
        
        # Setup handlers
        setup_text_handlers(application)
        setup_voice_handlers(application)
        setup_document_handlers(application)
        setup_inline_handlers(application)
        
        print("✅ All handlers setup complete")
        
    except ImportError as e:
        print(f"❌ Handler import error: {e}")
        print("📂 Available files in bot directory:")
        if os.path.exists('handlers'):
            print(f"   handlers: {os.listdir('handlers')}")
        raise

def main():
    """Main function to start the bot"""
    print("🚀 Starting Telegram Translator Bot...")
    
    try:
        # Setup bot application
        application = setup_bot()
        
        # Setup handlers
        setup_handlers(application)
        
        print("✅ Bot setup complete. Starting polling...")
        
        # Start the bot
        application.run_polling()
        print("🎉 Bot is now running! Press Ctrl+C to stop.")
        
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == '__main__':
    main()