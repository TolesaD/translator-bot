# check_consistency.py
import sys
import os

def check_imports():
    """Check for inconsistent database imports"""
    print("🔍 Checking database imports...")
    
    files_to_check = [
        'bot/handlers/inline_handler.py',
        'bot/utils/checks.py',
        'bot/handlers/admin_handlers.py',
        'bot/handlers/translation_handler.py',
        'main.py'
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
                if 'bot.services.database' in content:
                    print(f"❌ {file_path}: Uses old database import")
                elif 'bot.database' in content:
                    print(f"✅ {file_path}: Uses new database import")
                elif 'database' in content:
                    print(f"⚠️  {file_path}: Might need checking")

if __name__ == '__main__':
    check_imports()