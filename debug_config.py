# debug_config.py
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

print("🔍 Debugging config module...")

# Try to import config
try:
    import config
    print(f"✅ Imported config module from: {config.__file__}")
    
    # List all attributes in config
    print("\n📋 Attributes in config module:")
    for attr in dir(config):
        if not attr.startswith('_'):
            print(f"  - {attr}")
    
    # Try to access specific attributes
    print("\n🔍 Trying to access attributes:")
    try:
        print(f"  BOT_TOKEN: {hasattr(config, 'BOT_TOKEN')}")
    except:
        print("  BOT_TOKEN: Not accessible")
    
    try:
        print(f"  ADMIN_IDS: {hasattr(config, 'ADMIN_IDS')}")
    except:
        print("  ADMIN_IDS: Not accessible")
    
    try:
        print(f"  REQUIRED_CHANNELS: {hasattr(config, 'REQUIRED_CHANNELS')}")
    except:
        print("  REQUIRED_CHANNELS: Not accessible")
        
except ImportError as e:
    print(f"❌ Cannot import config: {e}")
    
    # Try to find config.py
    config_paths = [
        'config.py',
        os.path.join(os.path.dirname(__file__), 'config.py'),
        os.path.join(os.getcwd(), 'config.py')
    ]
    
    for path in config_paths:
        if os.path.exists(path):
            print(f"📁 Found config.py at: {path}")
            with open(path, 'r') as f:
                content = f.read()
                print(f"📄 First 500 chars of config.py:\n{content[:500]}...")
            break