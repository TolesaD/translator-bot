# test_start.py
import os
import sys
from telegram.ext import Application

print("🤖 Testing bot startup...")

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

try:
    from bot_config import BOT_TOKEN, ADMIN_IDS, REQUIRED_CHANNELS
    print(f"✅ Config loaded")
    print(f"   BOT_TOKEN: {'*' * len(BOT_TOKEN)}")
    print(f"   ADMIN_IDS: {ADMIN_IDS}")
    print(f"   REQUIRED_CHANNELS: {REQUIRED_CHANNELS}")
except Exception as e:
    print(f"❌ Config error: {e}")
    sys.exit(1)

try:
    # Create minimal application
    application = Application.builder().token(BOT_TOKEN).build()
    print("✅ Application created")
    
    # Add a simple start command
    from telegram.ext import CommandHandler
    
    async def start(update, context):
        await update.message.reply_text("✅ Bot is working!")
    
    application.add_handler(CommandHandler("start", start))
    
    print("✅ Handlers added")
    print("✅ Bot setup successful!")
    
except Exception as e:
    print(f"❌ Bot setup failed: {e}")
    import traceback
    traceback.print_exc()