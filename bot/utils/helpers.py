import re
import logging
from typing import Optional
from bot.services.translation import translation_service
from bot.utils.constants import LANGUAGE_NAMES

logger = logging.getLogger(__name__)

def validate_language_code(lang_code: str) -> bool:
    """Validate if language code is supported"""
    try:
        # Get supported languages from translation service
        supported_languages = translation_service.get_supported_languages()
        return lang_code.lower() in supported_languages
    except Exception as e:
        # Fallback: check against LANGUAGE_NAMES
        logger.warning(f"Translation service validation failed, using fallback: {e}")
        return lang_code.lower() in LANGUAGE_NAMES

def get_language_name(lang_code: str) -> str:
    """Get full language name from code"""
    try:
        languages = translation_service.get_supported_languages()
        return languages.get(lang_code.lower(), f"Unknown ({lang_code})")
    except Exception as e:
        # Fallback to constants
        logger.warning(f"Translation service failed, using constants fallback: {e}")
        return LANGUAGE_NAMES.get(lang_code.lower(), f"Unknown ({lang_code})")

def sanitize_text(text: str) -> str:
    """Sanitize and clean text"""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    return text

def truncate_text(text: str, max_length: int) -> str:
    """Truncate text to maximum length"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def format_translation_result(translation_data: dict, include_detection: bool = False) -> str:
    """Format translation result for display"""
    result = f"🌐 **Translation**\n\n"
    
    if include_detection and translation_data['source_language'] != 'auto':
        source_lang = get_language_name(translation_data['source_language'])
        result += f"**Detected Language:** {source_lang}\n\n"
    
    result += f"**Original:**\n{translation_data['original_text']}\n\n"
    result += f"**Translated:**\n{translation_data['translated_text']}"
    
    if translation_data.get('pronunciation'):
        result += f"\n\n**Pronunciation:**\n{translation_data['pronunciation']}"
    
    return result

def sanitize_markdown_text(text: str) -> str:
    """Sanitize text to prevent Markdown parsing errors"""
    if not text:
        return ""
    
    # Escape Markdown special characters
    markdown_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    for char in markdown_chars:
        text = text.replace(char, f'\\{char}')
    
    return text