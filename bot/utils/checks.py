import logging
import os
import json
import time
from functools import wraps
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from database import db_manager

logger = logging.getLogger(__name__)

# Cache settings
CHANNEL_CACHE_EXPIRY = 3600  # 1 hour in seconds
FORCE_RECHECK_INTERVAL = 86400  # 24 hours in seconds

def get_required_channels():
    """Get required channels directly from environment"""
    channels_str = os.getenv('REQUIRED_CHANNELS', '@LanguagesTranslator,@Botomics')
    logger.info(f"🔍 Raw REQUIRED_CHANNELS from env: '{channels_str}'")
    
    if channels_str:
        # Split by comma and clean up
        channels = []
        for channel in channels_str.split(','):
            channel = channel.strip()
            if channel:  # Only add non-empty strings
                # Ensure @ prefix
                if not channel.startswith('@'):
                    channel = f"@{channel}"
                channels.append(channel)
        
        logger.info(f"✅ Parsed channels: {channels}")
        return channels
    
    logger.warning("⚠️  No REQUIRED_CHANNELS found in environment")
    return []

def get_admin_ids():
    """Get admin IDs directly from environment"""
    admin_ids_str = os.getenv('ADMIN_IDS', '417079598')
    if admin_ids_str:
        try:
            return [int(id.strip()) for id in admin_ids_str.split(',') if id.strip()]
        except ValueError:
            logger.error(f"Invalid ADMIN_IDS format: {admin_ids_str}")
            return []
    return []

# Set constants directly
REQUIRED_CHANNELS = get_required_channels()
ADMIN_IDS = get_admin_ids()

logger.info(f"✅ Checks module loaded: {len(REQUIRED_CHANNELS)} required channels, {len(ADMIN_IDS)} admins")

def require_channel_membership(func):
    """Decorator to check if user is member of all required channels AND not banned"""
    @wraps(func)
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        user_id = update.effective_user.id
        
        logger.info(f"🔍 Security check for user {user_id}")
        
        # FIRST: Check if user is banned (this should come before admin check for banned admins)
        if db_manager.is_user_banned(user_id):
            logger.warning(f"🚫 Banned user {user_id} tried to use bot")
            await _send_banned_message(update, context)
            return None  # BLOCK the command
        
        # THEN: Skip check for admins (but banned admins already caught above)
        if _is_admin(user_id):
            logger.info(f"✅ User {user_id} is admin, bypassing channel check")
            return await func(update, context, *args, **kwargs)
        
        # Check if channels are required
        if not REQUIRED_CHANNELS:
            return await func(update, context, *args, **kwargs)
        
        # Check cached membership with expiry
        cache_time = CHANNEL_CACHE_EXPIRY
        
        # Force re-check if last check was more than 24 hours ago
        current_time = time.time()
        for channel in REQUIRED_CHANNELS:
            last_verified = db_manager.get_channel_verification_timestamp(user_id, channel)
            if current_time - last_verified > FORCE_RECHECK_INTERVAL:
                logger.info(f"Forcing re-check for user {user_id}, channel {channel}")
                cache_time = 0
                break
        
        if db_manager.has_joined_required_channels(user_id, REQUIRED_CHANNELS, max_cache_age=cache_time):
            logger.info(f"✅ User {user_id} has valid channel cache")
            return await func(update, context, *args, **kwargs)
        
        # Verify channel membership in real-time
        missing_channels = await _check_channel_membership(user_id, context)
        
        if not missing_channels:
            # User has joined all channels, update database and timestamps
            for channel in REQUIRED_CHANNELS:
                db_manager.update_channel_membership(user_id, channel, True)
                db_manager.update_channel_verification_timestamp(user_id, channel)
            
            logger.info(f"✅ User {user_id} verified all channels")
            return await func(update, context, *args, **kwargs)
        else:
            # User hasn't joined all channels
            logger.info(f"❌ User {user_id} missing channels: {missing_channels}")
            await _send_channel_request(update, context, missing_channels)
            return None
    
    return wrapper

