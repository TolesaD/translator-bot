import os
import logging
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logger
logger = logging.getLogger(__name__)

def get_bot_token():
    """Get bot token with Railway-specific debugging"""
    print("🔍 Checking Railway Environment...")
    
    # Check if we're running on Railway
    is_railway = os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('RAILWAY_PROJECT_ID')
    print(f"   Running on Railway: {is_railway}")
    
    # Check for BOT_TOKEN in environment
    bot_token = os.getenv('BOT_TOKEN')
    
    if bot_token:
        print(f"✅ BOT_TOKEN found (length: {len(bot_token)})")
        print(f"   Token preview: {bot_token[:10]}...{bot_token[-5:]}")
        return bot_token
    
    # If no token found, show detailed debug info
    print("❌ BOT_TOKEN not found in environment variables")
    print("📋 All available environment variables:")
    
    env_vars = dict(os.environ)
    for key, value in sorted(env_vars.items()):
        if any(secret in key.lower() for secret in ['token', 'key', 'secret', 'password']):
            print(f"   {key}: [HIDDEN - length: {len(value)}]")
        else:
            print(f"   {key}: {value}")
    
    # Railway-specific help
    if is_railway:
        print("\n🚨 RAILWAY SETUP INSTRUCTIONS:")
        print("1. Go to your Railway project dashboard")
        print("2. Click on your SERVICE (not the project)")
        print("3. Go to 'Variables' tab")
        print("4. Add: BOT_TOKEN = your_actual_bot_token")
        print("5. Make sure it's added to the SERVICE, not the project")
        print("6. Redeploy your application")
    else:
        print("\n💻 LOCAL SETUP:")
        print("Set environment variable: $env:BOT_TOKEN='your_token' (PowerShell)")
        print("Or: set BOT_TOKEN=your_token (Command Prompt)")
    
    raise ValueError("BOT_TOKEN environment variable is required")

def setup_bot():
    """Setup and return the bot application"""
    print("🤖 Setting up Telegram Translator Bot...")
    
    # Get bot token
    bot_token = get_bot_token()
    
    from telegram.ext import Application
    
    # Create application
    application = Application.builder().token(bot_token).build()
    
    # Store announcement channel
    announcement_channel = os.getenv('ANNOUNCEMENT_CHANNEL')
    if announcement_channel:
        application.bot_data['announcement_channel'] = announcement_channel
        print(f"✅ Announcement channel set: {announcement_channel}")
    
    return application

def setup_handlers(application):
    """Setup all bot handlers"""
    print("🔄 Setting up handlers...")
    
    # Import handlers
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

def main():
    """Main function to start the bot"""
    print("🚀 Starting Telegram Translator Bot...")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"🐍 Python version: {sys.version}")
    
    try:
        # Setup bot application
        application = setup_bot()
        
        # Setup handlers
        setup_handlers(application)
        
        print("✅ Bot setup complete. Starting polling...")
        
        # Start the bot
        application.run_polling()
        
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == '__main__':
    main()