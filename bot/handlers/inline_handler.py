from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import InlineQueryHandler, CallbackContext, filters
import logging
from bot.services.translation import translation_service
from bot.services.database import db_manager
from bot.utils.helpers import get_language_name

logger = logging.getLogger(__name__)

async def handle_inline_query(update: Update, context: CallbackContext):
    """Handle inline queries for instant translation"""
    query = update.inline_query.query
    
    if not query or len(query.strip()) == 0:
        return
    
    user_id = update.inline_query.from_user.id
    
    # Get user's default language
    default_lang = 'en'  # Default fallback
    
    if db_manager.is_connected:
        user_prefs = db_manager.get_user_preferences(user_id)
        default_lang = user_prefs.get('default_language', 'en')
    
    try:
        # Perform translation
        translation_result = translation_service.translate_text(query, default_lang)
        
        # Save to history if database is available
        if db_manager.is_connected:
            db_manager.add_translation_history(user_id, translation_result)
        
        # Prepare inline result
        source_lang_name = get_language_name(translation_result['source_language'])
        target_lang_name = get_language_name(translation_result['target_language'])
        
        result = InlineQueryResultArticle(
            id='1',
            title=f"Translate to {target_lang_name}",
            description=translation_result['translated_text'],
            input_message_content=InputTextMessageContent(
                message_text=f"🌐 **Inline Translation**\n\n"
                           f"**From:** {source_lang_name}\n"
                           f"**To:** {target_lang_name}\n\n"
                           f"**Original:** {query}\n"
                           f"**Translated:** {translation_result['translated_text']}",
                parse_mode='Markdown'
            )
        )
        
        await update.inline_query.answer([result], cache_time=1)
        
    except Exception as e:
        logger.error(f"Inline translation failed: {e}")
        # Provide error result
        error_result = InlineQueryResultArticle(
            id='1',
            title="Translation Error",
            description="Could not translate text",
            input_message_content=InputTextMessageContent(
                message_text="❌ Translation failed. Please try again."
            )
        )
        await update.inline_query.answer([error_result], cache_time=1)

def setup_handlers(application):
    """Setup inline handler"""
    application.add_handler(InlineQueryHandler(handle_inline_query))