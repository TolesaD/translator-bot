# fix_database.py
import os
import sys
import sqlite3

def update_database_schema():
    """Update existing database with new schema"""
    # Try different possible locations for the database
    possible_paths = [
        os.path.join('data', 'translator_bot.db'),
        os.path.join(os.getcwd(), 'data', 'translator_bot.db'),
        os.path.join(os.path.dirname(__file__), 'data', 'translator_bot.db'),
        'translator_bot.db'
    ]
    
    db_path = None
    for path in possible_paths:
        if os.path.exists(path):
            db_path = path
            print(f"✅ Found database at: {db_path}")
            break
    
    if not db_path:
        print("❌ Database file not found. Creating new one...")
        # Create data directory
        data_dir = os.path.join(os.getcwd(), 'data')
        os.makedirs(data_dir, exist_ok=True)
        db_path = os.path.join(data_dir, 'translator_bot.db')
        print(f"✅ Will create new database at: {db_path}")
    
    print(f"📁 Updating database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if user_preferences table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_preferences'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("❌ user_preferences table doesn't exist. Creating new tables...")
            # Create all tables from scratch
            from bot.services.database import DatabaseManager
            temp_db = DatabaseManager()
            temp_db._init_tables()
            temp_db.close()
            print("✅ Created new database with correct schema")
            return
        
        # Check if columns exist
        cursor.execute("PRAGMA table_info(user_preferences)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"📋 Existing columns: {columns}")
        
        # Add missing columns
        if 'is_admin' not in columns:
            print("➕ Adding 'is_admin' column...")
            cursor.execute("ALTER TABLE user_preferences ADD COLUMN is_admin BOOLEAN DEFAULT 0")
        
        if 'is_banned' not in columns:
            print("➕ Adding 'is_banned' column...")
            cursor.execute("ALTER TABLE user_preferences ADD COLUMN is_banned BOOLEAN DEFAULT 0")
        
        if 'channels_joined' not in columns:
            print("➕ Adding 'channels_joined' column...")
            cursor.execute("ALTER TABLE user_preferences ADD COLUMN channels_joined TEXT DEFAULT '[]'")
        
        if 'ban_reason' not in columns:
            print("➕ Adding 'ban_reason' column...")
            cursor.execute("ALTER TABLE user_preferences ADD COLUMN ban_reason TEXT")
        
        if 'ban_date' not in columns:
            print("➕ Adding 'ban_date' column...")
            cursor.execute("ALTER TABLE user_preferences ADD COLUMN ban_date TIMESTAMP")
        
        # Create admin_actions table if it doesn't exist
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
        
        # Create indexes
        print("🔧 Creating indexes...")
        
        try:
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_user_preferences_banned 
                ON user_preferences(is_banned)
            ''')
        except:
            pass
        
        try:
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_user_preferences_admin 
                ON user_preferences(is_admin)
            ''')
        except:
            pass
        
        try:
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_admin_actions_timestamp 
                ON admin_actions(timestamp DESC)
            ''')
        except:
            pass
        
        conn.commit()
        print("✅ Database schema updated successfully!")
        
    except Exception as e:
        print(f"❌ Error updating database: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        
        # Last resort: backup and create new
        print("🔄 Creating fresh database...")
        conn.close()
        if os.path.exists(db_path):
            backup_path = db_path + '.backup'
            os.rename(db_path, backup_path)
            print(f"📁 Backed up old database to: {backup_path}")
        
        # Import and create fresh
        sys.path.insert(0, os.path.dirname(__file__))
        from bot.services.database import DatabaseManager
        temp_db = DatabaseManager()
        temp_db._init_tables()
        temp_db.close()
        print("✅ Created fresh database with correct schema")
        
    finally:
        try:
            conn.close()
        except:
            pass

if __name__ == '__main__':
    update_database_schema()