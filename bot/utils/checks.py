import logging
import os
from functools import wraps
from telegram import Update
from telegram.ext import CallbackContext

logger = logging.getLogger(__name__)

def require_channel_membership(func):
    """Decorator to check if user is member of announcement channel"""
    @wraps(func)
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        # Get channel from multiple sources in priority order
        announcement_channel = None
        
        # 1. Try bot_data first
        announcement_channel = context.bot_data.get('announcement_channel')
        source = "bot_data"
        
        # 2. If not in bot_data, try environment variable directly
        if not announcement_channel:
            announcement_channel = os.getenv('ANNOUNCEMENT_CHANNEL')
            source = "environment"
        
        # DEBUG: Log what we found
        logger.info(f"🔍 CHANNEL CHECK - Source: {source}, Channel: {announcement_channel}")
        logger.info(f"🔍 CHANNEL CHECK - User: {update.effective_user.id}, Command: {update.message.text if update.message else 'N/A'}")
        
        if not announcement_channel:
            logger.warning("🚨 CHANNEL CHECK - No announcement channel found anywhere, skipping check")
            return await func(update, context, *args, **kwargs)
        
        # Ensure consistent format
        if announcement_channel and not announcement_channel.startswith('@'):
            announcement_channel = f"@{announcement_channel}"
            logger.info(f"🔍 CHANNEL CHECK - Formatted channel: {announcement_channel}")
        
        try:
            user_id = update.effective_user.id
            
            # Try channel access
            logger.info(f"🔍 Attempting membership check for user {user_id} in {announcement_channel}")
            
            chat_member = await context.bot.get_chat_member(
                chat_id=announcement_channel, 
                user_id=user_id
            )
            
            member_status = chat_member.status
            logger.info(f"🔍 Membership status for user {user_id}: {member_status}")
            
            # Allow if user is member (any status except 'left' and 'kicked')
            if member_status not in ['left', 'kicked', 'banned']:
                logger.info(f"✅ User {user_id} is a member of channel {announcement_channel}")
                return await func(update, context, *args, **kwargs)
            else:
                # User is not a member
                logger.warning(f"❌ User {user_id} is NOT a member of channel {announcement_channel}. Status: {member_status}")
                
                # Create user-friendly channel link
                channel_username = announcement_channel.replace('@', '')
                message = (
                    f"📢 **Channel Membership Required**\n\n"
                    f"To use this bot, please join our announcement channel first:\n"
                    f"👉 [@{channel_username}](https://t.me/{channel_username})\n\n"
                    f"*After joining, send the command again.* ✅"
                )
                
                if update.message:
                    await update.message.reply_text(message, parse_mode='Markdown', disable_web_page_preview=False)
                elif update.callback_query:
                    await update.callback_query.message.reply_text(message, parse_mode='Markdown', disable_web_page_preview=False)
                
                return None  # Block the command
                
        except Exception as e:
            logger.error(f"🚨 Channel membership check failed: {e}")
            
            # Provide helpful error message
            error_message = (
                f"❌ **Channel Verification Failed**\n\n"
                f"We couldn't verify your membership in @LanguagesTranslator.\n\n"
                f"Please:\n"
                f"1. Join [@LanguagesTranslator](https://t.me/LanguagesTranslator)\n"
                f"2. Try the command again\n\n"
                f"If you've already joined, this might be a temporary issue."
            )
            
            if update.message:
                await update.message.reply_text(error_message, parse_mode='Markdown', disable_web_page_preview=False)
            elif update.callback_query:
                await update.callback_query.message.reply_text(error_message, parse_mode='Markdown', disable_web_page_preview=False)
            
            return None  # Block the command when check fails
    
    return wrapper