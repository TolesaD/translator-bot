from telegram import Update
from telegram.ext import MessageHandler, CallbackContext, filters
import logging
import tempfile
import os
from bot.services.speech import speech_service
from bot.services.translation import translation_service
from bot.services.database import db_manager
from bot.utils.helpers import format_translation_result

logger = logging.getLogger(__name__)

async def handle_voice_message(update: Update, context: CallbackContext):
    """Handle voice messages for transcription and translation"""
    user_id = update.effective_user.id
    voice = update.message.voice
    
    # Check if speech recognition is available
    if not speech_service.is_speech_available():
        await update.message.reply_text(
            "🎤 Voice message translation is currently unavailable. "
            "Speech recognition package is not installed or has issues. "
            "Please use text messages for translation."
        )
        return
    
    # Get user's default language
    user_prefs = db_manager.get_user_preferences(user_id)
    target_lang = user_prefs.get('default_language', 'en')
    
    if not target_lang:
        await update.message.reply_text("Please set your default language first using /setlang command.")
        return
    
    try:
        # Send processing message
        processing_msg = await update.message.reply_text("🎤 Processing voice message...")
        
        # Download voice file
        voice_file = await voice.get_file()
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as temp_file:
            await voice_file.download_to_drive(temp_file.name)
            temp_path = temp_file.name
        
        try:
            # Convert voice to text
            transcribed_text = speech_service.voice_to_text(temp_path)
            
            if not transcribed_text:
                await context.bot.edit_message_text(
                    chat_id=processing_msg.chat_id,
                    message_id=processing_msg.message_id,
                    text="❌ Could not transcribe the voice message."
                )
                return
            
            # Translate the transcribed text
            translation_result = translation_service.translate_text(transcribed_text, target_lang)
            
            # Add original transcribed text to result
            translation_result['original_voice_text'] = transcribed_text
            
            # Save to history
            db_manager.add_translation_history(user_id, translation_result)
            
            # Format response
            response = f"🎤 **Voice Translation**\n\n"
            response += f"**Transcribed:** {transcribed_text}\n\n"
            response += format_translation_result(translation_result)
            
            await context.bot.edit_message_text(
                chat_id=processing_msg.chat_id,
                message_id=processing_msg.message_id,
                text=response,
                parse_mode='Markdown'
            )
            
        finally:
            # Cleanup temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        
    except Exception as e:
        logger.error(f"Voice message processing failed: {e}")
        error_msg = f"❌ Voice message processing failed: {str(e)}"
        try:
            await context.bot.edit_message_text(
                chat_id=processing_msg.chat_id,
                message_id=processing_msg.message_id,
                text=error_msg
            )
        except:
            await update.message.reply_text(error_msg)

def setup_handlers(application):
    """Setup voice handler"""
    application.add_handler(MessageHandler(filters.VOICE, handle_voice_message))