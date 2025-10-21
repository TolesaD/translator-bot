from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, CallbackContext, filters
import logging
from bot.services.translation import translation_service
from bot.services.database import db_manager
from bot.services.speech import speech_service
from bot.utils.helpers import format_translation_result, validate_language_code, get_language_name, truncate_text, sanitize_markdown_text
from bot.utils.constants import LANGUAGE_NAMES
from bot.utils.checks import require_channel_membership
from datetime import datetime

logger = logging.getLogger(__name__)

# In-memory storage for user preferences (fallback when database is unavailable)
user_preferences_cache = {}

async def start_command(update: Update, context: CallbackContext):
    """Handle /start command"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    welcome_text = f"""
🤖 *Welcome to Universal Translator Bot, {user_name}!*

I can help you translate text between 100+ languages instantly!

*Basic Commands:*
/start - Show this welcome message
/help - Detailed usage guide
/setlang [code] - Set your default language (e.g. /setlang es)
/detect [text] - Detect language of text
/history - Show your translation history
/audio [text] - Translate text and get audio pronunciation
/stats - Show your translation statistics
/mydata - View your stored data

*Features:*
• *Text Translation* - Just send me any text!
• *Voice Translation* - Send voice messages (transcribe & translate)
• *Document Translation* - Upload PDF, DOCX, TXT files
• *Text-to-Speech* - Use /audio command to get voice output
• *Inline Mode* - Use @LanguagesTranslatorBot in any chat!

*Inline Mode Usage:*
1. Go to *any chat* (not this one)
2. Type `@LanguagesTranslatorBot` followed by your text
3. Select from translation options
4. Send instantly!

*Examples:*
• Send any text to translate automatically
• /setlang fr (set French as default)
• /detect Hello world
• /audio Hello world (get audio translation)
• Send a voice message
• Upload a document
• *Inline:* Type `@LanguagesTranslatorBot Hello` in any chat

Start by sending me any text to translate! 🌍
"""
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

@require_channel_membership
async def help_command(update: Update, context: CallbackContext):
    """Handle /help command"""
    # Check if voice features are available
    voice_status = "✅ Available" if speech_service.is_speech_available() else "❌ Temporarily unavailable"
    
    help_text = f"""
📖 **How to Use the Translator Bot**

**1. Text Translation**
Simply send any text and I'll automatically detect the language and translate to your default language.

**2. Set Default Language**
Use `/setlang [code]` to set your preferred target language.
Example: `/setlang es` for Spanish

**3. Voice Message Translation** ({voice_status})
Send a voice message and I'll transcribe and translate it.

**4. Document Translation**
Upload PDF, DOCX, or TXT files and I'll extract and translate the text.

**5. Language Detection**
Use `/detect [text]` to detect the language of any text.

**6. Text-to-Speech**
Use `/audio [text]` to get voice output of the translation.

**7. Inline Mode**
In any chat, type `@LanguagesTranslator [text]` to translate instantly.

**8. Statistics & Data**
Use `/stats` to see your translation statistics
Use `/mydata` to see what data we store about you

**Supported Languages:**
I support 100+ languages including:
• English (en), Spanish (es), French (fr)
• German (de), Italian (it), Portuguese (pt)
• Russian (ru), Chinese (zh), Japanese (ja)
• Arabic (ar), Hindi (hi), and many more!

Use `/setlang` without arguments to see all supported languages.
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

