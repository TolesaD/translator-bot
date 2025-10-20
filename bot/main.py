import os
import logging
from telegram.ext import Application

# Import from our secure config
from config import BOT_TOKEN, ANNOUNCEMENT_CHANNEL

# Configure logger
logger = logging.getLogger(__name__)

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
    
    try:
        # Create application using token from config
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Store announcement channel
        if ANNOUNCEMENT_CHANNEL:
            application.bot_data['announcement_channel'] = ANNOUNCEMENT_CHANNEL
            print(f"✅ Announcement channel set: {ANNOUNCEMENT_CHANNEL}")
        
        # Setup handlers
        setup_handlers(application)
        
        print("✅ Bot setup complete. Starting polling...")
        
        # Start the bot
        application.run_polling()
        
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        raise

if __name__ == '__main__':
    main()