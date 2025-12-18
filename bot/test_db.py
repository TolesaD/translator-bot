# bot/test_db.py
import os
from database import db_manager

print("🔍 Database Diagnostic")
print(f"Database path: {db_manager.db_path}")
print(f"Database exists: {os.path.exists(db_manager.db_path)}")

# Test Railway paths
print("\n📁 Checking Railway paths:")
paths_to_check = ['/data', '/app/data', '/tmp', os.path.dirname(db_manager.db_path)]
for path in paths_to_check:
    exists = os.path.exists(path)
    writable = os.access(path, os.W_OK) if exists else False
    print(f"  {path}: {'✅ Exists' if exists else '❌ Missing'} {'✅ Writable' if writable else '❌ Not writable'}")