#@require_channel_membership  
async def set_language_command(update: Update, context: CallbackContext):
    """Handle /setlang command"""
    if not context.args:
        # Show supported languages
        languages = translation_service.get_supported_languages()
        # Show first 30 languages to avoid message too long
        lang_list = "\n".join([f"• {name} (`{code}`)" for code, name in list(languages.items())[:30]])
        message = f"**Supported Languages (first 30):**\n\n{lang_list}\n\nUse: `/setlang code`\nExample: `/setlang es` for Spanish"
        await update.message.reply_text(message, parse_mode='Markdown')
        return
    
    lang_code = context.args[0].lower()
    
    if not validate_language_code(lang_code):
        await update.message.reply_text("❌ Invalid language code. Use `/setlang` without arguments to see supported languages.")
        return
    
    user_id = update.effective_user.id
    
    # Set language in database
    db_manager.set_user_language(user_id, lang_code)
    
    # Also update cache for immediate use
    if user_id not in user_preferences_cache:
        user_preferences_cache[user_id] = {}
    user_preferences_cache[user_id]['default_language'] = lang_code
    
    lang_name = get_language_name(lang_code)
    await update.message.reply_text(f"✅ Default language set to **{lang_name}** (`{lang_code}`)", parse_mode='Markdown')

async def detect_language_command(update: Update, context: CallbackContext):
    """Handle /detect command with improved detection and Markdown safety"""
    if not context.args:
        await update.message.reply_text("Please provide text to detect. Usage: `/detect Hello world`", parse_mode='Markdown')
        return
    
    text = " ".join(context.args)
    
    if len(text) < 3:
        await update.message.reply_text("❌ Text too short for detection. Please provide at least 3 characters.")
        return
    
    if len(text) > 5000:
        await update.message.reply_text("❌ Text too long for detection. Please use text shorter than 5000 characters.")
        return
    
    try:
        # Send processing message for longer texts
        if len(text) > 100:
            processing_msg = await update.message.reply_text("🔍 Detecting language...")
        else:
            processing_msg = None
        
        # Perform language detection with multiple fallbacks
        detection_result = translation_service.detect_language_with_fallback(text)
        
        # Log for debugging
        logger.info(f"🔍 Language detection - Text length: {len(text)}, Result: {detection_result}")
        
        source_lang = detection_result.get('language', 'unknown')
        confidence = detection_result.get('confidence', 0)
        method = detection_result.get('method', 'unknown')
        
        # Handle detection results
        if source_lang in ["unknown", "auto", None]:
            # Use plain text for unknown detection to avoid Markdown issues
            response_text = (
                f"🔍 Language Detection\n\n"
                f"Text: {text[:200]}{'...' if len(text) > 200 else ''}\n"
                f"Detected: Could not determine language\n"
                f"Method: {method}\n\n"
                f"This could be because:\n"
                f"• The text is too ambiguous\n"
                f"• Mixed languages in the text\n"
                f"• Technical issue with detection service\n\n"
                f"Try using clearer text in one language."
            )
            
            if processing_msg:
                await context.bot.edit_message_text(
                    chat_id=processing_msg.chat_id,
                    message_id=processing_msg.message_id,
                    text=response_text
                )
            else:
                await update.message.reply_text(response_text)
            return
        
        lang_name = get_language_name(source_lang)
        confidence_percent = f"{confidence * 100:.1f}%" if confidence else "Unknown"
        
        # For Amharic and other complex scripts, use plain text to avoid Markdown issues
        # Check if text contains characters that might break Markdown
        has_complex_script = any(char in text for char in ['ሀ', 'ሁ', 'ሂ', 'ሃ', 'ሄ']) or len(text) > 500
        
        if has_complex_script:
            # Use plain text for complex scripts or long texts
            message = (
                f"🔍 Language Detection\n\n"
                f"Text: {text[:200]}{'...' if len(text) > 200 else ''}\n"
                f"Detected: {lang_name} ({source_lang})\n"
                f"Confidence: {confidence_percent}\n"
                f"Method: {method}"
            )
            parse_mode = None
        else:
            # Use Markdown for simple texts
            message = (
                f"🔍 **Language Detection**\n\n"
                f"**Text:** {text[:200]}{'...' if len(text) > 200 else ''}\n"
                f"**Detected:** {lang_name} (`{source_lang}`)\n"
                f"**Confidence:** {confidence_percent}\n"
                f"**Method:** {method}"
            )
            parse_mode = 'Markdown'
        
        if processing_msg:
            await context.bot.edit_message_text(
                chat_id=processing_msg.chat_id,
                message_id=processing_msg.message_id,
                text=message,
                parse_mode=parse_mode
            )
        else:
            await update.message.reply_text(message, parse_mode=parse_mode)
        
    except Exception as e:
        logger.error(f"Language detection failed: {e}")
        
        # Try again with plain text as fallback
        try:
            error_msg = (
                f"❌ Language detection failed.\n\n"
                f"Error: {str(e)}\n\n"
                f"Please try again with different text."
            )
            
            if processing_msg:
                await context.bot.edit_message_text(
                    chat_id=processing_msg.chat_id,
                    message_id=processing_msg.message_id,
                    text=error_msg
                )
            else:
                await update.message.reply_text(error_msg)
        except Exception as fallback_error:
            # Final fallback - very simple message
            logger.error(f"Even fallback failed: {fallback_error}")
            try:
                if processing_msg:
                    await context.bot.edit_message_text(
                        chat_id=processing_msg.chat_id,
                        message_id=processing_msg.message_id,
                        text="❌ Detection failed. Please try again."
                    )
                else:
                    await update.message.reply_text("❌ Detection failed. Please try again.")
            except:
                pass  # Give up if even this fails

