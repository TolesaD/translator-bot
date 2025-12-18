from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import InlineQueryHandler, CallbackContext
import logging
from bot.services.translation import translation_service
from database import db_manager
from bot.utils.helpers import get_language_name, sanitize_markdown_text

logger = logging.getLogger(__name__)

async def handle_inline_query(update: Update, context: CallbackContext):
    """Handle inline queries for instant translation"""
    try:
        user_id = update.inline_query.from_user.id
        
        # Check if user is banned
        if db_manager.is_user_banned(user_id):
            # Create error result for banned user
            error_result = InlineQueryResultArticle(
                id='banned',
                title="You are banned",
                description="You cannot use this bot",
                input_message_content=InputTextMessageContent(
                    message_text="⛔️ You are banned from using this bot."
                )
            )
            await update.inline_query.answer([error_result], cache_time=300, is_personal=True)
            return
        
        query = update.inline_query.query.strip()
        
        logger.info(f"🎯 INLINE: User {user_id} queried: '{query}'")
        
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
        
        # Get user's default language
        default_lang = 'en'  # Default fallback
        
        if db_manager.is_connected:
            user_prefs = db_manager.get_user_preferences(user_id)
            default_lang = user_prefs.get('default_language', 'en')
        
        # Limit query length for inline mode
        if len(query) > 1000:
            query_display = query[:997] + "..."
        else:
            query_display = query
        
        # Perform translation
        translation_result = translation_service.translate_text(query, default_lang)
        
        # Prepare language names
        source_lang_name = get_language_name(translation_result['source_language'])
        target_lang_name = get_language_name(translation_result['target_language'])
        
        # Sanitize text for Markdown
        original_safe = sanitize_markdown_text(query_display)
        translated_safe = sanitize_markdown_text(translation_result['translated_text'])
        
        # Create the main translation result
        main_result = InlineQueryResultArticle(
            id='translation',
            title=f"→ {target_lang_name}: {translation_result['translated_text'][:60]}{'...' if len(translation_result['translated_text']) > 60 else ''}",
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
                    'original_text': query[:100],
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
        popular_languages = ['es', 'fr', 'de', 'it', 'pt', 'ru', 'ar', 'zh-cn', 'ja', 'hi']  # Top 10 languages
        
        for lang_code in popular_languages:
            if lang_code != default_lang:  # Don't show the same language twice
                try:
                    alt_translation = translation_service.translate_text(query, lang_code)
                    alt_lang_name = get_language_name(lang_code)
                    alt_translated_safe = sanitize_markdown_text(alt_translation['translated_text'])
                    
                    alt_result = InlineQueryResultArticle(
                        id=f'translation_{lang_code}',
                        title=f"→ {alt_lang_name}: {alt_translation['translated_text'][:60]}{'...' if len(alt_translation['translated_text']) > 60 else ''}",
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
        
        # Combine all results (max 10 results total for inline mode)
        all_results = [main_result] + additional_results[:9]
        
        await update.inline_query.answer(all_results, cache_time=1, is_personal=True)
        logger.info(f"✅ INLINE: Sent {len(all_results)} translation options")
        
    except Exception as e:
        logger.error(f"❌ Inline translation failed: {e}")
        
        # Provide error result
        error_result = InlineQueryResultArticle(
            id='error',
            title="Translation Error",
            description="Could not translate text",
            input_message_content=InputTextMessageContent(
                message_text="❌ Translation failed. Please try again with different text."
            )
        )
        await update.inline_query.answer([error_result], cache_time=1, is_personal=True)

def setup_handlers(application):
    """Setup inline handler"""
    application.add_handler(InlineQueryHandler(handle_inline_query))