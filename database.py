import os
import sqlite3
import json
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging
import threading

logger = logging.getLogger(__name__)

def require_connection(func):
    """Decorator to ensure database connection before executing method"""
    def wrapper(self, *args, **kwargs):
        self._ensure_connection()
        if not self.is_connected:
            logger.error(f"Cannot execute {func.__name__} - database not connected")
            # Return appropriate default value based on function
            if func.__name__.startswith('get'):
                return [] if 'List' in str(func.__annotations__.get('return', '')) else {}
            return False
        return func(self, *args, **kwargs)
    return wrapper

class DatabaseManager:
    def __init__(self):
        self.conn = None
        self.is_connected = False
        self.db_path = None
        self._lock = threading.Lock()
        self._ensure_connection()
    
    def _ensure_connection(self):
        """Ensure database connection is active"""
        if not self.is_connected or self.conn is None:
            self.connect()
        else:
            # Test if connection is still valid
            try:
                cursor = self.conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
            except (sqlite3.Error, AttributeError):
                logger.warning("⚠️ Database connection lost, reconnecting...")
                self.connect()
    
    def connect(self):
        """Connect to SQLite database with production settings"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # Use persistent path that won't reset on restart
                # On Railway, use /data directory which persists
                if os.getenv('RAILWAY_ENVIRONMENT'):
                    # Railway persistent storage
                    data_dir = '/data'
                else:
                    # Local development
                    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                    data_dir = os.path.join(project_root, 'data')
                
                os.makedirs(data_dir, exist_ok=True)
                
                self.db_path = os.path.join(data_dir, 'translator_bot.db')
                logger.info(f"📁 Database path: {self.db_path}")
                logger.info(f"📁 Database exists: {os.path.exists(self.db_path)}")
                
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
                
                # Test the connection with a simple query
                cursor = self.conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                
                self.is_connected = True
                
                # Initialize database tables
                self._init_tables()
                
                # Check if we have data
                cursor.execute("SELECT COUNT(*) as count FROM user_preferences")
                user_count = cursor.fetchone()['count']
                logger.info(f"📊 Database has {user_count} users")
                
                # Check banned users
                cursor.execute("SELECT COUNT(*) as count FROM user_preferences WHERE is_banned = 1")
                banned_count = cursor.fetchone()['count']
                logger.info(f"📊 Database has {banned_count} banned users")
                
                logger.info(f"✅ Database connected successfully (attempt {attempt + 1})")
                
                # Test the methods after connecting
                self._test_methods()
                return
                
            except sqlite3.Error as e:
                logger.error(f"❌ Database connection failed (attempt {attempt + 1}): {e}")
                
                if attempt < max_retries - 1:
                    logger.info(f"🔄 Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    
                    # Try to repair corrupted database
                    if "database is locked" in str(e) or "disk I/O error" in str(e):
                        try:
                            if self.conn:
                                self.conn.close()
                        except:
                            pass
                else:
                    # Last attempt failed, create new database
                    logger.error("🚨 All connection attempts failed, creating new database")
                    self._create_fresh_database()
        
        self.is_connected = False
    
    def _test_methods(self):
        """Test that all required methods are available"""
        required_methods = [
            'get_all_users',
            'get_user_preferences',
            'ban_user',
            'unban_user',
            'is_user_banned',
            'get_user_count',
            'get_database_stats',
            'get_banned_users'
        ]
        
        for method_name in required_methods:
            if not hasattr(self, method_name):
                logger.error(f"❌ Missing method: {method_name}")
            else:
                logger.debug(f"✅ Method available: {method_name}")
    
    def _create_fresh_database(self):
        """Create a fresh database file"""
        try:
            if self.db_path and os.path.exists(self.db_path):
                # Backup old database
                import shutil
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_path = self.db_path + f'.corrupted_{timestamp}'
                shutil.copy2(self.db_path, backup_path)
                logger.warning(f"📁 Backup created: {backup_path}")
            
            # Create new connection
            self.conn = sqlite3.connect(
                self.db_path, 
                check_same_thread=False,
                timeout=30.0
            )
            self.conn.row_factory = sqlite3.Row
            
            # Initialize tables
            self._init_tables()
            
            self.is_connected = True
            logger.info("🔄 Created fresh database")
            
        except Exception as e:
            logger.error(f"❌ Failed to create fresh database: {e}")
            self.is_connected = False
    
    def _init_tables(self):
        """Initialize database tables with proper constraints - idempotent"""
        cursor = self.conn.cursor()
        
        # User preferences table - UPDATED with channels_verified_at
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id INTEGER PRIMARY KEY,
                default_language TEXT NOT NULL DEFAULT 'en',
                is_admin BOOLEAN DEFAULT 0,
                is_banned BOOLEAN DEFAULT 0,
                channels_joined TEXT DEFAULT '[]',  -- JSON array of channel IDs user has joined
                channels_verified_at TEXT DEFAULT '{}',  -- JSON: {"@channel1": timestamp, "@channel2": timestamp}
                ban_reason TEXT,
                ban_date TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Translation history table
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
        
        # Admin actions log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER NOT NULL,
                action_type TEXT NOT NULL,
                target_user_id INTEGER,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_user_preferences_banned 
            ON user_preferences(is_banned)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_user_preferences_admin 
            ON user_preferences(is_admin)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_admin_actions_timestamp 
            ON admin_actions(timestamp DESC)
        ''')
        
        self.conn.commit()
        logger.info("Database tables verified/initialized with admin features")
    
    @require_connection
    def get_user_preferences(self, user_id: int) -> Dict:
        """Get user preferences including default language"""
        with self._lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute(
                    'SELECT default_language, is_admin, is_banned, channels_joined, channels_verified_at, created_at, updated_at, last_activity, ban_reason, ban_date FROM user_preferences WHERE user_id = ?', 
                    (user_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    channels = []
                    if row['channels_joined']:
                        try:
                            channels = json.loads(row['channels_joined'])
                        except:
                            channels = []
                    
                    timestamps = {}
                    if row['channels_verified_at']:
                        try:
                            timestamps = json.loads(row['channels_verified_at'])
                        except:
                            timestamps = {}
                    
                    return {
                        'default_language': row['default_language'],
                        'is_admin': bool(row['is_admin']),
                        'is_banned': bool(row['is_banned']),
                        'channels_joined': channels,
                        'channels_verified_at': timestamps,
                        'ban_reason': row['ban_reason'],
                        'ban_date': row['ban_date'],
                        'user_id': user_id,
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at'],
                        'last_activity': row['last_activity']
                    }
                return {}
                
            except Exception as e:
                logger.error(f"Error getting user preferences: {e}")
                return {}
    
    @require_connection
    def set_user_language(self, user_id: int, language: str):
        """Set user's default target language"""
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
    
    @require_connection
    def add_translation_history(self, user_id: int, translation_data: Dict):
        """Add translation to user's history with statistics"""
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
    
    @require_connection
    def get_translation_history(self, user_id: int, limit: int = 5) -> List[Dict]:
        """Get user's translation history"""
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
    
    @require_connection
    def get_user_stats(self, user_id: int) -> Dict:
        """Get comprehensive user statistics"""
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
    
    @require_connection
    def get_top_languages(self, user_id: int, limit: int = 5) -> List[Tuple[str, int]]:
        """Get user's most used target languages"""
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
    
    @require_connection
    def get_database_stats(self) -> Dict:
        """Get overall database statistics"""
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
                
                # Banned users count
                cursor.execute("SELECT COUNT(*) as count FROM user_preferences WHERE is_banned = 1")
                stats['banned_users'] = cursor.fetchone()['count']
                
                # Admin users count
                cursor.execute("SELECT COUNT(*) as count FROM user_preferences WHERE is_admin = 1")
                stats['admin_users'] = cursor.fetchone()['count']
                
                # Database size
                cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                stats['database_size_bytes'] = cursor.fetchone()['size']
                
                return stats
                
            except Exception as e:
                logger.error(f"Error getting database stats: {e}")
                return {}
    
    @require_connection
    def is_user_banned(self, user_id: int) -> bool:
        """Check if user is banned"""
        with self._lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute(
                    'SELECT is_banned FROM user_preferences WHERE user_id = ?', 
                    (user_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    is_banned = bool(row['is_banned'])
                    logger.info(f"🔍 Ban check for user {user_id}: {is_banned}")
                    return is_banned
                else:
                    logger.info(f"🔍 User {user_id} not found in database, not banned")
                    return False
                
            except Exception as e:
                logger.error(f"Error checking if user is banned: {e}")
                return False
    
    @require_connection
    def ban_user(self, user_id: int, admin_id: int, reason: str = "Violation of terms"):
        """Ban a user"""
        with self._lock:
            try:
                cursor = self.conn.cursor()
                
                # First check if user exists
                cursor.execute('SELECT user_id FROM user_preferences WHERE user_id = ?', (user_id,))
                user_exists = cursor.fetchone()
                
                if not user_exists:
                    # Create user record if doesn't exist
                    cursor.execute('''
                        INSERT INTO user_preferences 
                        (user_id, default_language, is_banned, ban_reason, ban_date, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (user_id, 'en', 1, reason, datetime.utcnow(), datetime.utcnow()))
                else:
                    # Update existing user
                    cursor.execute('''
                        UPDATE user_preferences 
                        SET is_banned = 1, ban_reason = ?, ban_date = ?, updated_at = ?
                        WHERE user_id = ?
                    ''', (reason, datetime.utcnow(), datetime.utcnow(), user_id))
                
                # Log admin action
                cursor.execute('''
                    INSERT INTO admin_actions 
                    (admin_id, action_type, target_user_id, details)
                    VALUES (?, ?, ?, ?)
                ''', (admin_id, 'ban', user_id, f"Reason: {reason}"))
                
                self.conn.commit()
                logger.info(f"✅ Banned user {user_id} by admin {admin_id}. Reason: {reason}")
                return True
                
            except Exception as e:
                logger.error(f"❌ Error banning user {user_id}: {e}")
                self.conn.rollback()
                return False
    
    @require_connection
    def unban_user(self, user_id: int, admin_id: int):
        """Unban a user - Enhanced with better debugging"""
        with self._lock:
            try:
                logger.info(f"🔧 DATABASE: Starting unban for user {user_id} by admin {admin_id}")
                
                cursor = self.conn.cursor()
                
                # First check if user exists
                cursor.execute(
                    'SELECT user_id, is_banned FROM user_preferences WHERE user_id = ?', 
                    (user_id,)
                )
                row = cursor.fetchone()
                
                if not row:
                    logger.error(f"❌ DATABASE: User {user_id} not found in database")
                    return False
                
                is_banned = bool(row['is_banned'])
                logger.info(f"🔧 DATABASE: Current is_banned value: {is_banned} (raw: {row['is_banned']})")
                
                if not is_banned:
                    logger.warning(f"⚠️ DATABASE: User {user_id} is not banned, nothing to do")
                    return True  # Already not banned
                
                # Perform the unban
                logger.info(f"🔧 DATABASE: Executing UPDATE for user {user_id}")
                cursor.execute('''
                    UPDATE user_preferences 
                    SET is_banned = 0, 
                        ban_reason = NULL, 
                        ban_date = NULL, 
                        updated_at = ?
                    WHERE user_id = ?
                ''', (datetime.utcnow(), user_id))
                
                updated_rows = cursor.rowcount
                logger.info(f"🔧 DATABASE: UPDATE affected {updated_rows} rows")
                
                if updated_rows == 0:
                    logger.error(f"❌ DATABASE: UPDATE affected 0 rows for user {user_id}")
                    self.conn.rollback()
                    return False
                
                # Verify the change immediately
                cursor.execute(
                    'SELECT is_banned FROM user_preferences WHERE user_id = ?', 
                    (user_id,)
                )
                verify_row = cursor.fetchone()
                
                if verify_row:
                    new_is_banned = bool(verify_row['is_banned'])
                    logger.info(f"🔧 DATABASE: After UPDATE - is_banned: {new_is_banned} (raw: {verify_row['is_banned']})")
                    
                    if not new_is_banned:
                        # Log admin action
                        cursor.execute('''
                            INSERT INTO admin_actions 
                            (admin_id, action_type, target_user_id, details)
                            VALUES (?, ?, ?, ?)
                        ''', (admin_id, 'unban', user_id, 'Unbanned via admin panel'))
                        
                        self.conn.commit()
                        logger.info(f"✅ DATABASE: Successfully unbanned user {user_id}")
                        return True
                    else:
                        logger.error(f"❌ DATABASE: Verification failed - user still marked as banned")
                        self.conn.rollback()
                        return False
                else:
                    logger.error(f"❌ DATABASE: Could not verify UPDATE - user not found after update")
                    self.conn.rollback()
                    return False
                
            except Exception as e:
                logger.error(f"❌❌ DATABASE ERROR in unban_user: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                self.conn.rollback()
                return False
    
    @require_connection
    def update_channel_membership(self, user_id: int, channel_id: str, joined: bool = True):
        """Update user's channel membership status"""
        with self._lock:
            try:
                # Special case: clear all channels
                if channel_id == "clear_all":
                    cursor = self.conn.cursor()
                    cursor.execute('''
                        UPDATE user_preferences 
                        SET channels_joined = '[]', channels_verified_at = '{}', updated_at = ?
                        WHERE user_id = ?
                    ''', (datetime.utcnow(), user_id))
                    self.conn.commit()
                    logger.info(f"Cleared all channels for user {user_id}")
                    return True
                
                # Get current channels
                cursor = self.conn.cursor()
                cursor.execute(
                    'SELECT channels_joined FROM user_preferences WHERE user_id = ?', 
                    (user_id,)
                )
                row = cursor.fetchone()
                
                channels = []
                if row and row['channels_joined']:
                    try:
                        channels = json.loads(row['channels_joined'])
                    except:
                        channels = []
                
                # Update channels list
                if joined and channel_id not in channels:
                    channels.append(channel_id)
                elif not joined and channel_id in channels:
                    channels.remove(channel_id)
                
                # Update database
                cursor.execute('''
                    INSERT OR REPLACE INTO user_preferences 
                    (user_id, channels_joined, updated_at, last_activity)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, json.dumps(channels), datetime.utcnow(), datetime.utcnow()))
                
                self.conn.commit()
                logger.debug(f"Updated channel membership for user {user_id}: {channel_id} = {joined}")
                return True
                
            except Exception as e:
                logger.error(f"Error updating channel membership: {e}")
                self.conn.rollback()
                return False
    
    @require_connection
    def update_channel_verification_timestamp(self, user_id: int, channel_id: str):
        """Update the timestamp when a channel was last verified"""
        with self._lock:
            try:
                # Get current timestamps
                cursor = self.conn.cursor()
                cursor.execute(
                    'SELECT channels_verified_at FROM user_preferences WHERE user_id = ?', 
                    (user_id,)
                )
                row = cursor.fetchone()
                
                timestamps = {}
                if row and row['channels_verified_at']:
                    try:
                        timestamps = json.loads(row['channels_verified_at'])
                    except:
                        timestamps = {}
                
                # Update timestamp for this channel
                timestamps[channel_id] = time.time()
                
                # Update database
                cursor.execute('''
                    UPDATE user_preferences 
                    SET channels_verified_at = ?, updated_at = ?
                    WHERE user_id = ?
                ''', (json.dumps(timestamps), datetime.utcnow(), user_id))
                
                self.conn.commit()
                logger.debug(f"Updated verification timestamp for user {user_id}, channel {channel_id}")
                return True
                
            except Exception as e:
                logger.error(f"Error updating verification timestamp: {e}")
                self.conn.rollback()
                return False
    
    @require_connection
    def get_channel_verification_timestamp(self, user_id: int, channel_id: str):
        """Get when a channel was last verified for a user"""
        with self._lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute(
                    'SELECT channels_verified_at FROM user_preferences WHERE user_id = ?', 
                    (user_id,)
                )
                row = cursor.fetchone()
                
                if row and row['channels_verified_at']:
                    try:
                        timestamps = json.loads(row['channels_verified_at'])
                        return timestamps.get(channel_id, 0)
                    except:
                        return 0
                return 0
                
            except Exception as e:
                logger.error(f"Error getting verification timestamp: {e}")
                return 0
    
    @require_connection
    def has_joined_required_channels(self, user_id: int, required_channels: list, max_cache_age: int = 3600) -> bool:
        """Check if user has joined all required channels, with cache expiry"""
        if not required_channels:
            return True  # No channels required
        
        with self._lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute(
                    'SELECT channels_joined, channels_verified_at FROM user_preferences WHERE user_id = ?', 
                    (user_id,)
                )
                row = cursor.fetchone()
                
                if not row or not row['channels_joined']:
                    return False
                
                # Parse user's channels
                try:
                    user_channels = json.loads(row['channels_joined'])
                except:
                    user_channels = []
                
                # Parse timestamps
                timestamps = {}
                if row['channels_verified_at']:
                    try:
                        timestamps = json.loads(row['channels_verified_at'])
                    except:
                        timestamps = {}
                
                # Check if user has joined all required channels
                required_set = set(required_channels)
                user_set = set(user_channels)
                
                if not required_set.issubset(user_set):
                    return False
                
                # Check cache expiry for each channel
                current_time = time.time()
                for channel in required_channels:
                    last_verified = timestamps.get(channel, 0)
                    cache_age = current_time - last_verified
                    
                    if cache_age > max_cache_age:
                        # Cache expired for this channel
                        logger.info(f"Cache expired for user {user_id}, channel {channel}. Age: {cache_age:.0f}s")
                        return False
                
                return True
                
            except Exception as e:
                logger.error(f"Error checking channel membership with cache: {e}")
                return False
    
    @require_connection
    def set_admin_status(self, user_id: int, is_admin: bool = True):
        """Set user as admin or remove admin status"""
        with self._lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                    UPDATE user_preferences 
                    SET is_admin = ?, updated_at = ?
                    WHERE user_id = ?
                ''', (1 if is_admin else 0, datetime.utcnow(), user_id))
                
                self.conn.commit()
                logger.info(f"Set admin status for user {user_id}: {is_admin}")
                return True
                
            except Exception as e:
                logger.error(f"Error setting admin status: {e}")
                self.conn.rollback()
                return False
    
    @require_connection
    def is_user_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        with self._lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute(
                    'SELECT is_admin FROM user_preferences WHERE user_id = ?', 
                    (user_id,)
                )
                row = cursor.fetchone()
                return bool(row and row['is_admin'])
                
            except Exception as e:
                logger.error(f"Error checking if user is admin: {e}")
                return False
    
    @require_connection
    def get_banned_users(self) -> List[Dict]:
        """Get list of all banned users"""
        with self._lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                    SELECT user_id, ban_reason, ban_date 
                    FROM user_preferences 
                    WHERE is_banned = 1
                    ORDER BY ban_date DESC
                ''')
                
                banned_users = []
                for row in cursor.fetchall():
                    banned_users.append({
                        'user_id': row['user_id'],
                        'ban_reason': row['ban_reason'],
                        'ban_date': row['ban_date']
                    })
                
                return banned_users
                
            except Exception as e:
                logger.error(f"Error getting banned users: {e}")
                return []
    
    @require_connection
    def get_all_users(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get all users with pagination"""
        with self._lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                    SELECT 
                        user_id,
                        default_language,
                        is_admin,
                        is_banned,
                        created_at,
                        last_activity,
                        (SELECT COUNT(*) FROM translation_history th WHERE th.user_id = up.user_id) as translation_count
                    FROM user_preferences up
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                ''', (limit, offset))
                
                users = []
                for row in cursor.fetchall():
                    users.append({
                        'user_id': row['user_id'],
                        'default_language': row['default_language'],
                        'is_admin': bool(row['is_admin']),
                        'is_banned': bool(row['is_banned']),
                        'created_at': row['created_at'],
                        'last_activity': row['last_activity'],
                        'translation_count': row['translation_count']
                    })
                
                return users
                
            except Exception as e:
                logger.error(f"Error getting all users: {e}")
                return []
    
    @require_connection
    def get_user_count(self) -> int:
        """Get total number of users"""
        with self._lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('SELECT COUNT(*) as count FROM user_preferences')
                return cursor.fetchone()['count']
                
            except Exception as e:
                logger.error(f"Error getting user count: {e}")
                return 0
    
    @require_connection
    def get_daily_stats(self, days: int = 7) -> List[Dict]:
        """Get daily statistics for the last N days"""
        with self._lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                    SELECT 
                        DATE(timestamp) as date,
                        COUNT(*) as translation_count,
                        COUNT(DISTINCT user_id) as user_count,
                        SUM(word_count) as total_words
                    FROM translation_history 
                    WHERE timestamp >= date('now', ?)
                    GROUP BY DATE(timestamp)
                    ORDER BY date DESC
                ''', (f'-{days} days',))
                
                stats = []
                for row in cursor.fetchall():
                    stats.append({
                        'date': row['date'],
                        'translation_count': row['translation_count'],
                        'user_count': row['user_count'],
                        'total_words': row['total_words']
                    })
                
                return stats
                
            except Exception as e:
                logger.error(f"Error getting daily stats: {e}")
                return []
    
    @require_connection
    def cleanup_old_data(self, days_old: int = 90):
        """Clean up translation history older than specified days"""
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
    
    @require_connection
    def backup_database(self, backup_path: str = None) -> bool:
        """Create a backup of the database"""
        try:
            if not backup_path:
                # Create backup directory
                if os.getenv('RAILWAY_ENVIRONMENT'):
                    backup_dir = '/data/backups'
                else:
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