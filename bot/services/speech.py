import os
import tempfile
import logging
from gtts import gTTS
import io

logger = logging.getLogger(__name__)

class SpeechService:
    def __init__(self):
        self.recognizer = None
        self._initialize_recognizer()
    
    def _initialize_recognizer(self):
        """Initialize speech recognition with error handling"""
        try:
            import speech_recognition as sr
            self.recognizer = sr.Recognizer()
            logger.info("✅ SpeechRecognition initialized successfully")
        except ImportError as e:
            logger.warning(f"❌ SpeechRecognition not available: {e}")
            self.recognizer = None
    
    def voice_to_text(self, voice_file_path: str) -> str:
        """Convert voice message to text"""
        if not self.recognizer:
            raise Exception("Speech recognition is not available. Please install SpeechRecognition package.")
        
        try:
            import speech_recognition as sr
            from pydub import AudioSegment
            
            # Convert OGG to WAV for better recognition
            logger.info("Converting OGG to WAV...")
            audio = AudioSegment.from_ogg(voice_file_path)
            wav_data = io.BytesIO()
            audio.export(wav_data, format="wav")
            wav_data.seek(0)
            
            # Recognize speech
            logger.info("Recognizing speech...")
            with sr.AudioFile(wav_data) as source:
                audio_data = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio_data)
                logger.info(f"Recognized text: {text}")
                return text
                
        except ImportError as e:
            raise Exception(f"Required package not available: {e}")
        except Exception as e:
            logger.error(f"Voice to text conversion failed: {e}")
            raise Exception(f"Could not process voice message: {str(e)}")
    
    def text_to_speech(self, text: str, language: str) -> str:
        """Convert text to speech and return file path"""
        try:
            logger.info(f"Converting text to speech in {language}...")
            tts = gTTS(text=text, lang=language, slow=False)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                tts.save(temp_file.name)
                return temp_file.name
                
        except Exception as e:
            logger.error(f"Text to speech conversion failed: {e}")
            raise
    
    def cleanup_file(self, file_path: str):
        """Clean up temporary files"""
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except Exception as e:
            logger.warning(f"Could not delete file {file_path}: {e}")
    
    def is_speech_available(self) -> bool:
        """Check if speech recognition is available"""
        return self.recognizer is not None

# Global speech service instance
speech_service = SpeechService()