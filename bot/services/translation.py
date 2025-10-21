import logging
from deep_translator import GoogleTranslator
from bot.utils.constants import SUPPORTED_LANGUAGES

logger = logging.getLogger(__name__)

class TranslationService:
    def __init__(self):
        self.supported_languages = SUPPORTED_LANGUAGES
        logger.info("✅ Translation service initialized")

    def get_supported_languages(self):
        """Return supported languages"""
        return self.supported_languages

    def detect_language(self, text: str):
        """Detect language using GoogleTranslator"""
        try:
            if len(text.strip()) < 2:
                return "unknown", 0.0
                
            detector = GoogleTranslator()
            detection = detector.detect(text)
            
            logger.info(f"🔍 Raw detection result: {detection}")
            
            if detection and isinstance(detection, str):
                # If it returns a string like 'en'
                return detection, 0.95
            elif detection and isinstance(detection, list) and len(detection) > 0:
                # If it returns a list like ['en', 0.95]
                lang_code = detection[0]
                confidence = detection[1] if len(detection) > 1 else 0.95
                return lang_code, confidence
            else:
                return "unknown", 0.0
                
        except Exception as e:
            logger.error(f"Language detection error: {e}")
            return "unknown", 0.0

    def detect_amharic_specific(self, text: str) -> dict:
        """Specific detection for Amharic language"""
        # Ethiopic Unicode range: U+1200 to U+137F
        ethiopic_chars = 0
        total_chars = 0
        
        for char in text:
            if '\u1200' <= char <= '\u137F':  # Ethiopic script range
                ethiopic_chars += 1
            if char.isalpha():
                total_chars += 1
        
        if total_chars > 0:
            ethiopic_ratio = ethiopic_chars / total_chars
            if ethiopic_ratio > 0.3:  # If 30%+ of alphabetic characters are Ethiopic
                return {
                    'language': 'am',
                    'confidence': min(ethiopic_ratio, 0.95),
                    'method': 'ethiopic_script'
                }
        
        return None

    def _simple_language_detection(self, text: str) -> dict:
        """Simple keyword-based language detection for common languages"""
        text_lower = text.lower()
        
        # Common words for major languages - IMPROVED FOR AMHARIC
        language_keywords = {
            'en': ['the', 'and', 'is', 'are', 'was', 'were', 'this', 'that', 'with', 'for'],
            'es': ['el', 'la', 'los', 'las', 'de', 'que', 'y', 'en', 'un', 'una'],
            'fr': ['le', 'la', 'les', 'de', 'et', 'en', 'un', 'une', 'des', 'que'],
            'de': ['der', 'die', 'das', 'und', 'in', 'den', 'von', 'zu', 'mit', 'sich'],
            'it': ['il', 'la', 'le', 'di', 'e', 'che', 'in', 'un', 'una', 'per'],
            'pt': ['o', 'a', 'os', 'as', 'de', 'e', 'em', 'um', 'uma', 'para'],
            'ru': ['и', 'в', 'не', 'на', 'я', 'быть', 'с', 'что', 'а', 'по'],
            'zh': ['的', '是', '在', '和', '了', '有', '我', '他', '这', '不'],
            'ja': ['の', 'に', 'は', 'を', 'た', 'が', 'で', 'て', 'と', 'し'],
            'ar': ['في', 'من', 'على', 'أن', 'ما', 'هو', 'هي', 'إلى', 'كان', 'لا'],
            'am': ['እና', 'ውስጥ', 'ነው', 'አይደለም', 'ይህ', 'ያ', 'ከ', 'ለ', 'በ', 'እኔ']  # Amharic common words
        }
        
        # Character-based detection for Amharic (Ethiopic script)
        ethiopic_chars = set('ሀሁሂሃሄህሆለሉሊላሌልሎሏሐሑሒሓሔሕሖሗመሙሚማሜምሞሟሠሡሢሣሤሥሦሧረሩሪራሬርሮሯሰሱሲሳሴስሶሷሸሹሺሻሼሽሾሿቀቁቂቃቄቅቆቋበቡቢባቤብቦቧቨቩቪቫቬቭቮቯተቱቲታቴትቶቷቸቹቺቻቼችቾቿኀኁኂኃኄኅኆኇኈ኉ኊኋኌኍ኎ነኑኒናኔንኖኗኘኙኚኛኜኝኞኟአኡኢኣኤእኦኧከኩኪካኬክኮኳኸኹኺኻኼኽኾወዉዊዋዌውዎዐዑዒዓዔዕዖዘዙዚዛዜዝዞዟዠዡዢዣዤዥዦዧየዩዪያዬይዮደዱዲዳዴድዶዷዸዹዺዻዼዽዾዿጀጁጂጃጄጅጆጇገጉጊጋጌግጎጏጠጡጢጣጤጥጦጧጨጩጪጫጬጭጮጯጰጱጲጳጴጵጶጷጸጹጺጻጼጽጾጿፀፁፂፃፄፅፆፇፈፉፊፋፌፍፎፏፐፑፒፓፔፕፖፗ')
        
        # Check for Ethiopic script (Amharic, Tigrinya, etc.)
        ethiopic_count = sum(1 for char in text if char in ethiopic_chars)
        if ethiopic_count > 0:
            amharic_ratio = ethiopic_count / len(text)
            if amharic_ratio > 0.3:  # If 30%+ characters are Ethiopic
                return {
                    'language': 'am',
                    'confidence': min(amharic_ratio, 0.9)
                }
        
        scores = {}
        for lang_code, keywords in language_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                scores[lang_code] = score
        
        if scores:
            best_lang = max(scores.items(), key=lambda x: x[1])
            confidence = min(best_lang[1] / 10.0, 0.8)  # Normalize to 0-0.8 confidence
            return {
                'language': best_lang[0],
                'confidence': confidence
            }
        
        return None

    def detect_language_with_fallback(self, text: str) -> dict:
        """
        Detect language with multiple fallback methods
        Returns: {'language': 'en', 'confidence': 0.95, 'method': 'primary'}
        """
        try:
            # Method 0: Specific script detection for Amharic
            amharic_detection = self.detect_amharic_specific(text)
            if amharic_detection:
                logger.info(f"🔍 Amharic script detection: {amharic_detection}")
                return amharic_detection

            # Method 1: Primary detection (GoogleTranslator)
            try:
                source_lang, confidence = self.detect_language(text)
                logger.info(f"🔍 Primary detection: {source_lang}, {confidence}")
                
                if source_lang and source_lang not in ['unknown', 'auto'] and confidence > 0.1:
                    return {
                        'language': source_lang,
                        'confidence': confidence,
                        'method': 'google_translator'
                    }
            except Exception as e:
                logger.warning(f"Primary detection failed: {e}")

            # Method 2: Try langdetect library
            try:
                from langdetect import detect, detect_langs, LangDetectException
                detected_langs = detect_langs(text)
                logger.info(f"🔍 Langdetect result: {detected_langs}")
                
                if detected_langs:
                    best_lang = detected_langs[0]
                    if best_lang.prob > 0.1:  # Minimum confidence
                        return {
                            'language': best_lang.lang,
                            'confidence': best_lang.prob,
                            'method': 'langdetect'
                        }
            except ImportError:
                logger.warning("langdetect not available")
            except LangDetectException as e:
                logger.warning(f"langdetect failed: {e}")
            except Exception as e:
                logger.warning(f"langdetect error: {e}")

            # Method 3: Simple keyword-based detection for common languages
            simple_detection = self._simple_language_detection(text)
            if simple_detection:
                logger.info(f"🔍 Keyword detection: {simple_detection}")
                return {
                    'language': simple_detection['language'],
                    'confidence': simple_detection['confidence'],
                    'method': 'keyword'
                }

            # Method 4: Try translation with 'auto' detection
            try:
                # Translate to English and see what source language was detected
                translation_result = self.translate_text(text, 'en')
                detected_lang = translation_result.get('source_language', 'unknown')
                logger.info(f"🔍 Translation fallback detection: {detected_lang}")
                
                if detected_lang and detected_lang != 'auto':
                    return {
                        'language': detected_lang,
                        'confidence': 0.5,  # Medium confidence
                        'method': 'translation_fallback'
                    }
            except Exception as e:
                logger.warning(f"Translation fallback detection failed: {e}")

            return {
                'language': 'unknown',
                'confidence': 0,
                'method': 'all_methods_failed'
            }
            
        except Exception as e:
            logger.error(f"All language detection methods failed: {e}")
            return {
                'language': 'unknown',
                'confidence': 0,
                'method': 'error'
            }

    def translate_text(self, text: str, target_lang: str, source_lang: str = 'auto'):
        """Translate text to target language"""
        try:
            if source_lang == 'auto':
                # Auto-detect source language
                detected_lang, confidence = self.detect_language(text)
                source_lang = detected_lang if detected_lang != 'unknown' else 'auto'
            
            logger.info(f"🌐 Translating from {source_lang} to {target_lang}")
            
            # Validate languages
            if target_lang not in self.supported_languages:
                raise ValueError(f"Unsupported target language: {target_lang}")
            
            # Perform translation
            translator = GoogleTranslator(source=source_lang, target=target_lang)
            translated_text = translator.translate(text)
            
            return {
                'original_text': text,
                'translated_text': translated_text,
                'source_language': source_lang,
                'target_language': target_lang
            }
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            raise Exception(f"Translation failed: {str(e)}")

# Global instance
translation_service = TranslationService()