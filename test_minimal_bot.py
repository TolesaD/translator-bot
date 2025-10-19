import os
import sys
import logging

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Set a test bot token (you can use a real one or dummy)
os.environ['BOT_TOKEN'] = 'test_token'
os.environ['MONGODB_URI'] = 'mongodb://localhost:27017/test'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_bot_structure():
    print("Testing bot structure...")
    
    try:
        # Test if we can import the main components
        from bot.services.database import DatabaseManager
        print("✅ DatabaseManager can be imported")
        
        from bot.services.translation import TranslationService
        print("✅ TranslationService can be imported")
        
        from bot.services.speech import SpeechService
        print("✅ SpeechService can be imported")
        
        # Test speech service initialization
        speech_service = SpeechService()
        if speech_service.is_speech_available():
            print("✅ Speech recognition is available")
        else:
            print("⚠️ Speech recognition not available (this might be OK)")
            
        print("\n🎉 Basic structure test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Structure test failed: {e}")
        return False

if __name__ == '__main__':
    test_bot_structure()