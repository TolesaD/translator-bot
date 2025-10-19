import os
import logging
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logger
logger = logging.getLogger(__name__)

def setup_bot():
    """Setup and return the bot application"""
    print("🤖 Setting up Telegram Translator Bot...")
    
    # Get bot token
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        raise ValueError("❌ BOT_TOKEN not found in environment variables")
    
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
    
    # Use relative imports with dot notation for package-relative imports
    from .handlers.text_handler import setup_handlers as setup_text_handlers
    from .handlers.voice_handler import setup_handlers as setup_voice_handlers
    from .handlers.document_handler import setup_handlers as setup_document_handlers
    from .handlers.inline_handler import setup_handlers as setup_inline_handlers
    
    # Setup handlers
    setup_text_handlers(application)
    setup_voice_handlers(application)
    setup_document_handlers(application)
    setup_inline_handlers(application)
    
    print("✅ All handlers setup complete")

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

# This allows the file to be imported without running the bot
if __name__ == '__main__':
    main()