import os
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Configure logger
logger = logging.getLogger(__name__)

async def start(update, context):
    """Send a message when the command /start is issued."""
    await update.message.reply_text('🤖 Hello! I am your Telegram Translator Bot!')

async def help_command(update, context):
    """Send a message when the command /help is issued."""
    await update.message.reply_text('Help command - I can translate text, voice, and documents!')

async def echo(update, context):
    """Echo the user message."""
    await update.message.reply_text(f'You said: {update.message.text}')

def setup_handlers(application):
    """Setup all bot handlers"""
    print("🔄 Setting up handlers...")
    
    # Add basic handlers first
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    # Try to import additional handlers if they exist
    try:
        from bot.handlers.text_handler import setup_handlers as setup_text_handlers
        setup_text_handlers(application)
        print("✅ Text handlers loaded")
    except ImportError as e:
        print(f"⚠️  Text handlers not available: {e}")
    
    try:
        from bot.handlers.voice_handler import setup_handlers as setup_voice_handlers
        setup_voice_handlers(application)
        print("✅ Voice handlers loaded")
    except ImportError as e:
        print(f"⚠️  Voice handlers not available: {e}")
    
    print("✅ All handlers setup complete")

def main():
    """Main function to start the bot"""
    print("🚀 Starting Telegram Translator Bot...")
    
    try:
        # Get bot token from environment
        bot_token = os.getenv('BOT_TOKEN')
        if not bot_token:
            raise ValueError("BOT_TOKEN not found in environment")
        
        print(f"✅ Using bot token (length: {len(bot_token)})")
        
        # Create application
        application = Application.builder().token(bot_token).build()
        
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