async def _check_channel_membership(user_id: int, context: CallbackContext) -> list:
    """Check which channels user hasn't joined"""
    missing_channels = []
    
    for channel in REQUIRED_CHANNELS:
        try:
            logger.info(f"🔍 Checking membership for user {user_id} in {channel}")
            
            # Try to get chat member
            chat_member = await context.bot.get_chat_member(
                chat_id=channel,
                user_id=user_id
            )
            
            status = chat_member.status
            logger.info(f"✅ Membership status for {channel}: {status}")
            
            # Check if user is a member
            # 'member', 'administrator', 'creator' are all valid memberships
            if status in ['left', 'kicked', 'banned']:
                missing_channels.append(channel)
                logger.info(f"❌ User {user_id} is not a member of {channel} (status: {status})")
            else:
                logger.info(f"✅ User {user_id} is a member of {channel} (status: {status})")
                # User is a member (could be 'member', 'administrator', 'creator', etc.)
                
        except Exception as e:
            logger.error(f"❌ Failed to check membership for channel {channel}: {e}")
            
            # If we can't check membership, we have a few options:
            # 1. Assume user needs to join (safe option)
            # 2. Try alternative method
            
            # For now, we'll assume they need to join if we can't verify
            missing_channels.append(channel)
            
            # Try to get more specific error info
            error_msg = str(e).lower()
            if "chat not found" in error_msg:
                logger.error(f"🚨 Channel {channel} not found or bot is not in channel")
            elif "bot was kicked" in error_msg:
                logger.error(f"🚨 Bot was kicked from {channel}")
            elif "not enough rights" in error_msg:
                logger.error(f"🚨 Bot doesn't have rights to check membership in {channel}")
    
    logger.info(f"📊 Final missing channels for user {user_id}: {missing_channels}")
    return missing_channels

