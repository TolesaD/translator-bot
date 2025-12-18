from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import logging
from database import db_manager
from bot_config import ADMIN_IDS, REQUIRED_CHANNELS
from datetime import datetime
import math

logger = logging.getLogger(__name__)

async def admin_command(update: Update, context: CallbackContext):
    """Admin panel main command"""
    user_id = update.effective_user.id
    
    # Check if user is admin
    if not _is_admin(user_id):
        await update.message.reply_text("⛔️ You are not authorized to use admin commands.")
        return
    
    # Show admin panel
    keyboard = [
        [InlineKeyboardButton("📊 Statistics", callback_data='admin_stats')],
        [InlineKeyboardButton("👥 User Management", callback_data='admin_users')],
        [InlineKeyboardButton("🔨 Ban/Unban Users", callback_data='admin_bans')],
        [InlineKeyboardButton("📢 Broadcast Message", callback_data='admin_broadcast')],
        [InlineKeyboardButton("⚙️ Channel Settings", callback_data='admin_channels')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔧 **Admin Panel**\n\n"
        "Select an option below:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def admin_callback_handler(update: Update, context: CallbackContext):
    """Handle admin panel callbacks"""
    query = update.callback_query
    user_id = query.from_user.id
    
    logger.info(f"🔍 CALLBACK: Received callback data: {query.data} from user {user_id}")
    
    # Check if user is admin
    if not _is_admin(user_id):
        logger.warning(f"❌ User {user_id} tried to access admin callback but is not admin")
        await query.answer("⛔️ You are not authorized.", show_alert=True)
        return
    
    await query.answer()
    
    data = query.data
    logger.info(f"🔍 CALLBACK: Processing data: {data}")
    
    # Route to appropriate handler
    if data == 'admin_stats':
        await _show_statistics(query, context)
    elif data == 'admin_users':
        await _show_user_management(query, context)
    elif data == 'admin_bans':
        await _show_ban_management(query, context)
    elif data == 'admin_broadcast':
        await _show_broadcast_menu(query, context)
    elif data == 'admin_channels':
        await _show_channel_settings(query, context)
    elif data.startswith('user_page_'):
        page = int(data.split('_')[2])
        await _show_users_page(query, context, page)
    elif data.startswith('user_detail_'):
        user_id_target = int(data.split('_')[2])
        await _show_user_detail(query, context, user_id_target)
    elif data.startswith('ban_user_'):
        user_id_target = int(data.split('_')[2])
        await _show_ban_user(query, context, user_id_target)
    elif data.startswith('unban_user_'):
        user_id_target = int(data.split('_')[2])
        logger.info(f"🔧 UNBAN: Attempting to unban user {user_id_target}")
        await _unban_user(query, context, user_id_target)
    elif data.startswith('ban_confirm_'):
        user_id_target = int(data.split('_')[2])
        await _ban_user_confirm(query, context, user_id_target)
    elif data == 'broadcast_start':
        await _start_broadcast(query, context)
    elif data == 'broadcast_cancel':
        await query.edit_message_text("📢 Broadcast cancelled.")
    elif data == 'back_to_admin':
        await _back_to_admin_panel(query, context)
    else:
        logger.warning(f"⚠️ Unknown callback data: {data}")
        await query.edit_message_text(f"Unknown action: {data}")

async def _show_statistics(query, context):
    """Show bot statistics"""
    try:
        # Get database statistics
        db_stats = db_manager.get_database_stats()
        
        # Get user statistics
        total_users = db_manager.get_user_count()
        
        # Get daily stats for last 7 days
        daily_stats = db_manager.get_daily_stats(7)
        
        # Calculate today's stats
        today = datetime.now().strftime('%Y-%m-%d')
        today_stats = next((stat for stat in daily_stats if stat['date'] == today), None)
        
        message = "📊 **Bot Statistics**\n\n"
        message += f"👥 **Users:** {total_users:,}\n"
        message += f"📝 **Total Translations:** {db_stats.get('total_translations', 0):,}\n"
        message += f"📖 **Total Words:** {db_stats.get('total_words', 0):,}\n\n"
        
        if today_stats:
            message += f"📈 **Today's Activity:**\n"
            message += f"   • Translations: {today_stats['translation_count']:,}\n"
            message += f"   • Active Users: {today_stats['user_count']:,}\n"
            message += f"   • Words Translated: {today_stats['total_words']:,}\n\n"
        
        if daily_stats:
            message += "📅 **Last 7 Days Activity:**\n"
            for stat in daily_stats[:5]:  # Show last 5 days
                message += f"   • {stat['date']}: {stat['translation_count']:,} translations\n"
        
        # Add admin info
        message += f"\n🔧 **Admins:** {len(ADMIN_IDS)}\n"
        message += f"📢 **Required Channels:** {len(REQUIRED_CHANNELS)}\n"
        
        # Database info
        message += f"\n💾 **Database:** {db_stats.get('database_size_bytes', 0) / 1024 / 1024:.2f} MB"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data='back_to_admin')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error showing statistics: {e}")
        await query.edit_message_text(f"❌ Error loading statistics: {str(e)}")

async def _show_user_management(query, context):
    """Show user management interface"""
    await _show_users_page(query, context, 1)

async def _show_users_page(query, context, page: int = 1):
    """Show users page with pagination"""
    try:
        users_per_page = 10
        offset = (page - 1) * users_per_page
        
        users = db_manager.get_all_users(limit=users_per_page, offset=offset)
        total_users = db_manager.get_user_count()
        total_pages = max(1, math.ceil(total_users / users_per_page))
        
        if not users:
            message = "👥 **User Management**\n\nNo users found."
        else:
            message = f"👥 **User Management**\n\n"
            message += f"**Page {page}/{total_pages}**\n\n"
            
            for i, user in enumerate(users, 1):
                index = offset + i
                emoji = "👑" if user['is_admin'] else "🔨" if user['is_banned'] else "👤"
                message += f"{index}. {emoji} User ID: `{user['user_id']}`\n"
                message += f"   📝 Translations: {user['translation_count']:,}\n"
                message += f"   📍 Last Active: {_format_date(user['last_activity'])}\n\n"
        
        # Create keyboard with pagination
        keyboard = []
        
        # Previous/Next buttons
        nav_buttons = []
        if page > 1:
            nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f'user_page_{page-1}'))
        if page < total_pages:
            nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f'user_page_{page+1}'))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        # User action buttons for first 5 users on this page
        for i, user in enumerate(users[:5]):
            keyboard.append([
                InlineKeyboardButton(f"👁️ User {offset + i + 1}", callback_data=f'user_detail_{user["user_id"]}'),
                InlineKeyboardButton("🔨 Ban" if not user['is_banned'] else "✅ Unban", 
                                   callback_data=f'ban_user_{user["user_id"]}' if not user['is_banned'] else f'unban_user_{user["user_id"]}')
            ])
        
        # Back button
        keyboard.append([InlineKeyboardButton("🔙 Back to Admin", callback_data='back_to_admin')])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error showing users page: {e}")
        await query.edit_message_text(f"❌ Error loading users: {str(e)}")