async def history_command(update: Update, context: CallbackContext):
    """Handle /history command"""
    user_id = update.effective_user.id
    
    history = db_manager.get_translation_history(user_id)
    
    if not history:
        await update.message.reply_text("📝 No translation history found.\n\nStart translating text, voice messages, or documents to build your history!")
        return
    
    message = "📝 **Recent Translations**\n\n"
    
    for i, item in enumerate(history, 1):
        # Truncate long texts for display and sanitize for Markdown
        orig_truncated = item['original_text'][:80] + "..." if len(item['original_text']) > 80 else item['original_text']
        trans_truncated = item['translated_text'][:80] + "..." if len(item['translated_text']) > 80 else item['translated_text']
        
        # Sanitize text to prevent Markdown parsing errors
        orig_truncated = sanitize_markdown_text(orig_truncated)
        trans_truncated = sanitize_markdown_text(trans_truncated)
        
        # Get language names
        source_lang_name = get_language_name(item['source_language'])
        target_lang_name = get_language_name(item['target_language'])
        
        # Sanitize language names too
        source_lang_name = sanitize_markdown_text(source_lang_name)
        target_lang_name = sanitize_markdown_text(target_lang_name)
        
        # Add type emoji
        type_emoji = "📄" if item.get('translation_type') == 'document' else "🎤" if item.get('translation_type') == 'voice' else "🔊" if item.get('translation_type') == 'audio' else "📝"
        
        message += f"{i}. {type_emoji} From {source_lang_name} → To {target_lang_name}\n"
        message += f"   📖 Original: {orig_truncated}\n"
        message += f"   🌐 Translated: {trans_truncated}\n\n"
    
    message += f"💾 Showing last {len(history)} translations"
    
    # Send without Markdown to avoid parsing errors
    await update.message.reply_text(message)

