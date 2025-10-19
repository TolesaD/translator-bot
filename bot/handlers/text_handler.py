from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, CallbackContext, filters
import logging
from bot.services.translation import translation_service
from bot.services.database import db_manager
from bot.services.speech import speech_service
from bot.utils.helpers import format_translation_result, validate_language_code, get_language_name
from bot.utils.constants import LANGUAGE_NAMES
from bot.utils.checks import require_channel_membership

logger = logging.getLogger(__name__)

# In-memory storage for user preferences (fallback when database is unavailable)
user_preferences_cache = {}

async def start_command(update: Update, context: CallbackContext):
    """Handle /start command"""
    welcome_text = """
🤖 *Welcome to Universal Translator Bot!*

I can help you translate text between 100+ languages instantly!

*Basic Commands:*
/start - Show this welcome message
/help - Detailed usage guide
/setlang [code] - Set your default language (e.g. /setlang es)
/detect [text] - Detect language of text
/history - Show your translation history
/audio [text] - Translate text and get audio pronunciation

*Features:*
• *Text Translation* - Just send me any text!
• *Voice Translation* - Send voice messages (transcribe & translate)
• *Document Translation* - Upload PDF, DOCX, TXT files
• *Text-to-Speech* - Use /audio command to get voice output
• *Inline Mode* - Use @LanguagesTranslatorBot in any chat!

*Examples:*
• Send any text to translate automatically
• /setlang fr (set French as default)
• /detect Hello world
• /audio Hello world (get audio translation)
• Send a voice message
• Upload a document

Start by sending me any text to translate! 🌍
"""
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

@require_channel_membership
async def help_command(update: Update, context: CallbackContext):
    """Handle /help command"""
    # Check if voice features are available
    voice_status = "✅ Available" if speech_service.is_speech_available() else "❌ Temporarily unavailable"
    
    # Check database status
    db_status = "✅ Connected" if db_manager.is_connected else "❌ Disabled (running in memory)"
    
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

**Database Status:** {db_status}

**Supported Languages:**
I support 100+ languages including:
• English (en), Spanish (es), French (fr)
• German (de), Italian (it), Portuguese (pt)
• Russian (ru), Chinese (zh), Japanese (ja)
• Arabic (ar), Hindi (hi), and many more!

Use `/setlang` without arguments to see all supported languages.
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

@require_channel_membership  
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
    
    # Try database first, then fallback to cache
    if db_manager.is_connected:
        db_manager.set_user_language(user_id, lang_code)
    else:
        # Use in-memory cache
        if user_id not in user_preferences_cache:
            user_preferences_cache[user_id] = {}
        user_preferences_cache[user_id]['default_language'] = lang_code
    
    lang_name = get_language_name(lang_code)
    await update.message.reply_text(f"✅ Default language set to **{lang_name}** (`{lang_code}`)", parse_mode='Markdown')

async def detect_language_command(update: Update, context: CallbackContext):
    """Handle /detect command"""
    if not context.args:
        await update.message.reply_text("Please provide text to detect. Usage: `/detect Hello world`", parse_mode='Markdown')
        return
    
    text = " ".join(context.args)
    source_lang, confidence = translation_service.detect_language(text)
    
    if source_lang == "unknown":
        await update.message.reply_text("❌ Could not detect language")
        return
    
    lang_name = get_language_name(source_lang)
    confidence_percent = confidence * 100 if confidence else "Unknown"
    
    message = f"🔍 **Language Detection**\n\n**Text:** {text}\n**Detected:** {lang_name} (`{source_lang}`)\n**Confidence:** {confidence_percent}%"
    await update.message.reply_text(message, parse_mode='Markdown')

async def history_command(update: Update, context: CallbackContext):
    """Handle /history command"""
    user_id = update.effective_user.id
    
    if not db_manager.is_connected:
        await update.message.reply_text(
            "📝 Translation history is currently unavailable.\n\n"
            "Database connection is disabled. When MongoDB is connected, "
            "your translation history will be saved automatically."
        )
        return
    
    history = db_manager.get_translation_history(user_id)
    
    if not history:
        await update.message.reply_text("📝 No translation history found.")
        return
    
    # Show last 5 translations
    recent_history = history[-5:]
    message = "📝 **Recent Translations**\n\n"
    
    for i, item in enumerate(recent_history, 1):
        orig_truncated = item['original_text'][:50] + "..." if len(item['original_text']) > 50 else item['original_text']
        trans_truncated = item['translated_text'][:50] + "..." if len(item['translated_text']) > 50 else item['translated_text']
        
        message += f"{i}. **From** {get_language_name(item['source_language'])} → **To** {get_language_name(item['target_language'])}\n"
        message += f"   Original: {orig_truncated}\n"
        message += f"   Translated: {trans_truncated}\n\n"
    
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
        
        # Save to history if database is available
        if db_manager.is_connected:
            db_manager.add_translation_history(user_id, translation_result)
        
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
    
    # Ignore empty messages
    if not text.strip():
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
        
        # Save to history if database is available
        if db_manager.is_connected:
            db_manager.add_translation_history(user_id, translation_result)
        
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
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))