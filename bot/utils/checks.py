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
            logger.info(f"🔍 Checking channel membership for user {user_id} in {announcement_channel}")
            
            # Clean channel ID (remove @ if present, add -100 for supergroups)
            channel_id = announcement_channel.replace('@', '')
            
            # Try different channel ID formats
            channel_formats = [
                channel_id,  # Original format
                f"@{channel_id}",  # With @
                f"-100{channel_id}" if channel_id.isdigit() else channel_id,  # Supergroup format
            ]
            
            member_status = None
            working_channel = None
            
            # Try each channel format
            for channel_format in channel_formats:
                try:
                    chat_member = await context.bot.get_chat_member(
                        chat_id=channel_format, 
                        user_id=user_id
                    )
                    member_status = chat_member.status
                    working_channel = channel_format
                    logger.info(f"✅ Channel check successful with format: {channel_format}")
                    break
                except Exception as format_error:
                    logger.debug(f"❌ Channel format {channel_format} failed: {format_error}")
                    continue
            
            # If we found a working channel format and user is member
            if member_status and member_status not in ['left', 'kicked', 'banned']:
                logger.info(f"✅ User {user_id} is a member of channel {working_channel} (status: {member_status})")
                return await func(update, context, *args, **kwargs)
            else:
                # User is not a member or channel not accessible
                logger.warning(f"❌ User {user_id} is not a member of channel or channel not accessible")
                
                # Create user-friendly channel link
                if announcement_channel.startswith('@'):
                    channel_link = f"https://t.me/{announcement_channel[1:]}"
                    channel_display = announcement_channel
                else:
                    channel_link = f"https://t.me/{announcement_channel}"
                    channel_display = f"@{announcement_channel}"
                
                message = (
                    f"📢 **Channel Membership Required**\n\n"
                    f"To use this bot, please join our announcement channel first:\n"
                    f"👉 [{channel_display}]({channel_link})\n\n"
                    f"*After joining, send the command again.* ✅"
                )
                
                if update.message:
                    await update.message.reply_text(
                        message, 
                        parse_mode='Markdown', 
                        disable_web_page_preview=False
                    )
                elif update.callback_query:
                    await update.callback_query.message.reply_text(
                        message, 
                        parse_mode='Markdown', 
                        disable_web_page_preview=False
                    )
                return None
                
        except Exception as e:
            logger.error(f"🚨 Channel membership check completely failed: {e}")
            
            # Provide helpful error message
            error_message = (
                "❌ **Channel verification failed**\n\n"
                "We couldn't verify your channel membership. This could be because:\n"
                "• The bot needs to be admin in the channel\n"
                "• Channel privacy settings are restricting access\n"
                "• Temporary technical issue\n\n"
                "Please contact the bot administrator for assistance."
            )
            
            if update.message:
                await update.message.reply_text(error_message, parse_mode='Markdown')
            elif update.callback_query:
                await update.callback_query.message.reply_text(error_message, parse_mode='Markdown')
            
            # Don't proceed with the command
            return None
    
    return wrapper