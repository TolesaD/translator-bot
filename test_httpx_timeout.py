import httpx

# Test if we can create a Timeout with 'connect' parameter
try:
    timeout = httpx.Timeout(connect=5.0, read=5.0, write=5.0, pool=5.0)
    print("✅ httpx.Timeout with connect parameter works!")
except Exception as e:
    print(f"❌ httpx.Timeout failed: {e}")