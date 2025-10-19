import os
from dotenv import load_dotenv

load_dotenv()

print("Environment Variables Test:")
print(f"BOT_TOKEN: {'✅ Set' if os.getenv('BOT_TOKEN') else '❌ Missing'}")
print(f"MONGODB_URI: {'✅ Set' if os.getenv('MONGODB_URI') else '❌ Missing'}")
print(f"DEFAULT_LANGUAGE: {os.getenv('DEFAULT_LANGUAGE', 'Not set')}")
print(f"MAX_HISTORY: {os.getenv('MAX_HISTORY', 'Not set')}")

if os.getenv('BOT_TOKEN') and os.getenv('MONGODB_URI'):
    print("\n🎉 Environment variables loaded successfully!")
else:
    print("\n⚠️  Some environment variables are missing!")
    print("Please check your .env file in the root directory")