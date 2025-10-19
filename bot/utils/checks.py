import logging
from functools import wraps
from telegram import Update
from telegram.ext import CallbackContext

logger = logging.getLogger(__name__)

def require_channel_membership(func):
    """Decorator to check if user is member of announcement channel"""
    @wraps(func)
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        # If no announcement channel is set, skip the check
        announcement_channel = context.bot_data.get('announcement_channel')
        if not announcement_channel:
            logger.debug("No announcement channel set, skipping membership check")
            return await func(update, context, *args, **kwargs)
        
        try:
            user_id = update.effective_user.id
            
            # Log the check attempt
            logger.info(f"Checking channel membership for user {user_id} in channel {announcement_channel}")
            
            # Check if user is member of the channel
            chat_member = await context.bot.get_chat_member(
                chat_id=announcement_channel, 
                user_id=user_id
            )
            
            # Allow if user is member (any status except 'left' and 'kicked')
            if chat_member.status not in ['left', 'kicked']:
                logger.debug(f"User {user_id} is a member of channel {announcement_channel}")
                return await func(update, context, *args, **kwargs)
            else:
                # User is not a member
                logger.info(f"User {user_id} is not a member of channel {announcement_channel}")
                channel_username = announcement_channel.replace('@', '')
                message = (
                    f"📢 **Channel Membership Required**\n\n"
                    f"To use this bot, please join our announcement channel first:\n"
                    f"👉 [@{channel_username}](https://t.me/{channel_username})\n\n"
                    f"After joining, send the command again."
                )
                if update.message:
                    await update.message.reply_text(message, parse_mode='Markdown', disable_web_page_preview=True)
                elif update.callback_query:
                    await update.callback_query.message.reply_text(message, parse_mode='Markdown', disable_web_page_preview=True)
                return None  # Don't proceed with the original command
                
        except Exception as e:
            logger.error(f"Channel membership check failed: {e}")
            # If check fails (e.g., bot doesn't have access to channel), allow the command to proceed
            logger.warning(f"Allowing command due to check failure: {e}")
            return await func(update, context, *args, **kwargs)
    
    return wrapper