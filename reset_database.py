import os
import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_database():
    """Completely reset the database with correct schema"""
    try:
        # Get database path
        project_root = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(project_root, 'data')
        db_path = os.path.join(data_dir, 'translator_bot.db')
        
        # Remove old database if exists
        if os.path.exists(db_path):
            # Create backup
            backup_dir = os.path.join(project_root, 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            import datetime
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(backup_dir, f'pre_reset_backup_{timestamp}.db')
            
            import shutil
            shutil.copy2(db_path, backup_path)
            logger.info(f"Backup created: {backup_path}")
            
            os.remove(db_path)
            logger.info("Old database removed")
        
        # Create new database with correct schema
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE user_preferences (
                user_id INTEGER PRIMARY KEY,
                default_language TEXT NOT NULL DEFAULT 'en',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE translation_history (
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
        
        # Create indexes
        cursor.execute('CREATE INDEX idx_translation_history_user_id ON translation_history(user_id)')
        cursor.execute('CREATE INDEX idx_translation_history_timestamp ON translation_history(timestamp DESC)')
        cursor.execute('CREATE INDEX idx_translation_history_type ON translation_history(translation_type)')
        cursor.execute('CREATE INDEX idx_user_preferences_activity ON user_preferences(last_activity DESC)')
        
        conn.commit()
        conn.close()
        
        logger.info("✅ Database reset successfully with correct schema")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to reset database: {e}")
        return False

if __name__ == "__main__":
    if reset_database():
        print("✅ Database reset complete! Restart your bot.")
    else:
        print("❌ Database reset failed.")