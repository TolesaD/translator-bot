import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    print("🤖 Starting Telegram Translator Bot...")
    
    # Get bot token
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        print("❌ BOT_TOKEN not found in .env file")
        return
    
    print("✅ Bot token found")
    
    try:
        from telegram.ext import Application
        print("✅ Application imported successfully")
        
        # Import handlers
        from bot.handlers.text_handler import setup_handlers as setup_text_handlers
        from bot.handlers.voice_handler import setup_handlers as setup_voice_handlers
        from bot.handlers.document_handler import setup_handlers as setup_document_handlers
        from bot.handlers.inline_handler import setup_handlers as setup_inline_handlers
        print("✅ All handlers imported successfully")
        
        # Create application
        application = Application.builder().token(bot_token).build()
        
        # Store announcement channel in bot_data for access in handlers
        announcement_channel = os.getenv('ANNOUNCEMENT_CHANNEL')
        if announcement_channel:
            application.bot_data['announcement_channel'] = announcement_channel
            print(f"✅ Announcement channel set: {announcement_channel}")
        else:
            print("⚠️  No announcement channel set")
        
        # Setup handlers
        setup_text_handlers(application)
        setup_voice_handlers(application)
        setup_document_handlers(application)
        setup_inline_handlers(application)
        
        print("✅ Bot setup complete. Starting polling...")
        
        # Start the bot
        application.run_polling()
        print("🎉 Bot is now running! Press Ctrl+C to stop.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()