async def stats_command(update: Update, context: CallbackContext):
    """Handle /stats command - show user statistics"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    stats = db_manager.get_user_stats(user_id)
    
    if not stats or stats.get('total_translations', 0) == 0:
        await update.message.reply_text(
            f"📊 *Hello {user_name}!*\n\n"
            "You haven't made any translations yet. Start translating to see your statistics!\n\n"
            "Try sending some text, a voice message, or uploading a document to get started! 🌍"
        )
        return
    
    message = f"📊 **{user_name}'s Translation Statistics**\n\n"
    message += f"• **Total Translations:** {stats['total_translations']}\n"
    message += f"• **Total Words:** {stats['total_words']:,}\n"
    message += f"• **Total Characters:** {stats['total_characters']:,}\n"
    message += f"• **Active Days:** {stats['active_days']}\n"
    message += f"• **Favorite Language:** {get_language_name(stats['favorite_language'])}\n"
    
    if stats.get('first_translation'):
        try:
            first_date = datetime.fromisoformat(stats['first_translation'].replace('Z', '+00:00')).strftime('%Y-%m-%d')
            message += f"• **First Translation:** {first_date}\n"
        except:
            pass
    
    # Get top languages
    top_langs = db_manager.get_top_languages(user_id, 3)
    if top_langs:
        message += "\n**Most Used Languages:**\n"
        for lang_code, count in top_langs:
            lang_name = get_language_name(lang_code)
            percentage = (count / stats['total_translations']) * 100
            message += f"• {lang_name}: {count} ({percentage:.1f}%)\n"
    
    # Calculate average words per translation
    if stats['total_translations'] > 0:
        avg_words = stats['total_words'] / stats['total_translations']
        message += f"• **Average Words/Translation:** {avg_words:.1f}\n"
    
    message += "\n🎯 *Keep translating to improve your language skills!*"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def mydata_command(update: Update, context: CallbackContext):
    """Handle /mydata command - show user's stored data"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    # Get user data
    user_prefs = db_manager.get_user_preferences(user_id)
    history_count = len(db_manager.get_translation_history(user_id))
    stats = db_manager.get_user_stats(user_id)
    
    message = f"🔒 **{user_name}'s Data Privacy**\n\n"
    
    message += "**📊 Stored Information:**\n"
    message += f"• User ID: `{user_id}`\n"
    message += f"• Default Language: {get_language_name(user_prefs.get('default_language', 'Not set'))}\n"
    message += f"• Translation History: {history_count} entries\n"
    
    if stats:
        message += f"• Total Translations: {stats.get('total_translations', 0)}\n"
        message += f"• Total Words Translated: {stats.get('total_words', 0):,}\n"
    
    message += "\n**🔐 Privacy & Data Protection:**\n"
    message += "• Translation history is automatically deleted after 90 days\n"
    message += "• No personal data is shared with third parties\n"
    message += "• Voice messages are processed and immediately deleted\n"
    message += "• Documents are processed temporarily and not stored\n"
    
    message += "\n**🗑️ Data Management:**\n"
    message += "• Your data is automatically managed and cleaned up\n"
    message += "• No manual data deletion is required\n"
    message += "• All processing happens securely on the server\n"
    
    message += "\n*Your privacy and data security are our top priorities!* 🔒"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def audio_command(update: Update, context: CallbackContext):
    """Handle /audio command for text-to-speech"""
    if not context.args:
        await update.message.reply_text(
            "Usage: `/audio [text to translate and convert to speech]`\n\n"
            "Example: `/audio Hello world`\n"
            "This will translate the text to your default language and send audio.",
            parse_mode='Markdown'
        )
        return
    
    user_id = update.effective_user.id
    text = " ".join(context.args)
    
    # Limit text length for audio generation
    if len(text) > 500:
        await update.message.reply_text("❌ Text too long for audio generation. Please use text shorter than 500 characters.")
        return
    
    # Get user's default language
    default_lang = 'en'  # Default fallback
    
    if db_manager.is_connected:
        user_prefs = db_manager.get_user_preferences(user_id)
        default_lang = user_prefs.get('default_language', 'en')
    else:
        # Check cache
        if user_id in user_preferences_cache:
            default_lang = user_preferences_cache[user_id].get('default_language', 'en')
    
    if not default_lang:
        await update.message.reply_text("Please set your default language first using `/setlang` command.", parse_mode='Markdown')
        return
    
    try:
        # Send processing message
        processing_msg = await update.message.reply_text("🔊 Processing audio translation...")
        
        # First translate the text
        translation_result = translation_service.translate_text(text, default_lang)
        
        # Save to history with audio type
        history_data = {
            'original_text': text,
            'translated_text': translation_result.get('translated_text', ''),
            'source_language': translation_result.get('source_language', 'auto'),
            'target_language': default_lang,
            'translation_type': 'audio'
        }
        db_manager.add_translation_history(user_id, history_data)
        
        # Convert to speech
        audio_file = None
        try:
            audio_file = speech_service.text_to_speech(translation_result['translated_text'], default_lang)
            
            # Send the text translation first
            response_text = format_translation_result(translation_result, include_detection=True)
            await context.bot.edit_message_text(
                chat_id=processing_msg.chat_id,
                message_id=processing_msg.message_id,
                text=response_text,
                parse_mode='Markdown'
            )
            
            # Send the audio file
            with open(audio_file, 'rb') as audio:
                await update.message.reply_voice(
                    voice=audio,
                    caption=f"🎧 Audio translation to {get_language_name(default_lang)}"
                )
            
        except Exception as e:
            logger.error(f"Audio generation failed: {e}")
            # If audio fails, still send the text translation
            response_text = format_translation_result(translation_result, include_detection=True)
            response_text += f"\n\n❌ Could not generate audio: {str(e)}"
            await context.bot.edit_message_text(
                chat_id=processing_msg.chat_id,
                message_id=processing_msg.message_id,
                text=response_text,
                parse_mode='Markdown'
            )
            
        finally:
            # Cleanup temporary file
            if audio_file:
                speech_service.cleanup_file(audio_file)
            
    except Exception as e:
        logger.error(f"Audio command failed: {e}")
        error_msg = f"❌ Failed to process audio command: {str(e)}"
        try:
            await context.bot.edit_message_text(
                chat_id=processing_msg.chat_id,
                message_id=processing_msg.message_id,
                text=error_msg
            )
        except:
            await update.message.reply_text(error_msg)

