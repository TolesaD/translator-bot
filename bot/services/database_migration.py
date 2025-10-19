import os
import sqlite3
import logging

logger = logging.getLogger(__name__)

def migrate_database():
    """Migrate database to latest schema"""
    try:
        # Get database path
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        data_dir = os.path.join(project_root, 'data')
        db_path = os.path.join(data_dir, 'translator_bot.db')
        
        if not os.path.exists(db_path):
            logger.info("No existing database found, fresh installation")
            return True
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if migration is needed
        cursor.execute("PRAGMA table_info(user_preferences)")
        columns = [column[1] for column in cursor.fetchall()]
        
        migrations_applied = 0
        
        # Migration 1: Add last_activity column to user_preferences
        if 'last_activity' not in columns:
            logger.info("Applying migration: Add last_activity column")
            cursor.execute('''
                ALTER TABLE user_preferences 
                ADD COLUMN last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ''')
            migrations_applied += 1
        
        # Migration 2: Check user_statistics table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_statistics'")
        if not cursor.fetchone():
            logger.info("Applying migration: Create user_statistics table")
            cursor.execute('''
                CREATE TABLE user_statistics (
                    user_id INTEGER PRIMARY KEY,
                    total_translations INTEGER DEFAULT 0,
                    total_words INTEGER DEFAULT 0,
                    total_characters INTEGER DEFAULT 0,
                    favorite_target_language TEXT DEFAULT 'en',
                    last_translation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            migrations_applied += 1
        
        # Migration 3: Check translation_history has new columns
        cursor.execute("PRAGMA table_info(translation_history)")
        history_columns = [column[1] for column in cursor.fetchall()]
        
        if 'translation_type' not in history_columns:
            logger.info("Applying migration: Add translation_type to translation_history")
            cursor.execute('''
                ALTER TABLE translation_history 
                ADD COLUMN translation_type TEXT NOT NULL DEFAULT 'text'
            ''')
            migrations_applied += 1
        
        if 'word_count' not in history_columns:
            logger.info("Applying migration: Add word_count to translation_history")
            cursor.execute('''
                ALTER TABLE translation_history 
                ADD COLUMN word_count INTEGER DEFAULT 0
            ''')
            migrations_applied += 1
        
        if 'character_count' not in history_columns:
            logger.info("Applying migration: Add character_count to translation_history")
            cursor.execute('''
                ALTER TABLE translation_history 
                ADD COLUMN character_count INTEGER DEFAULT 0
            ''')
            migrations_applied += 1
        
        # Migration 4: Create indexes if they don't exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_user_preferences_activity'")
        if not cursor.fetchone():
            logger.info("Applying migration: Create activity index")
            cursor.execute('''
                CREATE INDEX idx_user_preferences_activity 
                ON user_preferences(last_activity DESC)
            ''')
            migrations_applied += 1
        
        conn.commit()
        conn.close()
        
        if migrations_applied > 0:
            logger.info(f"Applied {migrations_applied} database migrations successfully")
        else:
            logger.info("Database is already up to date")
        
        return True
        
    except Exception as e:
        logger.error(f"Database migration failed: {e}")
        return False

def backup_and_reset_database():
    """Create backup and reset database (nuclear option)"""
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        data_dir = os.path.join(project_root, 'data')
        db_path = os.path.join(data_dir, 'translator_bot.db')
        backup_dir = os.path.join(project_root, 'backups')
        
        if os.path.exists(db_path):
            # Create backup
            os.makedirs(backup_dir, exist_ok=True)
            import datetime
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(backup_dir, f'pre_migration_backup_{timestamp}.db')
            
            import shutil
            shutil.copy2(db_path, backup_path)
            logger.info(f"Created backup at: {backup_path}")
            
            # Remove old database
            os.remove(db_path)
            logger.info("Removed old database file")
        
        return True
        
    except Exception as e:
        logger.error(f"Database reset failed: {e}")
        return False