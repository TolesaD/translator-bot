import os
import logging
import sys
from dotenv import load_dotenv

# Configure logger
logger = logging.getLogger(__name__)

def setup_bot():
    """Setup and return the bot application with proper configuration"""
    print("🤖 Setting up Telegram Translator Bot...")
    
    # Load environment variables from .env file (for local development)
    # This will be ignored on Railway where vars are set directly in environment
    load_dotenv()
    
    # Get bot token
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        raise ValueError("❌ BOT_TOKEN not found in environment variables")
    
    print("✅ Bot token found")
    
    from telegram.ext import Application
    
    # Create application
    application = Application.builder().token(bot_token).build()
    
    # DEBUG: Check all environment variables
    print("🔍 Environment Variables Check:")
    print(f"   ANNOUNCEMENT_CHANNEL: {os.getenv('ANNOUNCEMENT_CHANNEL')}")
    print(f"   BOT_TOKEN length: {len(bot_token) if bot_token else 'NOT FOUND'}")
    
    # Store announcement channel in bot_data for access in handlers
    announcement_channel = os.getenv('ANNOUNCEMENT_CHANNEL')
    if announcement_channel:
        # Ensure consistent format - always with @
        if not announcement_channel.startswith('@'):
            announcement_channel = f"@{announcement_channel}"
        
        application.bot_data['announcement_channel'] = announcement_channel
        print(f"✅ Announcement channel set in bot_data: {announcement_channel}")
        
        # DEBUG: Verify it's actually in bot_data
        stored_channel = application.bot_data.get('announcement_channel')
        print(f"✅ Confirmed in bot_data: {stored_channel}")
    else:
        print("⚠️  No announcement channel set - membership checks will be skipped")
    
    return application

def setup_handlers(application):
    """Setup all bot handlers"""
    print("🔄 Setting up handlers...")
    
    try:
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
        
    except ImportError as e:
        print(f"❌ Handler import error: {e}")
        raise

def main():
    """Main function to start the bot"""
    print("🚀 Starting Telegram Translator Bot...")
    print(f"📁 Working directory: {os.getcwd()}")
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