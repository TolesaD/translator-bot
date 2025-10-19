import os
import logging
import sys
from dotenv import load_dotenv

# Load environment variables from .env file (for local development)
load_dotenv()

# Configure logger
logger = logging.getLogger(__name__)

def get_bot_token():
    """Get bot token from environment with better error handling"""
    # Try multiple possible environment variable names
    bot_token = os.getenv('BOT_TOKEN') or os.getenv('TELEGRAM_BOT_TOKEN') or os.getenv('BOT_TOKEN')
    
    if not bot_token:
        # Print all available environment variables for debugging (without sensitive data)
        print("🔍 Available environment variables:")
        for key in sorted(os.environ.keys()):
            if any(secret in key.lower() for secret in ['token', 'key', 'secret', 'password']):
                print(f"   {key}: [REDACTED]")
            else:
                print(f"   {key}: {os.environ[key]}")
        
        raise ValueError("❌ BOT_TOKEN not found in environment variables. Please check your Railway environment variables.")
    
    return bot_token

def setup_bot():
    """Setup and return the bot application"""
    print("🤖 Setting up Telegram Translator Bot...")
    
    # Get bot token with better error handling
    bot_token = get_bot_token()
    print("✅ Bot token found")
    
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

def main():
    """Main function to start the bot"""
    print("🚀 Starting Telegram Translator Bot...")
    print(f"📁 Current directory: {os.getcwd()}")
    print(f"🐍 Python path: {sys.path}")
    
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