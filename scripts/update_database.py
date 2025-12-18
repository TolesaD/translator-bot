# scripts/update_database.py
import os
import sys
import sqlite3

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def update_database_schema():
    """Update existing database with new schema"""
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    db_path = os.path.join(project_root, 'data', 'translator_bot.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return
    
    print(f"📁 Updating database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if columns exist
        cursor.execute("PRAGMA table_info(user_preferences)")
        columns = [col[1] for col in cursor.fetchall()]
        
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
        
        conn.commit()
        print("✅ Database schema updated successfully!")
        
    except Exception as e:
        print(f"❌ Error updating database: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    update_database_schema()