async def handle_text_message(update: Update, context: CallbackContext):
    """Handle regular text messages for translation"""
    user_id = update.effective_user.id
    text = update.message.text
    
    # Ignore empty messages or very long texts
    if not text.strip():
        return
    
    if len(text) > 5000:
        await update.message.reply_text("❌ Text too long. Please use text shorter than 5000 characters.")
        return
    
    # Get user's default language
    default_lang = 'en'  # Default fallback
    
    if db_manager.is_connected:
        user_prefs = db_manager.get_user_preferences(user_id)
        default_lang = user_prefs.get('default_language', 'en')
    else:
        # Check cache
        if user_id in user_preferences_cache:
            default_lang = user_preferences_cache[user_id].get('default_language', 'en')
    
    if not default_lang:
        await update.message.reply_text(
            "🌍 Please set your default language first using `/setlang` command.\n\n"
            "Example: `/setlang es` for Spanish\n"
            "Use `/setlang` without arguments to see all supported languages.",
            parse_mode='Markdown'
        )
        return
    
    try:
        # Send processing message for longer texts
        if len(text) > 100:
            processing_msg = await update.message.reply_text("🔄 Translating...")
        else:
            processing_msg = None
        
        # Perform translation
        translation_result = translation_service.translate_text(text, default_lang)
        
        # Save to history
        history_data = {
            'original_text': text,
            'translated_text': translation_result.get('translated_text', ''),
            'source_language': translation_result.get('source_language', 'auto'),
            'target_language': default_lang,
            'translation_type': 'text'
        }
        db_manager.add_translation_history(user_id, history_data)
        
        # Format and send response
        response_text = format_translation_result(translation_result, include_detection=True)
        
        if processing_msg:
            await context.bot.edit_message_text(
                chat_id=processing_msg.chat_id,
                message_id=processing_msg.message_id,
                text=response_text,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(response_text, parse_mode='Markdown')
            
    except Exception as e:
        logger.error(f"Text translation failed: {e}")
        error_msg = f"❌ Translation failed: {str(e)}"
        if processing_msg:
            await context.bot.edit_message_text(
                chat_id=processing_msg.chat_id,
                message_id=processing_msg.message_id,
                text=error_msg
            )
        else:
            await update.message.reply_text(error_msg)

def setup_handlers(application):
    """Setup all text handlers"""
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("setlang", set_language_command))
    application.add_handler(CommandHandler("detect", detect_language_command))
    application.add_handler(CommandHandler("history", history_command))
    application.add_handler(CommandHandler("audio", audio_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("mydata", mydata_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))