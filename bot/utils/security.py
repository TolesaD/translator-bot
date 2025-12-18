import logging
from functools import wraps
from telegram import Update
from telegram.ext import CallbackContext
from database import db_manager

logger = logging.getLogger(__name__)

def require_unbanned_user(func):
    """Decorator to check if user is not banned"""
    @wraps(func)
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        user_id = update.effective_user.id
        
        # Check if user is banned
        if db_manager.is_user_banned(user_id):
            logger.warning(f"🚫 Banned user {user_id} tried to use function: {func.__name__}")
            
            # Send banned message if possible
            if hasattr(update, 'message') and update.message:
                from bot.utils.checks import _send_banned_message
                await _send_banned_message(update, context)
            elif hasattr(update, 'callback_query') and update.callback_query:
                from bot.utils.checks import _send_banned_message
                await _send_banned_message(update, context)
            
            return None  # Block the function
        
        return await func(update, context, *args, **kwargs)
    
    return wrapper