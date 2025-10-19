@echo off
echo Starting Telegram Translator Bot...
call telegram_bot_env\Scripts\activate
python -m bot.main
pause