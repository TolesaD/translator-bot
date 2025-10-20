#!/usr/bin/env python3
"""
Verify Railway Variables
"""
import os

print("🔍 Checking Railway Configuration...")
print("=" * 50)

# Check if we're on Railway
is_railway = bool(os.getenv('RAILWAY_PROJECT_ID'))
print(f"Running on Railway: {is_railway}")

# Check BOT_TOKEN
bot_token = os.getenv('BOT_TOKEN')
if bot_token:
    print(f"✅ BOT_TOKEN FOUND (Service Level)")
    print(f"   Length: {len(bot_token)}")
    print(f"   Preview: {bot_token[:10]}...{bot_token[-5:]}")
else:
    print("❌ BOT_TOKEN NOT FOUND")
    print("💡 Please add BOT_TOKEN to SERVICE level variables")

# Show Railway-specific environment vars
print("\n📋 Railway Environment Variables:")
railway_vars = {k: v for k, v in os.environ.items() if 'RAILWAY' in k}
for key, value in sorted(railway_vars.items()):
    print(f"   {key}: {value}")

print("=" * 50)

if bot_token:
    # Import and run your bot
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from bot.main import main as bot_main
    bot_main()
else:
    print("❌ Cannot start without BOT_TOKEN")
    exit(1)