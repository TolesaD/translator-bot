# check_database.py
import sqlite3

db_path = 'data/translator_bot.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("📊 Tables in database:")
for table in tables:
    print(f"  - {table[0]}")

# Check user_preferences columns
cursor.execute("PRAGMA table_info(user_preferences)")
columns = cursor.fetchall()
print("\n📋 user_preferences columns:")
for col in columns:
    print(f"  - {col[1]} ({col[2]})")

# Check if channels_joined column exists (it might be missing)
column_names = [col[1] for col in columns]
if 'channels_joined' not in column_names:
    print("\n❌ 'channels_joined' column is missing! Adding it...")
    cursor.execute("ALTER TABLE user_preferences ADD COLUMN channels_joined TEXT DEFAULT '[]'")
    conn.commit()
    print("✅ Added 'channels_joined' column")

conn.close()
print("\n✅ Database check complete!")