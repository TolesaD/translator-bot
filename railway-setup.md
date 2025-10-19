# Railway Setup Instructions

Since Railway environment variables aren't working, we'll use a file-based approach:

1. **Add this build command in Railway:**
   - Go to your Railway service → Settings → Build Command
   - Add: `echo "7747855846:AAFWjqqZXNBpwFFjrAQi3fjT5qwBbjcJCNs" > /app/bot_token.txt`

2. **Or create a startup script:**
   Create `start.sh`:
   ```bash
   #!/bin/bash
   echo "$BOT_TOKEN" > /app/bot_token.txt
   python main.py