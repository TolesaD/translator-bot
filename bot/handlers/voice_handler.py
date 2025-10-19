from telegram import Update
from telegram.ext import MessageHandler, CallbackContext, filters
import logging
import tempfile
import os
from bot.services.speech import speech_service
from bot.services.translation import translation_service
from bot.services.database import db_manager
from bot.utils.helpers import format_translation_result, get_language_name

logger = logging.getLogger(__name__)

async def handle_voice_message(update: Update, context: CallbackContext):
    """Handle voice messages for transcription and translation"""
    user_id = update.effective_user.id
    voice = update.message.voice
    
    # Check if speech recognition is available
    if not speech_service.is_speech_available():
        await update.message.reply_text(
            "🎤 Voice message translation is currently unavailable. "
            "Speech recognition service is not available. "
            "Please use text messages for translation."
        )
        return
    
    # Check voice message duration and size
    if voice.duration < 2:
        await update.message.reply_text(
            "❌ Voice message is too short. Please send a message that's at least 2 seconds long."
        )
        return
    
    if voice.file_size < 2000:  # Less than 2KB
        await update.message.reply_text(
            "❌ Voice message is too small. The audio might be corrupted or too quiet."
        )
        return
    
    # Get user's default language
    user_prefs = db_manager.get_user_preferences(user_id)
    target_lang = user_prefs.get('default_language', 'en')
    
    if not target_lang:
        await update.message.reply_text("Please set your default language first using /setlang command.")
        return
    
    temp_path = None
    processing_msg = None
    
    try:
        # Send processing message
        processing_msg = await update.message.reply_text(
            f"🎤 Processing voice message ({voice.duration}s)..."
        )
        
        # Download voice file
        voice_file = await voice.get_file()
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as temp_file:
            temp_path = temp_file.name
            await voice_file.download_to_drive(temp_path)
        
        logger.info(f"Voice file downloaded: {temp_path}, size: {os.path.getsize(temp_path)} bytes")
        
        # Step 1: Convert voice to text
        await context.bot.edit_message_text(
            chat_id=processing_msg.chat_id,
            message_id=processing_msg.message_id,
            text="🎤 Transcribing voice message..."
        )
        
        transcribed_text = speech_service.voice_to_text(temp_path)
        
        if not transcribed_text:
            await context.bot.edit_message_text(
                chat_id=processing_msg.chat_id,
                message_id=processing_msg.message_id,
                text="❌ Could not transcribe the voice message. Please try again with clearer audio."
            )
            return
        
        # Check if transcribed text is meaningful
        transcribed_text = transcribed_text.strip()
        if len(transcribed_text) < 2:
            await context.bot.edit_message_text(
                chat_id=processing_msg.chat_id,
                message_id=processing_msg.message_id,
                text="❌ Transcribed text is too short or empty. Please try again with clearer speech."
            )
            return
        
        # Step 2: Translate the text
        await context.bot.edit_message_text(
            chat_id=processing_msg.chat_id,
            message_id=processing_msg.message_id,
            text="🔄 Translating transcribed text..."
        )
        
        translation_result = translation_service.translate_text(transcribed_text, target_lang)
        
        # Save to history
        history_data = {
            'original_text': transcribed_text,
            'translated_text': translation_result.get('translated_text', ''),
            'source_language': translation_result.get('source_language', 'auto'),
            'target_language': target_lang,
            'translation_type': 'voice'
        }
        db_manager.add_translation_history(user_id, history_data)
        
        # Format response
        response = f"🎤 **Voice Translation**\n\n"
        response += f"**Duration:** {voice.duration} seconds\n"
        response += f"**Transcribed:** {transcribed_text}\n\n"
        response += format_translation_result(translation_result)
        
        await context.bot.edit_message_text(
            chat_id=processing_msg.chat_id,
            message_id=processing_msg.message_id,
            text=response,
            parse_mode='Markdown'
        )
        
        logger.info(f"Voice translation completed for user {user_id}")
        
    except Exception as e:
        logger.error(f"Voice message processing failed: {e}", exc_info=True)
        
        # Provide user-friendly error messages
        error_msg = str(e)
        if "could not understand" in error_msg.lower():
            user_error = "❌ Could not understand the audio. Please speak clearly and try again."
        elif "service is unavailable" in error_msg.lower():
            user_error = "❌ Speech recognition service is temporarily unavailable. Please try again later."
        elif "required package" in error_msg.lower():
            user_error = "❌ Speech recognition is not properly configured. Please contact support."
        else:
            user_error = f"❌ Could not process voice message: {error_msg}"
        
        try:
            if processing_msg:
                await context.bot.edit_message_text(
                    chat_id=processing_msg.chat_id,
                    message_id=processing_msg.message_id,
                    text=user_error
                )
            else:
                await update.message.reply_text(user_error)
        except Exception as edit_error:
            logger.error(f"Could not update error message: {edit_error}")
            await update.message.reply_text(user_error)
    
    finally:
        # Cleanup temporary file
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
                logger.debug(f"Cleaned up temporary voice file: {temp_path}")
            except Exception as e:
                logger.warning(f"Could not cleanup temp file {temp_path}: {e}")

def setup_handlers(application):
    """Setup voice handler"""
    application.add_handler(MessageHandler(filters.VOICE, handle_voice_message))