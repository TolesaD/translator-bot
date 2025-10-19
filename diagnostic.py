import os
import sys
import traceback

print("=== DIAGNOSTIC REPORT ===")
print(f"Python path: {sys.executable}")
print(f"Working dir: {os.getcwd()}")
print(f"Files in current dir: {os.listdir('.')}")

if os.path.exists('bot'):
    print(f"Files in bot dir: {os.listdir('bot')}")
else:
    print("❌ bot directory not found!")

print("\nTrying to import bot.main...")
try:
    from bot.main import main
    print("✅ SUCCESS: bot.main imported!")
    print("Starting bot...")
    main()
except Exception as e:
    print(f"❌ FAILED: {e}")
    print("\nFull traceback:")
    traceback.print_exc()