async def _show_user_detail(query, context, user_id_target: int):
    """Show detailed user information"""
    try:
        user_prefs = db_manager.get_user_preferences(user_id_target)
        user_stats = db_manager.get_user_stats(user_id_target)
        history = db_manager.get_translation_history(user_id_target, limit=5)
        
        message = f"👤 **User Details**\n\n"
        message += f"**User ID:** `{user_id_target}`\n"
        message += f"**Admin:** {'✅ Yes' if db_manager.is_user_admin(user_id_target) else '❌ No'}\n"
        message += f"**Banned:** {'🔨 Yes' if db_manager.is_user_banned(user_id_target) else '✅ No'}\n"
        
        if user_prefs:
            message += f"**Language:** {user_prefs.get('default_language', 'en')}\n"
            message += f"**Joined:** {_format_date(user_prefs.get('created_at'))}\n"
            message += f"**Last Active:** {_format_date(user_prefs.get('last_activity'))}\n\n"
        
        if user_stats:
            message += f"📊 **Statistics**\n"
            message += f"• Translations: {user_stats.get('total_translations', 0):,}\n"
            message += f"• Words: {user_stats.get('total_words', 0):,}\n"
            message += f"• Characters: {user_stats.get('total_characters', 0):,}\n"
            message += f"• Active Days: {user_stats.get('active_days', 0)}\n\n"
        
        if history:
            message += f"📝 **Recent Translations**\n"
            for i, item in enumerate(history, 1):
                orig = item['original_text'][:30] + "..." if len(item['original_text']) > 30 else item['original_text']
                trans = item['translated_text'][:30] + "..." if len(item['translated_text']) > 30 else item['translated_text']
                message += f"{i}. {orig} → {trans}\n"
        
        keyboard = [
            [
                InlineKeyboardButton("🔨 Ban" if not db_manager.is_user_banned(user_id_target) else "✅ Unban", 
                                   callback_data=f'ban_user_{user_id_target}' if not db_manager.is_user_banned(user_id_target) else f'unban_user_{user_id_target}'),
                InlineKeyboardButton("🔙 Back", callback_data='user_page_1')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error showing user detail: {e}")
        await query.edit_message_text(f"❌ Error loading user details: {str(e)}")

async def _show_ban_management(query, context):
    """Show ban management interface"""
    try:
        banned_users = db_manager.get_banned_users()
        
        if not banned_users:
            message = "🔨 **Ban Management**\n\nNo banned users."
        else:
            message = "🔨 **Banned Users**\n\n"
            for i, user in enumerate(banned_users, 1):
                message += f"{i}. User ID: `{user['user_id']}`\n"
                message += f"   Reason: {user['ban_reason']}\n"
                message += f"   Date: {_format_date(user['ban_date'])}\n\n"
        
        keyboard = [
            [InlineKeyboardButton("👥 Manage Users", callback_data='admin_users')],
            [InlineKeyboardButton("🔙 Back", callback_data='back_to_admin')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error showing ban management: {e}")
        await query.edit_message_text(f"❌ Error loading banned users: {str(e)}")

async def _show_ban_user(query, context, user_id_target: int):
    """Show ban confirmation for a user"""
    message = f"🔨 **Ban User**\n\n"
    message += f"Are you sure you want to ban User ID `{user_id_target}`?\n\n"
    message += "Please provide a reason for the ban (optional).\n"
    message += "Reply with the reason, or type 'cancel' to abort."
    
    # Store user_id in context for later use
    context.user_data['ban_user_id'] = user_id_target
    context.user_data['awaiting_ban_reason'] = True
    
    keyboard = [
        [InlineKeyboardButton("❌ Cancel", callback_data='user_detail_' + str(user_id_target))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def _ban_user_confirm(query, context, user_id_target: int):
    """Confirm and execute ban"""
    admin_id = query.from_user.id
    reason = context.user_data.get('ban_reason', 'Violation of terms')
    
    success = db_manager.ban_user(user_id_target, admin_id, reason)
    
    if success:
        # Try to notify the user
        try:
            await context.bot.send_message(
                chat_id=user_id_target,
                text=f"⛔️ **You have been banned from using the bot.**\n\n"
                     f"Reason: {reason}\n\n"
                     f"If you believe this is a mistake, please contact the bot administrator."
            )
        except:
            pass  # User might have blocked the bot
        
        await query.edit_message_text(
            f"✅ User `{user_id_target}` has been banned.\nReason: {reason}",
            parse_mode='Markdown'
        )
    else:
        await query.edit_message_text(
            f"❌ Failed to ban user `{user_id_target}`.",
            parse_mode='Markdown'
        )
    
    # Clean up user_data
    context.user_data.pop('ban_user_id', None)
    context.user_data.pop('ban_reason', None)
    context.user_data.pop('awaiting_ban_reason', None)

async def _unban_user(query, context, user_id_target: int):
    """Unban a user with detailed debugging and immediate feedback"""
    admin_id = query.from_user.id
    
    logger.info(f"🔧 UNBAN: Starting unban process from admin panel")
    logger.info(f"🔧 UNBAN: Target user: {user_id_target}")
    logger.info(f"🔧 UNBAN: Admin ID: {admin_id}")
    
    # Show "processing" message immediately
    await query.edit_message_text(
        f"🔄 Unbanning user `{user_id_target}`...",
        parse_mode='Markdown'
    )
    
    # First, check current status BEFORE unban
    try:
        cursor = db_manager.conn.cursor()
        cursor.execute(
            'SELECT is_banned, ban_reason FROM user_preferences WHERE user_id = ?',
            (user_id_target,)
        )
        row_before = cursor.fetchone()
        
        if row_before:
            logger.info(f"🔧 UNBAN: Before unban - is_banned: {row_before['is_banned']}, ban_reason: {row_before['ban_reason']}")
            is_banned_before = bool(row_before['is_banned'])
        else:
            logger.info(f"🔧 UNBAN: User {user_id_target} not found before unban attempt")
            is_banned_before = False
    except Exception as e:
        logger.error(f"❌ UNBAN: Error checking before status: {e}")
        is_banned_before = False
    
    # Perform the unban
    success = db_manager.unban_user(user_id_target, admin_id)
    
    # Check status AFTER unban
    try:
        cursor.execute(
            'SELECT is_banned, ban_reason FROM user_preferences WHERE user_id = ?',
            (user_id_target,)
        )
        row_after = cursor.fetchone()
        
        if row_after:
            logger.info(f"🔧 UNBAN: After unban - is_banned: {row_after['is_banned']}, ban_reason: {row_after['ban_reason']}")
    except Exception as e:
        logger.error(f"❌ UNBAN: Error checking after status: {e}")
    
    logger.info(f"🔧 UNBAN: db_manager.unban_user returned: {success}")
    
    if success:
        # Try to notify the user
        try:
            await context.bot.send_message(
                chat_id=user_id_target,
                text="✅ **Your ban has been lifted.**\n\n"
                     "You can now use the bot again."
            )
            logger.info(f"🔧 UNBAN: Notification sent to user {user_id_target}")
        except Exception as e:
            logger.warning(f"⚠️ UNBAN: Could not notify user {user_id_target}: {e}")
        
        # Show success message
        success_message = f"✅ User `{user_id_target}` has been unbanned successfully!"
        
        keyboard = [
            [
                InlineKeyboardButton("👁️ View User", callback_data=f'user_detail_{user_id_target}'),
                InlineKeyboardButton("🔙 Back to Users", callback_data='user_page_1')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            success_message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        # Show error message with debug info
        error_message = f"❌ Failed to unban user `{user_id_target}`.\n\n"
        error_message += f"**Debug Information:**\n"
        error_message += f"• Before unban: is_banned={is_banned_before}\n"
        error_message += f"• After unban: Unknown (database error)\n"
        error_message += f"• Database method returned: {success}\n\n"
        error_message += "Please try again or check the logs."
        
        keyboard = [
            [InlineKeyboardButton("🔄 Try Again", callback_data=f'unban_user_{user_id_target}')],
            [InlineKeyboardButton("🔙 Back", callback_data=f'user_detail_{user_id_target}')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            error_message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def _show_broadcast_menu(query, context):
    """Show broadcast message menu"""
    total_users = db_manager.get_user_count()
    
    message = f"📢 **Broadcast Message**\n\n"
    message += f"You can send a message to all {total_users:,} users.\n\n"
    message += "Please send the message you want to broadcast.\n"
    message += "Format: Markdown is supported.\n"
    message += "Type 'cancel' to abort."
    
    context.user_data['awaiting_broadcast'] = True
    
    keyboard = [
        [InlineKeyboardButton("❌ Cancel", callback_data='back_to_admin')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def _start_broadcast(query, context):
    """Start broadcast process"""
    message = context.user_data.get('broadcast_message')
    
    if not message:
        await query.edit_message_text("❌ No message to broadcast.")
        return
    
    await query.edit_message_text("📢 Starting broadcast...")
    
    # Get all users
    users = db_manager.get_all_users(limit=10000)  # Large limit to get all users
    
    if not users:
        await query.edit_message_text("❌ No users to broadcast to.")
        return
    
    success_count = 0
    fail_count = 0
    total = len(users)
    
    # Send to users in batches
    for i, user in enumerate(users, 1):
        try:
            # Skip banned users
            if user['is_banned']:
                fail_count += 1
                continue
                
            await context.bot.send_message(
                chat_id=user['user_id'],
                text=message,
                parse_mode='Markdown'
            )
            success_count += 1
            
            # Update progress every 10 users
            if i % 10 == 0:
                await query.edit_message_text(
                    f"📢 Broadcasting... {i}/{total}\n"
                    f"✅ Success: {success_count}\n"
                    f"❌ Failed: {fail_count}"
                )
            
        except Exception as e:
            fail_count += 1
            logger.error(f"Failed to send broadcast to user {user['user_id']}: {e}")
    
    # Final report
    await query.edit_message_text(
        f"✅ **Broadcast Complete**\n\n"
        f"📊 **Statistics:**\n"
        f"• Total Users: {total:,}\n"
        f"• Successful: {success_count:,}\n"
        f"• Failed: {fail_count:,}\n"
        f"• Success Rate: {(success_count/total*100):.1f}%\n\n"
        f"📝 **Message sent to {success_count:,} users.**"
    )
    
    # Clean up user_data
    context.user_data.pop('broadcast_message', None)
    context.user_data.pop('awaiting_broadcast', None)

async def _show_channel_settings(query, context):
    """Show channel settings"""
    message = "⚙️ **Channel Settings**\n\n"
    message += f"**Required Channels:** {len(REQUIRED_CHANNELS)}\n\n"
    
    if REQUIRED_CHANNELS:
        message += "Users must join these channels:\n"
        for i, channel in enumerate(REQUIRED_CHANNELS, 1):
            message += f"{i}. {channel}\n"
    else:
        message += "No channels required. Users can use the bot freely.\n\n"
        message += "To set required channels, add them to the REQUIRED_CHANNELS environment variable."
    
    keyboard = [
        [InlineKeyboardButton("🔙 Back", callback_data='back_to_admin')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

    # Add to admin_handler.py
async def db_diagnostic(update: Update, context: CallbackContext):
    """Database diagnostic command"""
    user_id = update.effective_user.id
    
    if not _is_admin(user_id):
        await update.message.reply_text("❌ Admin only")
        return
    
    # Get target user from command args
    if not context.args:
        await update.message.reply_text("Usage: /dbdiagnostic <user_id>")
        return
    
    try:
        target_user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid user ID")
        return
    
    # Direct database query
    cursor = db_manager.conn.cursor()
    
    message = f"🔍 **Database Diagnostic for User {target_user_id}**\n\n"
    
    # Check user_preferences table
    cursor.execute('''
        SELECT user_id, is_banned, ban_reason, ban_date, 
               created_at, updated_at, last_activity
        FROM user_preferences 
        WHERE user_id = ?
    ''', (target_user_id,))
    
    row = cursor.fetchone()
    
    if not row:
        message += "❌ User not found in user_preferences table\n"
    else:
        message += "📋 **user_preferences table:**\n"
        for key in row.keys():
            value = row[key]
            if value is None:
                value_str = "NULL"
            else:
                value_str = str(value)
            message += f"• `{key}`: `{value_str}`\n"
            if key == 'is_banned':
                message += f"  → bool(is_banned): {bool(value)}\n"
    
    # Check admin_actions for ban/unban history
    cursor.execute('''
        SELECT action_type, details, timestamp
        FROM admin_actions 
        WHERE target_user_id = ?
        ORDER BY timestamp DESC
        LIMIT 5
    ''', (target_user_id,))
    
    actions = cursor.fetchall()
    if actions:
        message += "\n📜 **Recent Admin Actions:**\n"
        for action in actions:
            message += f"• {action['action_type']}: {action['details']} ({action['timestamp']})\n"
    
    # Check if user exists in translation_history
    cursor.execute(
        'SELECT COUNT(*) as count FROM translation_history WHERE user_id = ?',
        (target_user_id,)
    )
    count_row = cursor.fetchone()
    message += f"\n📝 **Translation History:** {count_row['count']} records\n"
    
    # Database info
    message += f"\n💾 **Database Info:**\n"
    message += f"• Path: `{db_manager.db_path}`\n"
    message += f"• Connected: {db_manager.is_connected}\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def _back_to_admin_panel(query, context):
    """Return to admin panel"""
    # Clean up any pending actions
    for key in ['awaiting_broadcast', 'broadcast_message', 'awaiting_ban_reason', 'ban_user_id', 'ban_reason']:
        context.user_data.pop(key, None)
    
    keyboard = [
        [InlineKeyboardButton("📊 Statistics", callback_data='admin_stats')],
        [InlineKeyboardButton("👥 User Management", callback_data='admin_users')],
        [InlineKeyboardButton("🔨 Ban/Unban Users", callback_data='admin_bans')],
        [InlineKeyboardButton("📢 Broadcast Message", callback_data='admin_broadcast')],
        [InlineKeyboardButton("⚙️ Channel Settings", callback_data='admin_channels')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🔧 **Admin Panel**\n\n"
        "Select an option below:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_admin_text_input(update: Update, context: CallbackContext):
    """Handle text input for admin actions (broadcast and ban reason)"""
    user_id = update.effective_user.id
    
    if not _is_admin(user_id):
        # If not admin, let other handlers process it
        return
    
    text = update.message.text
    
    logger.info(f"🔍 Admin text input from user {user_id}: '{text}'")
    logger.info(f"📊 User data state: {context.user_data}")
    
    # Check if we're waiting for broadcast message
    if context.user_data.get('awaiting_broadcast'):
        logger.info(f"📢 Processing broadcast message from admin {user_id}")
        context.user_data['broadcast_message'] = text
        
        # Confirm broadcast
        keyboard = [
            [
                InlineKeyboardButton("✅ Send Broadcast", callback_data='broadcast_start'),
                InlineKeyboardButton("❌ Cancel", callback_data='broadcast_cancel')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"📢 **Broadcast Preview**\n\n"
            f"Message:\n{text}\n\n"
            f"Send this to all users?",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        context.user_data['awaiting_broadcast'] = False
        return  # IMPORTANT: Return to prevent other handlers from processing
    
    # Check if we're waiting for ban reason
    if context.user_data.get('awaiting_ban_reason'):
        logger.info(f"🔨 Processing ban reason from admin {user_id}")
        
        if text.lower() == 'cancel':
            await update.message.reply_text("Ban cancelled.")
            context.user_data.pop('awaiting_ban_reason', None)
            context.user_data.pop('ban_user_id', None)
            return
        
        context.user_data['ban_reason'] = text
        target_user_id = context.user_data.get('ban_user_id')
        
        if target_user_id:
            keyboard = [
                [
                    InlineKeyboardButton("✅ Confirm Ban", callback_data=f'ban_confirm_{target_user_id}'),
                    InlineKeyboardButton("❌ Cancel", callback_data=f'user_detail_{target_user_id}')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"🔨 **Confirm Ban**\n\n"
                f"User ID: `{target_user_id}`\n"
                f"Reason: {text}\n\n"
                f"Confirm ban?",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        
        context.user_data['awaiting_ban_reason'] = False
        return  # IMPORTANT: Return to prevent other handlers from processing
    
    # If we reach here, it's not an admin action, let other handlers process
    logger.info(f"📝 Not an admin action, allowing other handlers to process")
    return

def _is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    logger.info(f"🔍 Checking if user {user_id} is admin...")
    logger.info(f"🔍 ADMIN_IDS from env: {ADMIN_IDS}")
    
    # First check environment variable admins
    if user_id in ADMIN_IDS:
        logger.info(f"✅ User {user_id} is in ADMIN_IDS list")
        return True
    
    # Then check database (for dynamic admin management)
    db_admin = db_manager.is_user_admin(user_id)
    logger.info(f"🔍 Database admin check for {user_id}: {db_admin}")
    
    return db_admin

def _format_date(date_str):
    """Format date string for display"""
    if not date_str:
        return "Never"
    
    try:
        if isinstance(date_str, str):
            # Remove timezone info if present
            date_str = date_str.split('+')[0].split('.')[0]
            dt = datetime.fromisoformat(date_str)
        else:
            dt = date_str
        
        return dt.strftime('%Y-%m-%d %H:%M')
    except:
        return str(date_str)

def setup_handlers(application):
    """Setup admin handlers"""
    # Add admin command handler
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("dbdiagnostic", db_diagnostic))  # Add this line
    
    # Add callback query handlers
    application.add_handler(CallbackQueryHandler(admin_callback_handler, pattern='^admin_'))
    application.add_handler(CallbackQueryHandler(admin_callback_handler, pattern='^user_'))
    application.add_handler(CallbackQueryHandler(admin_callback_handler, pattern='^ban_'))
    application.add_handler(CallbackQueryHandler(admin_callback_handler, pattern='^broadcast_'))
    application.add_handler(CallbackQueryHandler(admin_callback_handler, pattern='^back_to_admin'))
    
    # Add admin text input handler with HIGHER priority (group 1)
    # This will run BEFORE the regular text handler (group 0)
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            handle_admin_text_input
        ),
        group=1  # Higher group number = higher priority
    )
    
    # Single message handler for all admin text input
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        handle_admin_text_input
    ))