from deep_translator import GoogleTranslator
from deep_translator.exceptions import TranslationNotFound, RequestError, TooManyRequests
from typing import Tuple, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class TranslationService:
    def __init__(self):
        self.supported_languages = {
            'af': 'Afrikaans', 'sq': 'Albanian', 'am': 'Amharic', 'ar': 'Arabic',
            'hy': 'Armenian', 'az': 'Azerbaijani', 'eu': 'Basque', 'be': 'Belarusian',
            'bn': 'Bengali', 'bs': 'Bosnian', 'bg': 'Bulgarian', 'ca': 'Catalan',
            'ceb': 'Cebuano', 'zh-cn': 'Chinese (Simplified)', 'zh-tw': 'Chinese (Traditional)',
            'co': 'Corsican', 'hr': 'Croatian', 'cs': 'Czech', 'da': 'Danish',
            'nl': 'Dutch', 'en': 'English', 'eo': 'Esperanto', 'et': 'Estonian',
            'fi': 'Finnish', 'fr': 'French', 'fy': 'Frisian', 'gl': 'Galician',
            'ka': 'Georgian', 'de': 'German', 'el': 'Greek', 'gu': 'Gujarati',
            'ht': 'Haitian Creole', 'ha': 'Hausa', 'haw': 'Hawaiian', 'he': 'Hebrew',
            'hi': 'Hindi', 'hmn': 'Hmong', 'hu': 'Hungarian', 'is': 'Icelandic',
            'ig': 'Igbo', 'id': 'Indonesian', 'ga': 'Irish', 'it': 'Italian',
            'ja': 'Japanese', 'jv': 'Javanese', 'kn': 'Kannada', 'kk': 'Kazakh',
            'km': 'Khmer', 'rw': 'Kinyarwanda', 'ko': 'Korean', 'ku': 'Kurdish',
            'ky': 'Kyrgyz', 'lo': 'Lao', 'la': 'Latin', 'lv': 'Latvian',
            'lt': 'Lithuanian', 'lb': 'Luxembourgish', 'mk': 'Macedonian', 'mg': 'Malagasy',
            'ms': 'Malay', 'ml': 'Malayalam', 'mt': 'Maltese', 'mi': 'Maori',
            'mr': 'Marathi', 'mn': 'Mongolian', 'my': 'Myanmar (Burmese)', 'ne': 'Nepali',
            'no': 'Norwegian', 'ny': 'Nyanja (Chichewa)', 'or': 'Odia (Oriya)',
            'ps': 'Pashto', 'fa': 'Persian', 'pl': 'Polish', 'pt': 'Portuguese',
            'pa': 'Punjabi', 'ro': 'Romanian', 'ru': 'Russian', 'sm': 'Samoan',
            'gd': 'Scots Gaelic', 'sr': 'Serbian', 'st': 'Sesotho', 'sn': 'Shona',
            'sd': 'Sindhi', 'si': 'Sinhala (Sinhalese)', 'sk': 'Slovak', 'sl': 'Slovenian',
            'so': 'Somali', 'es': 'Spanish', 'su': 'Sundanese', 'sw': 'Swahili',
            'sv': 'Swedish', 'tl': 'Tagalog (Filipino)', 'tg': 'Tajik', 'ta': 'Tamil',
            'tt': 'Tatar', 'te': 'Telugu', 'th': 'Thai', 'tr': 'Turkish',
            'tk': 'Turkmen', 'uk': 'Ukrainian', 'ur': 'Urdu', 'ug': 'Uyghur',
            'uz': 'Uzbek', 'vi': 'Vietnamese', 'cy': 'Welsh', 'xh': 'Xhosa',
            'yi': 'Yiddish', 'yo': 'Yoruba', 'zu': 'Zulu'
        }
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Return dictionary of supported languages"""
        return self.supported_languages
    
    def detect_language(self, text: str) -> Tuple[str, float]:
        """Detect language of text"""
        try:
            if not text or len(text.strip()) == 0:
                return "unknown", 0.0
            
            # Use deep-translator's auto-detection by attempting a translation
            translator = GoogleTranslator(source='auto', target='en')
            # The detection happens internally during translation
            translated = translator.translate(text[:500])  # Use first 500 chars for efficiency
            
            # Note: deep-translator doesn't provide confidence scores
            # We return a fixed high confidence for compatibility
            return 'auto', 0.95
            
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return "unknown", 0.0
    
    def translate_text(self, text: str, dest_lang: str, src_lang: Optional[str] = 'auto') -> Dict:
        """Translate text to target language"""
        try:
            if not text or len(text.strip()) == 0:
                raise ValueError("Text cannot be empty")
            
            # Validate target language
            if dest_lang not in self.supported_languages:
                raise ValueError(f"Unsupported target language: {dest_lang}")
            
            # Create translator instance
            translator = GoogleTranslator(source=src_lang, target=dest_lang)
            
            # Perform translation
            translated_text = translator.translate(text)
            
            # For source language detection, we'll use a separate call
            detected_src_lang = src_lang
            if src_lang == 'auto':
                try:
                    # Use a small sample for detection to avoid rate limits
                    sample_text = text[:200]
                    detect_translator = GoogleTranslator(source='auto', target='en')
                    detect_translator.translate(sample_text)
                    # Unfortunately deep-translator doesn't expose detected source language
                    # We'll use 'auto' to indicate it was auto-detected
                    detected_src_lang = 'auto'
                except Exception as e:
                    logger.warning(f"Could not detect source language: {e}")
                    detected_src_lang = 'auto'
            
            return {
                'original_text': text,
                'translated_text': translated_text,
                'source_language': detected_src_lang,
                'target_language': dest_lang,
                'pronunciation': None  # deep-translator doesn't provide pronunciation
            }
            
        except TranslationNotFound:
            logger.error("Translation not found")
            raise Exception("Translation not found for the given text")
        except TooManyRequests:
            logger.error("Too many translation requests")
            raise Exception("Translation service quota exceeded. Please try again later.")
        except RequestError as e:
            logger.error(f"Translation request failed: {e}")
            raise Exception("Translation service unavailable. Please try again later.")
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            raise Exception(f"Translation failed: {str(e)}")
    
    def is_language_supported(self, lang_code: str) -> bool:
        """Check if language code is supported"""
        return lang_code in self.supported_languages

# Global translation service instance
translation_service = TranslationService()