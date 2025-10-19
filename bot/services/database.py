import os
from typing import Dict, List, Optional
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ConfigurationError, ServerSelectionTimeoutError
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.client = None
        self.db = None
        self.is_connected = False
        self.connect()
    
    def connect(self):
        try:
            mongodb_uri = os.getenv('MONGODB_URI')
            
            if not mongodb_uri:
                logger.warning("MONGODB_URI not found in environment variables")
                return
            
            logger.info("🔐 Attempting MongoDB connection...")
            
            # Remove any existing SSL/TLS parameters from the URI and use simple connection
            # MongoDB Atlas requires TLS, but let's handle it differently
            clean_uri = mongodb_uri
            
            # Try with very simple connection parameters
            self.client = MongoClient(
                clean_uri,
                serverSelectionTimeoutMS=10000,
                connectTimeoutMS=15000,
                socketTimeoutMS=30000,
                retryWrites=True,
                maxPoolSize=10
            )
            
            # Test the connection
            self.client.admin.command('ping')
            self.db = self.client.get_database()
            self.is_connected = True
            
            logger.info("✅ MongoDB connected successfully")
                
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            logger.warning("The bot will run without database features")
            self.is_connected = False
    
    def get_user_preferences(self, user_id: int) -> Dict:
        """Get user preferences including default language"""
        if not self.is_connected:
            return {}
        
        try:
            return self.db.user_preferences.find_one({"user_id": user_id}) or {}
        except Exception as e:
            logger.error(f"Error getting user preferences: {e}")
            return {}
    
    def set_user_language(self, user_id: int, language: str):
        """Set user's default target language"""
        if not self.is_connected:
            logger.warning("Cannot set user language - database not connected")
            return
        
        try:
            self.db.user_preferences.update_one(
                {"user_id": user_id},
                {"$set": {"default_language": language, "user_id": user_id}},
                upsert=True
            )
            logger.debug(f"Set language for user {user_id}: {language}")
        except Exception as e:
            logger.error(f"Error setting user language: {e}")
    
    def add_translation_history(self, user_id: int, translation_data: Dict):
        """Add translation to user's history"""
        if not self.is_connected:
            return
        
        try:
            max_history = int(os.getenv('MAX_HISTORY', 10))
            
            # Add timestamp if not present
            if 'timestamp' not in translation_data:
                from datetime import datetime
                translation_data['timestamp'] = datetime.utcnow()
            
            # Push new translation and maintain only latest N entries
            self.db.translation_history.update_one(
                {"user_id": user_id},
                {
                    "$push": {
                        "translations": {
                            "$each": [translation_data],
                            "$slice": -max_history
                        }
                    }
                },
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error adding translation history: {e}")
    
    def get_translation_history(self, user_id: int) -> List[Dict]:
        """Get user's translation history"""
        if not self.is_connected:
            return []
        
        try:
            result = self.db.translation_history.find_one({"user_id": user_id})
            return result.get('translations', []) if result else []
        except Exception as e:
            logger.error(f"Error getting translation history: {e}")
            return []
    
    def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

# Global database instance
db_manager = DatabaseManager()