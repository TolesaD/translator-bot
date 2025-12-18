# scripts/init_admins.py
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from bot.services.database import db_manager
from bot_config import ADMIN_IDS

def init_admins():
    """Initialize admin users from environment variable"""
    print("👑 Initializing admin users...")
    
    for admin_id in ADMIN_IDS:
        try:
            db_manager.set_admin_status(admin_id, True)
            print(f"✅ Set admin status for user {admin_id}")
        except Exception as e:
            print(f"❌ Failed to set admin for {admin_id}: {e}")
    
    print("✅ Admin initialization complete")

if __name__ == '__main__':
    init_admins()