from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import InlineQueryHandler, CallbackContext
import logging
from bot.services.translation import translation_service
from bot.services.database import db_manager
from bot.utils.helpers import get_language_name, sanitize_markdown_text

logger = logging.getLogger(__name__)

async def handle_inline_query(update: Update, context: CallbackContext):
    """Handle inline queries for instant translation"""
    query = update.inline_query.query.strip()
    
    # Show help when no query is provided
    if not query:
        help_result = InlineQueryResultArticle(
            id='help',
            title="Universal Translator - Type text to translate",
            description="Example: Hello world → Hola mundo",
            input_message_content=InputTextMessageContent(
                message_text=(
                    "🌐 **Universal Translator Bot**\n\n"
                    "Use inline mode to translate instantly in any chat!\n\n"
                    "Simply type: `@LanguagesTranslatorBot your text here`\n\n"
                    "Supports 100+ languages automatically!"
                ),
                parse_mode='Markdown'
            )
        )
        await update.inline_query.answer([help_result], cache_time=300, is_personal=True)
        return
    
    user_id = update.inline_query.from_user.id
    
    # Get user's default language
    default_lang = 'en'  # Default fallback
    
    if db_manager.is_connected:
        user_prefs = db_manager.get_user_preferences(user_id)
        default_lang = user_prefs.get('default_language', 'en')
    
    try:
        # Limit query length for inline mode (Telegram has limits)
        if len(query) > 256:
            query_display = query[:253] + "..."
        else:
            query_display = query
        
        logger.info(f"🔍 Inline query from user {user_id}: '{query}' -> {default_lang}")
        
        # Perform translation
        translation_result = translation_service.translate_text(query, default_lang)
        
        # Prepare language names
        source_lang_name = get_language_name(translation_result['source_language'])
        target_lang_name = get_language_name(translation_result['target_language'])
        
        # Sanitize text for Markdown to prevent parsing errors
        original_safe = sanitize_markdown_text(query_display)
        translated_safe = sanitize_markdown_text(translation_result['translated_text'])
        
        # Create the main translation result
        main_result = InlineQueryResultArticle(
            id='translation',
            title=f"→ {target_lang_name}: {translation_result['translated_text'][:50]}{'...' if len(translation_result['translated_text']) > 50 else ''}",
            description=f"From {source_lang_name} to {target_lang_name}",
            input_message_content=InputTextMessageContent(
                message_text=(
                    f"🌐 **Inline Translation**\n\n"
                    f"**From:** {source_lang_name}\n"
                    f"**To:** {target_lang_name}\n\n"
                    f"**Original:** {original_safe}\n"
                    f"**Translated:** {translated_safe}"
                ),
                parse_mode='Markdown'
            )
        )
        
        # Save to history if database is available
        if db_manager.is_connected:
            try:
                history_data = {
                    'original_text': query[:100],  # Truncate for history
                    'translated_text': translation_result['translated_text'][:100],
                    'source_language': translation_result['source_language'],
                    'target_language': default_lang,
                    'translation_type': 'inline'
                }
                db_manager.add_translation_history(user_id, history_data)
            except Exception as history_error:
                logger.warning(f"Failed to save inline history: {history_error}")
        
        # Create additional results for popular languages
        additional_results = []
        popular_languages = ['es', 'fr', 'de', 'it', 'pt']  # Spanish, French, German, Italian, Portuguese
        
        for lang_code in popular_languages:
            if lang_code != default_lang:  # Don't show the same language twice
                try:
                    alt_translation = translation_service.translate_text(query, lang_code)
                    alt_lang_name = get_language_name(lang_code)
                    alt_translated_safe = sanitize_markdown_text(alt_translation['translated_text'])
                    
                    alt_result = InlineQueryResultArticle(
                        id=f'translation_{lang_code}',
                        title=f"→ {alt_lang_name}: {alt_translation['translated_text'][:50]}{'...' if len(alt_translation['translated_text']) > 50 else ''}",
                        description=f"Translate to {alt_lang_name}",
                        input_message_content=InputTextMessageContent(
                            message_text=(
                                f"🌐 **Inline Translation**\n\n"
                                f"**From:** {source_lang_name}\n"
                                f"**To:** {alt_lang_name}\n\n"
                                f"**Original:** {original_safe}\n"
                                f"**Translated:** {alt_translated_safe}"
                            ),
                            parse_mode='Markdown'
                        )
                    )
                    additional_results.append(alt_result)
                except Exception as alt_error:
                    logger.warning(f"Failed to create alternative translation for {lang_code}: {alt_error}")
        
        # Combine all results
        all_results = [main_result] + additional_results[:4]  # Limit to 5 total results
        
        await update.inline_query.answer(all_results, cache_time=1, is_personal=True)
        
    except Exception as e:
        logger.error(f"Inline translation failed: {e}")
        
        # Provide helpful error result
        error_result = InlineQueryResultArticle(
            id='error',
            title="Translation Error",
            description="Could not translate text - please try again",
            input_message_content=InputTextMessageContent(
                message_text=(
                    "❌ **Translation Failed**\n\n"
                    "Sorry, I couldn't translate that text.\n\n"
                    "This might be because:\n"
                    "• The text is too long\n"
                    "• Unsupported characters\n"
                    "• Temporary service issue\n\n"
                    "Please try again with different text."
                ),
                parse_mode='Markdown'
            )
        )
        await update.inline_query.answer([error_result], cache_time=1, is_personal=True)

def setup_handlers(application):
    """Setup inline handler"""
    application.add_handler(InlineQueryHandler(handle_inline_query))