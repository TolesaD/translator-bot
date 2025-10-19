import os
import sqlite3
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging
import threading

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.conn = None
        self.is_connected = False
        self.db_path = None
        self._lock = threading.Lock()
        self.connect()
    
    def connect(self):
        """Connect to SQLite database with production settings"""
        try:
            # Create data directory in the project root
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            data_dir = os.path.join(project_root, 'data')
            os.makedirs(data_dir, exist_ok=True)
            
            self.db_path = os.path.join(data_dir, 'translator_bot.db')
            logger.info(f"📁 Database path: {self.db_path}")
            
            # Connect to SQLite database with production settings
            self.conn = sqlite3.connect(
                self.db_path, 
                check_same_thread=False,
                timeout=30.0,
                detect_types=sqlite3.PARSE_DECLTYPES
            )
            self.conn.row_factory = sqlite3.Row
            self.conn.execute("PRAGMA journal_mode=WAL")
            self.conn.execute("PRAGMA synchronous=NORMAL")
            self.conn.execute("PRAGMA cache_size=-64000")
            self.conn.execute("PRAGMA busy_timeout=5000")
            
            self.is_connected = True
            
            # Initialize database tables
            self._init_tables()
            
            logger.info("✅ SQLite database connected successfully")
            
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            self.is_connected = False
    
    def _init_tables(self):
        """Initialize database tables with proper constraints - idempotent"""
        cursor = self.conn.cursor()
        
        # User preferences table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id INTEGER PRIMARY KEY,
                default_language TEXT NOT NULL DEFAULT 'en',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Translation history table - NO FOREIGN KEY constraint
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS translation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                original_text TEXT NOT NULL,
                translated_text TEXT NOT NULL,
                source_language TEXT NOT NULL DEFAULT 'auto',
                target_language TEXT NOT NULL DEFAULT 'en',
                translation_type TEXT NOT NULL DEFAULT 'text',
                word_count INTEGER DEFAULT 0,
                character_count INTEGER DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # User statistics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_statistics (
                user_id INTEGER PRIMARY KEY,
                total_translations INTEGER DEFAULT 0,
                total_words INTEGER DEFAULT 0,
                total_characters INTEGER DEFAULT 0,
                favorite_target_language TEXT DEFAULT 'en',
                last_translation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_translation_history_user_id 
            ON translation_history(user_id)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_translation_history_timestamp 
            ON translation_history(timestamp DESC)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_translation_history_type 
            ON translation_history(translation_type)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_user_preferences_activity 
            ON user_preferences(last_activity DESC)
        ''')
        
        self.conn.commit()
        logger.info("Database tables verified/initialized")
    
    def get_user_preferences(self, user_id: int) -> Dict:
        """Get user preferences including default language"""
        if not self.is_connected:
            return {}
        
        with self._lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute(
                    'SELECT default_language, created_at, updated_at, last_activity FROM user_preferences WHERE user_id = ?', 
                    (user_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    return {
                        'default_language': row['default_language'],
                        'user_id': user_id,
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at'],
                        'last_activity': row['last_activity']
                    }
                return {}
                
            except Exception as e:
                logger.error(f"Error getting user preferences: {e}")
                return {}
    
    def set_user_language(self, user_id: int, language: str):
        """Set user's default target language"""
        if not self.is_connected:
            logger.warning("Cannot set user language - database not connected")
            return
        
        with self._lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO user_preferences 
                    (user_id, default_language, updated_at, last_activity)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, language, datetime.utcnow(), datetime.utcnow()))
                
                self.conn.commit()
                logger.debug(f"Set language for user {user_id}: {language}")
                
            except Exception as e:
                logger.error(f"Error setting user language: {e}")
                self.conn.rollback()
    
    def add_translation_history(self, user_id: int, translation_data: Dict):
        """Add translation to user's history with statistics"""
        if not self.is_connected:
            return
        
        with self._lock:
            try:
                cursor = self.conn.cursor()
                
                # Extract data from translation result
                original_text = translation_data.get('original_text', '')
                translated_text = translation_data.get('translated_text', '')
                source_language = translation_data.get('source_language', 'auto')
                target_language = translation_data.get('target_language', 'en')
                translation_type = translation_data.get('translation_type', 'text')
                
                # Calculate statistics
                word_count = len(original_text.split())
                character_count = len(original_text)
                
                # Ensure user exists in preferences
                cursor.execute('''
                    INSERT OR IGNORE INTO user_preferences 
                    (user_id, default_language, last_activity)
                    VALUES (?, ?, ?)
                ''', (user_id, target_language, datetime.utcnow()))
                
                # Add the translation history
                cursor.execute('''
                    INSERT INTO translation_history 
                    (user_id, original_text, translated_text, source_language, 
                     target_language, translation_type, word_count, character_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, original_text[:1000], translated_text[:1000], 
                      source_language, target_language, translation_type, 
                      word_count, character_count))
                
                self.conn.commit()
                logger.debug(f"Added translation history for user {user_id}, type: {translation_type}")
                
            except Exception as e:
                logger.error(f"Error adding translation history: {e}")
                self.conn.rollback()
    
    def get_translation_history(self, user_id: int, limit: int = 5) -> List[Dict]:
        """Get user's translation history"""
        if not self.is_connected:
            return []
        
        with self._lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                    SELECT 
                        original_text, 
                        translated_text, 
                        source_language, 
                        target_language,
                        translation_type,
                        timestamp,
                        word_count
                    FROM translation_history 
                    WHERE user_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (user_id, limit))
                
                history = []
                for row in cursor.fetchall():
                    history.append({
                        'original_text': row['original_text'],
                        'translated_text': row['translated_text'],
                        'source_language': row['source_language'],
                        'target_language': row['target_language'],
                        'translation_type': row['translation_type'],
                        'timestamp': row['timestamp'],
                        'word_count': row['word_count']
                    })
                
                return history
                
            except Exception as e:
                logger.error(f"Error getting translation history: {e}")
                return []
    
    def get_user_stats(self, user_id: int) -> Dict:
        """Get comprehensive user statistics"""
        if not self.is_connected:
            return {}
        
        with self._lock:
            try:
                cursor = self.conn.cursor()
                
                # Get basic stats
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_translations,
                        COALESCE(SUM(word_count), 0) as total_words,
                        COALESCE(SUM(character_count), 0) as total_characters,
                        MAX(timestamp) as last_translation
                    FROM translation_history 
                    WHERE user_id = ?
                ''', (user_id,))
                
                stats_row = cursor.fetchone()
                
                if stats_row and stats_row['total_translations'] > 0:
                    # Get favorite language
                    cursor.execute('''
                        SELECT target_language, COUNT(*) as count
                        FROM translation_history 
                        WHERE user_id = ?
                        GROUP BY target_language 
                        ORDER BY count DESC 
                        LIMIT 1
                    ''', (user_id,))
                    
                    fav_lang_row = cursor.fetchone()
                    favorite_language = fav_lang_row['target_language'] if fav_lang_row else 'en'
                    
                    # Get active days
                    cursor.execute('''
                        SELECT COUNT(DISTINCT DATE(timestamp)) as active_days,
                               MIN(timestamp) as first_translation
                        FROM translation_history 
                        WHERE user_id = ?
                    ''', (user_id,))
                    
                    additional_stats = cursor.fetchone()
                    
                    return {
                        'total_translations': stats_row['total_translations'],
                        'total_words': stats_row['total_words'],
                        'total_characters': stats_row['total_characters'],
                        'favorite_language': favorite_language,
                        'last_translation': stats_row['last_translation'],
                        'active_days': additional_stats['active_days'] if additional_stats else 1,
                        'first_translation': additional_stats['first_translation'] if additional_stats else stats_row['last_translation']
                    }
                
                return {}
                
            except Exception as e:
                logger.error(f"Error getting user stats: {e}")
                return {}
    
    def get_top_languages(self, user_id: int, limit: int = 5) -> List[Tuple[str, int]]:
        """Get user's most used target languages"""
        if not self.is_connected:
            return []
        
        with self._lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                    SELECT target_language, COUNT(*) as count
                    FROM translation_history 
                    WHERE user_id = ?
                    GROUP BY target_language 
                    ORDER BY count DESC 
                    LIMIT ?
                ''', (user_id, limit))
                
                return [(row['target_language'], row['count']) for row in cursor.fetchall()]
                
            except Exception as e:
                logger.error(f"Error getting top languages: {e}")
                return []
    
    def get_database_stats(self) -> Dict:
        """Get overall database statistics"""
        if not self.is_connected:
            return {}
        
        with self._lock:
            try:
                cursor = self.conn.cursor()
                
                stats = {}
                
                # Table counts
                cursor.execute("SELECT COUNT(*) as count FROM user_preferences")
                stats['total_users'] = cursor.fetchone()['count']
                
                cursor.execute("SELECT COUNT(*) as count FROM translation_history")
                stats['total_translations'] = cursor.fetchone()['count']
                
                cursor.execute("SELECT COALESCE(SUM(word_count), 0) as words FROM translation_history")
                stats['total_words'] = cursor.fetchone()['words']
                
                # Database size
                cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                stats['database_size_bytes'] = cursor.fetchone()['size']
                
                return stats
                
            except Exception as e:
                logger.error(f"Error getting database stats: {e}")
                return {}
    
    def cleanup_old_data(self, days_old: int = 90):
        """Clean up translation history older than specified days"""
        if not self.is_connected:
            return
        
        with self._lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                    DELETE FROM translation_history 
                    WHERE timestamp < datetime('now', ?)
                ''', (f'-{days_old} days',))
                
                deleted_count = cursor.rowcount
                self.conn.commit()
                
                logger.info(f"Cleaned up {deleted_count} translation records older than {days_old} days")
                
            except Exception as e:
                logger.error(f"Error cleaning up old data: {e}")
                self.conn.rollback()
    
    def backup_database(self, backup_path: str = None) -> bool:
        """Create a backup of the database"""
        if not self.is_connected:
            return False
        
        try:
            if not backup_path:
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                backup_dir = os.path.join(project_root, 'backups')
                os.makedirs(backup_dir, exist_ok=True)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_path = os.path.join(backup_dir, f'translator_backup_{timestamp}.db')
            
            with self._lock:
                backup_conn = sqlite3.connect(backup_path)
                with backup_conn:
                    self.conn.backup(backup_conn, pages=100, sleep=0.1)
                backup_conn.close()
            
            logger.info(f"Database backup created: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating database backup: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

# Global database instance
db_manager = DatabaseManager()