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
            # Configure recognizer settings
            self.recognizer.energy_threshold = 300
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.8
            logger.info("✅ SpeechRecognition initialized successfully")
        except ImportError as e:
            logger.warning(f"❌ SpeechRecognition not available: {e}")
            self.recognizer = None
        except Exception as e:
            logger.error(f"❌ SpeechRecognition initialization failed: {e}")
            self.recognizer = None
    
    def voice_to_text(self, voice_file_path: str) -> str:
        """Convert voice message to text"""
        if not self.recognizer:
            raise Exception("Speech recognition is not available. Please install SpeechRecognition package.")
        
        try:
            import speech_recognition as sr
            from pydub import AudioSegment
            
            logger.info(f"Processing voice file: {voice_file_path}")
            
            # Check if file exists and has content
            if not os.path.exists(voice_file_path):
                raise Exception("Voice file does not exist")
            
            file_size = os.path.getsize(voice_file_path)
            if file_size == 0:
                raise Exception("Voice file is empty")
            
            logger.info(f"Voice file size: {file_size} bytes")
            
            # Convert OGG to WAV for better recognition
            logger.info("Converting OGG to WAV...")
            try:
                audio = AudioSegment.from_ogg(voice_file_path)
                wav_data = io.BytesIO()
                audio.export(wav_data, format="wav")
                wav_data.seek(0)
                logger.info("OGG to WAV conversion successful")
            except Exception as e:
                logger.error(f"OGG to WAV conversion failed: {e}")
                # Try direct processing as fallback
                wav_data = None
            
            # Recognize speech
            logger.info("Recognizing speech...")
            try:
                if wav_data:
                    # Use converted WAV data
                    with sr.AudioFile(wav_data) as source:
                        # Adjust for ambient noise
                        self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                        audio_data = self.recognizer.record(source)
                else:
                    # Try direct OGG processing (may not work)
                    with sr.AudioFile(voice_file_path) as source:
                        self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                        audio_data = self.recognizer.record(source)
                
                # Use Google Speech Recognition
                text = self.recognizer.recognize_google(audio_data)
                logger.info(f"Speech recognition successful: {text}")
                return text
                
            except sr.UnknownValueError:
                logger.error("Google Speech Recognition could not understand audio")
                raise Exception("Could not understand the audio. Please try again with clearer speech.")
            except sr.RequestError as e:
                logger.error(f"Google Speech Recognition request failed: {e}")
                raise Exception("Speech recognition service is unavailable. Please try again later.")
            except Exception as e:
                logger.error(f"Speech recognition failed: {e}")
                raise Exception(f"Speech recognition failed: {str(e)}")
                
        except ImportError as e:
            raise Exception(f"Required package not available: {e}")
        except Exception as e:
            logger.error(f"Voice to text conversion failed: {e}")
            raise Exception(f"Could not process voice message: {str(e)}")
    
    def text_to_speech(self, text: str, language: str) -> str:
        """Convert text to speech and return file path"""
        try:
            logger.info(f"Converting text to speech in {language}: {text[:50]}...")
            
            # Validate language code
            if not language or len(language) != 2:
                language = 'en'  # Default to English
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            temp_path = temp_file.name
            temp_file.close()
            
            # Generate speech using gTTS
            tts = gTTS(text=text, lang=language, slow=False)
            tts.save(temp_path)
            
            # Verify file was created
            if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                logger.info(f"Text-to-speech saved successfully: {temp_path}")
                return temp_path
            else:
                raise Exception("Generated audio file is empty")
                
        except Exception as e:
            logger.error(f"Text to speech conversion failed: {e}")
            raise Exception(f"Could not generate audio: {str(e)}")
    
    def cleanup_file(self, file_path: str):
        """Clean up temporary files"""
        try:
            if file_path and os.path.exists(file_path):
                os.unlink(file_path)
                logger.debug(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            logger.warning(f"Could not delete file {file_path}: {e}")
    
    def is_speech_available(self) -> bool:
        """Check if speech recognition is available"""
        return self.recognizer is not None

# Global speech service instance
speech_service = SpeechService()