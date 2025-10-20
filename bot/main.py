import os
import logging
import sys
from dotenv import load_dotenv

# Load environment variables from .env file (for local development)
load_dotenv()

# Configure logger
logger = logging.getLogger(__name__)

def get_bot_token():
    """Safely get bot token from environment with proper validation"""
    # Try multiple possible environment variable names
    bot_token = (
        os.getenv('BOT_TOKEN') or 
        os.getenv('TELEGRAM_BOT_TOKEN') or 
        os.getenv('BOT_TOKEN')
    )
    
    if not bot_token:
        # Don't print all environment variables in production
        # Just give clear instructions
        error_msg = """
❌ BOT_TOKEN not found in environment variables.

Railway Setup Instructions:
1. Go to your Railway project dashboard
2. Click on your SERVICE (not the project)
3. Go to 'Variables' tab  
4. Add: BOT_TOKEN = your_actual_bot_token
5. Make sure it's added to the SERVICE, not the project
6. Redeploy your application

Local Development:
- Create a .env file with: BOT_TOKEN=your_token
- Or set environment variable: export BOT_TOKEN=your_token
"""
        raise ValueError(error_msg)
    
    # Basic validation
    if ':' not in bot_token:
        raise ValueError(f"Invalid BOT_TOKEN format. Should be '123456:ABC-DEF1234' format. Got: {bot_token[:20]}...")
    
    if len(bot_token) < 10:
        raise ValueError(f"BOT_TOKEN seems too short: {len(bot_token)} characters")
    
    print(f"✅ Valid BOT_TOKEN loaded (length: {len(bot_token)})")
    return bot_token

def setup_bot():
    """Setup and return the bot application"""
    print("🤖 Setting up Telegram Translator Bot...")
    
    # Get bot token with validation
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
        # Don't print full traceback in production
        if os.getenv('RAILWAY_ENVIRONMENT'):
            print("💡 Check Railway service variables configuration")
        raise

if __name__ == '__main__':
    main()