async def _send_channel_request(update: Update, context: CallbackContext, missing_channels: list):
    """Send message asking user to join channels with buttons"""
    if not missing_channels:
        return
    
    # Count channels
    total_channels = len(REQUIRED_CHANNELS)
    missing_count = len(missing_channels)
    
    # Create inline keyboard with buttons for each missing channel
    keyboard = []
    for channel in missing_channels:
        channel_username = channel.replace('@', '')
        # Create button that opens the channel
        keyboard.append([
            InlineKeyboardButton(
                f"📢 Join {channel}",
                url=f"https://t.me/{channel_username}"
            )
        ])
    
    # Add a verification button
    keyboard.append([
        InlineKeyboardButton(
            "✅ I've Joined All Channels",
            callback_data="verify_channels"
        )
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Initialize message variable
    message = ""
    
    # Simplified message with just buttons
    if missing_count == total_channels:
        # User hasn't joined any channels
        message = "📢 **Join Required Channels**\n\n"
        message += f"To use this bot, please join **{total_channels}** required channels.\n\n"
        message += "**Click the buttons below to join each channel:**"
    else:
        # User has joined some but not all channels
        message += f"You've joined {total_channels - missing_count} of {total_channels} required channels.\n\n"
        message += f"Please join the remaining **{missing_count}** channels:\n\n"
        message += "**Click the buttons below to join:**"
    
    if update.message:
        sent_message = await update.message.reply_text(
            message, 
            reply_markup=reply_markup,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        # Store message ID for later verification
        context.user_data['channel_request_msg_id'] = sent_message.message_id
    elif update.callback_query:
        sent_message = await update.callback_query.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        context.user_data['channel_request_msg_id'] = sent_message.message_id

async def handle_channel_verification(update: Update, context: CallbackContext):
    """Handle channel verification button click"""
    query = update.callback_query
    user_id = query.from_user.id
    
    await query.answer("Checking your membership...")
    
    # Check channel membership
    missing_channels = await _check_channel_membership(user_id, context)
    
    if not missing_channels:
        # User has joined all channels
        for channel in REQUIRED_CHANNELS:
            db_manager.update_channel_membership(user_id, channel, True)
            db_manager.update_channel_verification_timestamp(user_id, channel)
        
        # Update the message
        await query.edit_message_text(
            "✅ **Verification Successful!**\n\n"
            "You have joined all required channels. You can now use the bot!\n\n"
            "Try your command again. 🎉",
            parse_mode='Markdown'
        )
        logger.info(f"✅ User {user_id} verified channel membership")
        
    else:
        # Still missing some channels
        missing_count = len(missing_channels)
        total_channels = len(REQUIRED_CHANNELS)
        
        # Create a cleaner error message with just buttons
        if missing_count == total_channels:
            error_msg = (
                f"You haven't joined any of the {total_channels} required channels.\n\n"
                f"**Please join using the buttons below:**"
            )
        else:
            error_msg = (
                f"You're still missing {missing_count} of {total_channels} required channels.\n\n"
                f"**Please join the remaining channels:**"
            )
        
        # Update keyboard to show only missing channels
        keyboard = []
        for channel in missing_channels:
            channel_username = channel.replace('@', '')
            keyboard.append([
                InlineKeyboardButton(
                    f"📢 Join {channel}",
                    url=f"https://t.me/{channel_username}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton(
                "🔄 Check Again",
                callback_data="verify_channels"
            )
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            error_msg,
            reply_markup=reply_markup,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        logger.info(f"❌ User {user_id} still missing {missing_count} channels")

async def periodic_channel_check(context: CallbackContext):
    """Periodic job to re-check channel membership for active users"""
    logger.info("🔄 Running periodic channel membership check...")
    
    try:
        # Get all users who were active in the last 7 days
        cursor = db_manager.conn.cursor()
        cursor.execute('''
            SELECT user_id, channels_joined, channels_verified_at 
            FROM user_preferences 
            WHERE last_activity > datetime('now', '-7 days')
              AND is_banned = 0
            LIMIT 100  # Limit to 100 users per run
        ''')
        
        users_to_check = []
        for row in cursor.fetchall():
            user_id = row['user_id']
            
            # Check if cache is expired for any channel
            timestamps = {}
            if row['channels_verified_at']:
                try:
                    timestamps = json.loads(row['channels_verified_at'])
                except:
                    continue
            
            current_time = time.time()
            needs_check = False
            
            for channel in REQUIRED_CHANNELS:
                last_verified = timestamps.get(channel, 0)
                if current_time - last_verified > FORCE_RECHECK_INTERVAL:
                    needs_check = True
                    break
            
            if needs_check:
                users_to_check.append(user_id)
        
        logger.info(f"🔍 Found {len(users_to_check)} users needing channel re-check")
        
        # Re-check a few users (limit to 10 per run to avoid rate limits)
        for user_id in users_to_check[:10]:
            try:
                missing_channels = await _check_channel_membership(user_id, context)
                
                if missing_channels:
                    # User left some channels
                    logger.warning(f"User {user_id} left channels: {missing_channels}")
                    
                    # Remove from cache
                    for channel in missing_channels:
                        db_manager.update_channel_membership(user_id, channel, False)
                    
                    # Try to notify user
                    try:
                        await context.bot.send_message(
                            chat_id=user_id,
                            text=f"⚠️ **Channel Membership Update**\n\n"
                                 f"It appears you've left some required channels:\n\n"
                                 f"{', '.join(missing_channels)}\n\n"
                                 f"Please re-join to continue using the bot.",
                            parse_mode='Markdown'
                        )
                    except:
                        pass  # User might have blocked the bot
                
                else:
                    # Still a member, update timestamp
                    for channel in REQUIRED_CHANNELS:
                        db_manager.update_channel_verification_timestamp(user_id, channel)
                        
            except Exception as e:
                logger.error(f"Error checking user {user_id}: {e}")
                
    except Exception as e:
        logger.error(f"Error in periodic channel check: {e}")

async def recheck_channels_command(update: Update, context: CallbackContext):
    """Manually trigger channel re-check"""
    user_id = update.effective_user.id
    
    await update.message.reply_text("🔄 Checking your channel membership...")
    
    # Clear cache for this user
    if db_manager.is_connected:
        # Reset all channel timestamps to force re-check
        for channel in REQUIRED_CHANNELS:
            db_manager.update_channel_verification_timestamp(user_id, channel)
    
    # Force immediate check
    missing_channels = await _check_channel_membership(user_id, context)
    
    if not missing_channels:
        # Update database
        for channel in REQUIRED_CHANNELS:
            db_manager.update_channel_membership(user_id, channel, True)
            db_manager.update_channel_verification_timestamp(user_id, channel)
        
        await update.message.reply_text(
            "✅ **All good!** You're still a member of all required channels.",
            parse_mode='Markdown'
        )
    else:
        # User left some channels
        missing_list = "\n".join([f"• {ch}" for ch in missing_channels])
        
        # Remove from cache
        for channel in missing_channels:
            db_manager.update_channel_membership(user_id, channel, False)
        
        await update.message.reply_text(
            f"❌ **You've left some channels:**\n\n{missing_list}\n\n"
            f"Please re-join to use the bot.",
            parse_mode='Markdown'
        )

async def check_my_status_command(update: Update, context: CallbackContext):
    """Check your current status with the bot"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    message = f"👤 **Status Check for {user_name}**\n\n"
    message += f"**User ID:** `{user_id}`\n"
    
    # Check admin status
    is_admin = _is_admin(user_id)
    message += f"**Admin:** {'✅ Yes' if is_admin else '❌ No'}\n"
    
    # Check ban status
    is_banned = db_manager.is_user_banned(user_id)
    message += f"**Banned:** {'🔨 Yes' if is_banned else '✅ No'}\n\n"
    
    # Check channel membership
    if REQUIRED_CHANNELS:
        message += "**Required Channels:**\n"
        
        for channel in REQUIRED_CHANNELS:
            try:
                chat_member = await context.bot.get_chat_member(
                    chat_id=channel,
                    user_id=user_id
                )
                status = chat_member.status
                is_member = status not in ['left', 'kicked', 'banned']
                
                emoji = "✅" if is_member else "❌"
                message += f"{emoji} {channel}: {status}\n"
                
            except Exception as e:
                message += f"❓ {channel}: Error checking\n"
    
    # Check database cache
    if db_manager.is_connected:
        user_prefs = db_manager.get_user_preferences(user_id)
        cached_channels = user_prefs.get('channels_joined', [])
        message += f"\n**Cached in DB:** {cached_channels}\n"
        
        # Check if DB thinks you've joined all channels
        has_joined = db_manager.has_joined_required_channels(user_id, REQUIRED_CHANNELS)
        message += f"**DB says joined all:** {'✅ Yes' if has_joined else '❌ No'}\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def force_check_command(update: Update, context: CallbackContext):
    """Force re-check channel membership and clear cache"""
    user_id = update.effective_user.id
    
    await update.message.reply_text("🔄 Force checking channel membership...")
    
    # Clear any cached membership in database
    if db_manager.is_connected:
        # Reset channels_joined for this user
        db_manager.update_channel_membership(user_id, "clear_all", False)
        logger.info(f"🧹 Cleared channel cache for user {user_id}")
    
    # Check membership in real-time
    missing_channels = await _check_channel_membership(user_id, context)
    
    if not missing_channels:
        # User has joined all channels, update database
        for channel in REQUIRED_CHANNELS:
            db_manager.update_channel_membership(user_id, channel, True)
        
        await update.message.reply_text(
            "✅ **Verified!** You are a member of all required channels.\n\n"
            "You can now use the bot normally. 🎉",
            parse_mode='Markdown'
        )
    else:
        # Show which channels are missing
        missing_list = "\n".join([f"• {ch}" for ch in missing_channels])
        await update.message.reply_text(
            f"❌ **Missing Channels:**\n\n{missing_list}\n\n"
            f"Please join the missing channels and try again.",
            parse_mode='Markdown'
        )

async def debug_channels_command(update: Update, context: CallbackContext):
    """Debug command to check channel configuration"""
    user_id = update.effective_user.id
    
    message = "🔧 **Debug - Channel Configuration**\n\n"
    
    # Show raw environment variable
    raw_channels = os.getenv('REQUIRED_CHANNELS', 'NOT SET')
    message += f"**Raw REQUIRED_CHANNELS env:** `{raw_channels}`\n\n"
    
    # Show parsed channels
    message += f"**Parsed REQUIRED_CHANNELS:** {REQUIRED_CHANNELS}\n"
    message += f"**Number of channels:** {len(REQUIRED_CHANNELS)}\n\n"
    
    # Check membership for each channel
    message += "**Channel Membership Status:**\n"
    
    for channel in REQUIRED_CHANNELS:
        try:
            chat_member = await context.bot.get_chat_member(
                chat_id=channel,
                user_id=user_id
            )
            status = chat_member.status
            is_member = status not in ['left', 'kicked', 'banned']
            
            emoji = "✅" if is_member else "❌"
            message += f"{emoji} {channel}: {status}\n"
            
        except Exception as e:
            message += f"❓ {channel}: Error - {str(e)[:50]}...\n"
    
    # Check database cached membership
    if db_manager.is_connected:
        user_prefs = db_manager.get_user_preferences(user_id)
        cached_channels = user_prefs.get('channels_joined', [])
        message += f"\n**Cached in DB:** {cached_channels}\n"
    
    message += f"\n**Is Admin:** {_is_admin(user_id)}"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def _send_banned_message(update: Update, context: CallbackContext):
    """Send message to banned user"""
    user_id = update.effective_user.id
    
    # Get ban reason from database
    try:
        cursor = db_manager.conn.cursor()
        cursor.execute(
            'SELECT ban_reason, ban_date FROM user_preferences WHERE user_id = ? AND is_banned = 1',
            (user_id,)
        )
        row = cursor.fetchone()
        
        ban_reason = row['ban_reason'] if row else "Violation of terms"
        ban_date = row['ban_date'] if row else "Unknown date"
    except Exception as e:
        logger.error(f"Error getting ban info: {e}")
        ban_reason = "Violation of terms"
        ban_date = "Unknown date"
    
    message = f"⛔️ **You are banned from using this bot.**\n\n"
    message += f"**Reason:** {ban_reason}\n"
    message += f"**Date:** {ban_date}\n\n"
    message += "If you believe this is a mistake, please contact the bot administrator."
    
    if update.message:
        await update.message.reply_text(message, parse_mode='Markdown')
    elif update.callback_query:
        await update.callback_query.message.reply_text(message, parse_mode='Markdown')

def _is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    logger.info(f"🔍 Checking if user {user_id} is admin...")
    logger.info(f"🔍 ADMIN_IDS from env: {ADMIN_IDS}")
    logger.info(f"🔍 Type of ADMIN_IDS: {type(ADMIN_IDS)}")
    logger.info(f"🔍 Type of user_id: {type(user_id)}")
    
    # First check environment variable admins
    if user_id in ADMIN_IDS:
        logger.info(f"✅ User {user_id} is in ADMIN_IDS list")
        return True
    else:
        logger.info(f"❌ User {user_id} is NOT in ADMIN_IDS list: {ADMIN_IDS}")
    
    # Then check database (for dynamic admin management)
    db_admin = db_manager.is_user_admin(user_id)
    logger.info(f"🔍 Database admin check for {user_id}: {db_admin}")
    
    return db_admin

async def check_and_request_channels(update: Update, context: CallbackContext) -> bool:
    """
    Check if user has joined required channels and request if not.
    Returns True if user can proceed, False if blocked.
    """
    user_id = update.effective_user.id
    
    # Skip check for admins
    if _is_admin(user_id):
        return True
    
    # Check if user is banned
    if db_manager.is_user_banned(user_id):
        await _send_banned_message(update, context)
        return False
    
    # Check if channels are required
    if not REQUIRED_CHANNELS:
        return True
    
    # Check cached membership
    if db_manager.has_joined_required_channels(user_id, REQUIRED_CHANNELS):
        return True
    
    # Real-time check
    missing_channels = await _check_channel_membership(user_id, context)
    
    if not missing_channels:
        # Update database
        for channel in REQUIRED_CHANNELS:
            db_manager.update_channel_membership(user_id, channel, True)
        return True
    else:
        await _send_channel_request(update, context, missing_channels)
        return False