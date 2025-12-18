# cleanup_cache.py
import os
import shutil
import glob

print("🧹 Cleaning Python cache...")

# Remove .pyc files
pyc_files = glob.glob('**/*.pyc', recursive=True)
for f in pyc_files:
    try:
        os.remove(f)
        print(f"🗑️  Removed: {f}")
    except:
        pass

# Remove __pycache__ directories
cache_dirs = glob.glob('**/__pycache__', recursive=True)
for d in cache_dirs:
    try:
        shutil.rmtree(d)
        print(f"🗑️  Removed: {d}")
    except:
        pass

print("✅ Cache cleaned!")