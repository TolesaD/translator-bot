import os
import sqlite3
import json
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SQLiteManager:
    def __init__(self):
        self.conn = None
        self.is_connected = False
        self.connect()
    
    def connect(self):
        try:
            db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'translator_bot.db')
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            self._init_tables()
            self.is_connected = True
            logger.info("✅ SQLite database connected successfully")
            
        except Exception as e:
            logger.error(f"❌ SQLite connection failed: {e}")
            self.is_connected = False
    
    def _init_tables(self):
        """Initialize database tables"""
        cursor = self.conn.cursor()
        
        # User preferences table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id INTEGER PRIMARY KEY,
                default_language TEXT DEFAULT 'en',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Translation history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS translation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                translation_data TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
    
    def get_user_preferences(self, user_id: int) -> Dict:
        if not self.is_connected:
            return {}
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                'SELECT default_language FROM user_preferences WHERE user_id = ?', 
                (user_id,)
            )
            row = cursor.fetchone()
            return {'default_language': row['default_language']} if row else {}
        except Exception as e:
            logger.error(f"Error getting user preferences: {e}")
            return {}
    
    def set_user_language(self, user_id: int, language: str):
        if not self.is_connected:
            return
        
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO user_preferences (user_id, default_language, updated_at)
                VALUES (?, ?, ?)
            ''', (user_id, language, datetime.utcnow()))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error setting user language: {e}")
    
    def add_translation_history(self, user_id: int, translation_data: Dict):
        if not self.is_connected:
            return
        
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO translation_history (user_id, translation_data)
                VALUES (?, ?)
            ''', (user_id, json.dumps(translation_data)))
            
            # Keep only last 10 entries per user
            cursor.execute('''
                DELETE FROM translation_history 
                WHERE user_id = ? AND id NOT IN (
                    SELECT id FROM translation_history 
                    WHERE user_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT 10
                )
            ''', (user_id, user_id))
            
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error adding translation history: {e}")
    
    def get_translation_history(self, user_id: int) -> List[Dict]:
        if not self.is_connected:
            return []
        
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT translation_data FROM translation_history 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 5
            ''', (user_id,))
            
            history = []
            for row in cursor.fetchall():
                try:
                    history.append(json.loads(row['translation_data']))
                except:
                    continue
            
            return history
        except Exception as e:
            logger.error(f"Error getting translation history: {e}")
            return []

# Global SQLite instance
sqlite_db = SQLiteManager()