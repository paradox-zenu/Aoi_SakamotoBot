from telegram import Update, ChatPermissions, ParseMode
from telegram.ext import CommandHandler, CallbackContext
from telegram.error import BadRequest
from loguru import logger
from config import SUDO_USERS, OWNER_ID, LOGS_CHANNEL
from database import db
from utils.decorators import admin_only, sudo_only, send_typing, log_command
from utils.helpers import extract_user_and_reason, extract_time

@admin_only
@send_typing
@log_command
def ban(update: Update, context: CallbackContext) -> None:
    """Ban a user from the group."""
    message = update.message
    chat = update.effective_chat
    user = update.effective_user
    
    # Extract user and reason
    user_id, reason = extract_user_and_reason(update, context)
    
    if not user_id:
        message.reply_text("You need to specify a user to ban.")
        return
    
    # Check if the user is trying to ban themselves
    if user_id == context.bot.id:
        message.reply_text("I'm not going to ban myself, are you crazy?")
        return
    
    # Try to ban the user
    try:
        # Get chat member info before banning
        chat_member = context.bot.get_chat_member(chat.id, user_id)
        target_user = chat_member.user
        
        # Check if the user is already banned
        if chat_member.status == "kicked":
            message.reply_text("This user is already banned.")
            return
        
        # Check if the user is an admin
        if chat_member.status in ["administrator", "creator"]:
            message.reply_text("I can't ban administrators.")
            return
        
        # Perform the ban
        context.bot.ban_chat_member(chat.id, user_id)
        
        # Build the ban message
        ban_message = f"🚫 <b>Ban Event</b>\n"
        ban_message += f"<b>User:</b> {target_user.mention_html()}\n"
        ban_message += f"<b>By:</b> {user.mention_html()}\n"
        
        if reason:
            ban_message += f"<b>Reason:</b> {reason}"
        
        # Send the ban message
        message.reply_html(ban_message)
        
        # Log the ban
        logger.info(f"User {user_id} banned from {chat.id} by {user.id} for: {reason}")
    
    except BadRequest as e:
        message.reply_text(f"Could not ban user: {e.message}")
        logger.error(f"Failed to ban user: {e}")

@admin_only
@send_typing
@log_command
def unban(update: Update, context: CallbackContext) -> None:
    """Unban a user from the group."""
    message = update.message
    chat = update.effective_chat
    user = update.effective_user
    
    # Extract user
    user_id, reason = extract_user_and_reason(update, context)
    
    if not user_id:
        message.reply_text("You need to specify a user to unban.")
        return
    
    # Try to unban the user
    try:
        # Get user info if possible
        try:
            target_user = context.bot.get_chat(user_id)
            user_mention = target_user.mention_html()
        except BadRequest:
            user_mention = f"<code>{user_id}</code>"
        
        # Unban the user
        context.bot.unban_chat_member(chat.id, user_id)
        
        # Send success message
        message.reply_html(
            f"✅ <b>Unbanned:</b> {user_mention}\n"
            f"👮‍♂️ <b>By:</b> {user.mention_html()}"
        )
        
        # Log the unban
        logger.info(f"User {user_id} unbanned from {chat.id} by {user.id}")
    
    except BadRequest as e:
        message.reply_text(f"Could not unban user: {e.message}")
        logger.error(f"Failed to unban user: {e}")

@admin_only
@send_typing
@log_command
def kick(update: Update, context: CallbackContext) -> None:
    """Kick a user from the group without banning."""
    message = update.message
    chat = update.effective_chat
    user = update.effective_user
    
    # Extract user and reason
    user_id, reason = extract_user_and_reason(update, context)
    
    if not user_id:
        message.reply_text("You need to specify a user to kick.")
        return
    
    # Check if the user is trying to kick themselves
    if user_id == context.bot.id:
        message.reply_text("I'm not going to kick myself, are you crazy?")
        return
    
    # Try to kick the user
    try:
        # Get chat member info before kicking
        chat_member = context.bot.get_chat_member(chat.id, user_id)
        target_user = chat_member.user
        
        # Check if the user is already banned
        if chat_member.status == "kicked":
            message.reply_text("This user is already banned.")
            return
        
        # Check if the user is an admin
        if chat_member.status in ["administrator", "creator"]:
            message.reply_text("I can't kick administrators.")
            return
        
        # Perform the kick (ban and unban)
        context.bot.ban_chat_member(chat.id, user_id)
        context.bot.unban_chat_member(chat.id, user_id)
        
        # Build the kick message
        kick_message = f"👢 <b>Kick Event</b>\n"
        kick_message += f"<b>User:</b> {target_user.mention_html()}\n"
        kick_message += f"<b>By:</b> {user.mention_html()}\n"
        
        if reason:
            kick_message += f"<b>Reason:</b> {reason}"
        
        # Send the kick message
        message.reply_html(kick_message)
        
        # Log the kick
        logger.info(f"User {user_id} kicked from {chat.id} by {user.id} for: {reason}")
    
    except BadRequest as e:
        message.reply_text(f"Could not kick user: {e.message}")
        logger.error(f"Failed to kick user: {e}")

@admin_only
@send_typing
@log_command
def mute(update: Update, context: CallbackContext) -> None:
    """Mute a user in the group."""
    message = update.message
    chat = update.effective_chat
    user = update.effective_user
    
    # Extract user, time, and reason
    user_id, reason = extract_user_and_reason(update, context)
    
    if not user_id:
        message.reply_text("You need to specify a user to mute.")
        return
    
    # Extract time if provided
    if reason:
        time_val = extract_time(reason.split()[0])
        if time_val:
            reason = " ".join(reason.split()[1:]) if len(reason.split()) > 1 else ""
    else:
        time_val = None
    
    # Check if the user is trying to mute themselves
    if user_id == context.bot.id:
        message.reply_text("I'm not going to mute myself, are you crazy?")
        return
    
    # Try to mute the user
    try:
        # Get chat member info before muting
        chat_member = context.bot.get_chat_member(chat.id, user_id)
        target_user = chat_member.user
        
        # Check if the user is an admin
        if chat_member.status in ["administrator", "creator"]:
            message.reply_text("I can't mute administrators.")
            return
        
        # Create permissions for mute
        mute_permissions = ChatPermissions(
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_polls=False,
            can_send_other_messages=False
        )
        
        # Perform the mute
        if time_val:
            context.bot.restrict_chat_member(
                chat.id, 
                user_id, 
                permissions=mute_permissions,
                until_date=time_val
            )
            time_text = f" for {time_val - message.date.timestamp():.0f} seconds"
        else:
            context.bot.restrict_chat_member(
                chat.id,
                user_id,
                permissions=mute_permissions
            )
            time_text = ""
        
        # Build the mute message
        mute_message = f"🔇 <b>Mute Event</b>\n"
        mute_message += f"<b>User:</b> {target_user.mention_html()}\n"
        mute_message += f"<b>By:</b> {user.mention_html()}\n"
        
        if time_text:
            mute_message += f"<b>Duration:</b>{time_text}\n"
        
        if reason:
            mute_message += f"<b>Reason:</b> {reason}"
        
        # Send the mute message
        message.reply_html(mute_message)
        
        # Log the mute
        logger.info(f"User {user_id} muted in {chat.id} by {user.id} for: {reason}")
    
    except BadRequest as e:
        message.reply_text(f"Could not mute user: {e.message}")
        logger.error(f"Failed to mute user: {e}")

@admin_only
@send_typing
@log_command
def unmute(update: Update, context: CallbackContext) -> None:
    """Unmute a user in the group."""
    message = update.message
    chat = update.effective_chat
    user = update.effective_user
    
    # Extract user
    user_id, _ = extract_user_and_reason(update, context)
    
    if not user_id:
        message.reply_text("You need to specify a user to unmute.")
        return
    
    # Try to unmute the user
    try:
        # Get chat member info
        chat_member = context.bot.get_chat_member(chat.id, user_id)
        target_user = chat_member.user
        
        # Check if the user can already send messages
        if chat_member.can_send_messages:
            message.reply_text("This user is not muted.")
            return
        
        # Create permissions for unmute
        unmute_permissions = ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
            can_invite_users=True
        )
        
        # Perform the unmute
        context.bot.restrict_chat_member(chat.id, user_id, permissions=unmute_permissions)
        
        # Send success message
        message.reply_html(
            f"🔊 <b>Unmuted:</b> {target_user.mention_html()}\n"
            f"👮‍♂️ <b>By:</b> {user.mention_html()}"
        )
        
        # Log the unmute
        logger.info(f"User {user_id} unmuted in {chat.id} by {user.id}")
    
    except BadRequest as e:
        message.reply_text(f"Could not unmute user: {e.message}")
        logger.error(f"Failed to unmute user: {e}")

@admin_only
@send_typing
@log_command
def warn(update: Update, context: CallbackContext) -> None:
    """Warn a user in the group."""
    message = update.message
    chat = update.effective_chat
    user = update.effective_user
    
    # Extract user and reason
    user_id, reason = extract_user_and_reason(update, context)
    
    if not user_id:
        message.reply_text("You need to specify a user to warn.")
        return
    
    # Check if the user is trying to warn themselves
    if user_id == context.bot.id:
        message.reply_text("I'm not going to warn myself, are you crazy?")
        return
    
    # Try to warn the user
    try:
        # Get chat member info
        chat_member = context.bot.get_chat_member(chat.id, user_id)
        target_user = chat_member.user
        
        # Check if the user is an admin
        if chat_member.status in ["administrator", "creator"]:
            message.reply_text("I can't warn administrators.")
            return
        
        # Add warning to database
        warn_count = db.warn_user(chat.id, user_id, reason, user.id)
        
        # Get warn limit
        warn_limit = int(db.get_setting(chat.id, "warn_limit") or 3)
        
        # Build the warn message
        warn_message = f"⚠️ <b>Warning {warn_count}/{warn_limit}</b>\n"
        warn_message += f"<b>User:</b> {target_user.mention_html()}\n"
        warn_message += f"<b>By:</b> {user.mention_html()}\n"
        
        if reason:
            warn_message += f"<b>Reason:</b> {reason}\n"
        
        # Check if user has exceeded warn limit
        if warn_count >= warn_limit:
            warn_message += f"\n<b>User has been banned for exceeding the warning limit!</b>"
            context.bot.ban_chat_member(chat.id, user_id)
            db.reset_warns(chat.id, user_id)  # Reset warnings after ban
        
        # Send the warn message
        message.reply_html(warn_message)
        
        # Log the warning
        logger.info(f"User {user_id} warned in {chat.id} by {user.id} for: {reason}")
    
    except BadRequest as e:
        message.reply_text(f"Could not warn user: {e.message}")
        logger.error(f"Failed to warn user: {e}")

@admin_only
@send_typing
@log_command
def unwarn(update: Update, context: CallbackContext) -> None:
    """Remove warnings from a user in the group."""
    message = update.message
    chat = update.effective_chat
    user = update.effective_user
    
    # Extract user
    user_id, _ = extract_user_and_reason(update, context)
    
    if not user_id:
        message.reply_text("You need to specify a user to remove warnings from.")
        return
    
    # Try to unwarn the user
    try:
        # Get chat member info
        chat_member = context.bot.get_chat_member(chat.id, user_id)
        target_user = chat_member.user
        
        # Get current warnings
        warns = db.get_warns(chat.id, user_id)
        
        if not warns:
            message.reply_text("This user has no warnings.")
            return
        
        # Reset warnings
        db.reset_warns(chat.id, user_id)
        
        # Send success message
        message.reply_html(
            f"🎯 <b>Warnings Reset</b>\n"
            f"<b>User:</b> {target_user.mention_html()}\n"
            f"<b>By:</b> {user.mention_html()}\n"
            f"<b>Cleared:</b> {len(warns)} warning(s)"
        )
        
        # Log the unwarn
        logger.info(f"Warnings reset for user {user_id} in {chat.id} by {user.id}")
    
    except BadRequest as e:
        message.reply_text(f"Could not reset warnings: {e.message}")
        logger.error(f"Failed to reset warnings: {e}")

@sudo_only
@send_typing
@log_command
def gban(update: Update, context: CallbackContext) -> None:
    """Globally ban a user from all groups where the bot is admin."""
    message = update.message
    user = update.effective_user
    
    # Extract user and reason
    user_id, reason = extract_user_and_reason(update, context)
    
    if not user_id:
        message.reply_text("You need to specify a user to globally ban.")
        return
    
    # Check if the user is trying to ban themselves or bot owner
    if user_id == context.bot.id:
        message.reply_text("I'm not going to ban myself, are you crazy?")
        return
    
    if user_id == OWNER_ID:
        message.reply_text("Nice try, but I won't ban my owner.")
        return
    
    if user_id in SUDO_USERS:
        message.reply_text("This user is a sudo user and cannot be globally banned.")
        return
    
    # Check if user is already gbanned
    if db.is_user_gbanned(user_id):
        message.reply_text("This user is already globally banned.")
        return
    
    # Try to get user info
    try:
        target_user = context.bot.get_chat(user_id)
        user_mention = target_user.mention_html()
    except BadRequest:
        user_mention = f"<code>{user_id}</code>"
    
    # Confirm gban
    message.reply_html(
        f"⚠️ <b>Global Ban Initiated</b>\n"
        f"<b>User:</b> {user_mention}\n"
        f"<b>By:</b> {user.mention_html()}\n"
        f"<b>Reason:</b> {reason or 'No reason provided'}\n\n"
        f"<i>Banning from all groups, this may take a while...</i>"
    )
    
    # Add user to gban list
    db.gban_user(user_id, user.id, reason)
    
    # Ban from all groups
    ban_count = 0
    groups = list(db.db.groups.find({}))
    
    for group in groups:
        try:
            context.bot.ban_chat_member(group["chat_id"], user_id)
            ban_count += 1
        except BadRequest:
            continue
    
    # Send success message
    message.reply_html(
        f"🌐 <b>Global Ban Complete</b>\n"
        f"<b>User:</b> {user_mention}\n"
        f"<b>By:</b> {user.mention_html()}\n"
        f"<b>Reason:</b> {reason or 'No reason provided'}\n"
        f"<b>Affected groups:</b> {ban_count}/{len(groups)}\n\n"
        f"<i>User has been added to the global ban list and banned from all possible groups.</i>"
    )
    
    # Log the gban
    logger.info(f"User {user_id} globally banned by {user.id} for: {reason}")
    
    # Send log to log channel if configured
    if LOGS_CHANNEL:
        try:
            context.bot.send_message(
                LOGS_CHANNEL,
                f"🌐 <b>Global Ban</b>\n"
                f"<b>User:</b> {user_mention}\n"
                f"<b>User ID:</b> <code>{user_id}</code>\n"
                f"<b>By:</b> {user.mention_html()} (<code>{user.id}</code>)\n"
                f"<b>Reason:</b> {reason or 'No reason provided'}\n"
                f"<b>Affected groups:</b> {ban_count}",
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Failed to send gban log: {e}")

@sudo_only
@send_typing
@log_command
def ungban(update: Update, context: CallbackContext) -> None:
    """Remove a user from the global ban list."""
    message = update.message
    user = update.effective_user
    
    # Extract user
    user_id, reason = extract_user_and_reason(update, context)
    
    if not user_id:
        message.reply_text("You need to specify a user to remove from global ban.")
        return
    
    # Check if user is gbanned
    if not db.is_user_gbanned(user_id):
        message.reply_text("This user is not globally banned.")
        return
    
    # Try to get user info
    try:
        target_user = context.bot.get_chat(user_id)
        user_mention = target_user.mention_html()
    except BadRequest:
        user_mention = f"<code>{user_id}</code>"
    
    # Confirm ungban
    message.reply_html(
        f"⚠️ <b>Global Unban Initiated</b>\n"
        f"<b>User:</b> {user_mention}\n"
        f"<b>By:</b> {user.mention_html()}\n\n"
        f"<i>Unbanning from all groups, this may take a while...</i>"
    )
    
    # Remove user from gban list
    db.ungban_user(user_id)
    
    # Unban from all groups
    unban_count = 0
    groups = list(db.db.groups.find({}))
    
    for group in groups:
        try:
            context.bot.unban_chat_member(group["chat_id"], user_id)
            unban_count += 1
        except BadRequest:
            continue
    
    # Send success message
    message.reply_html(
        f"🌐 <b>Global Unban Complete</b>\n"
        f"<b>User:</b> {user_mention}\n"
        f"<b>By:</b> {user.mention_html()}\n"
        f"<b>Affected groups:</b> {unban_count}/{len(groups)}\n\n"
        f"<i>User has been removed from the global ban list and unbanned from all possible groups.</i>"
    )
    
    # Log the ungban
    logger.info(f"User {user_id} globally unbanned by {user.id}")
    
    # Send log to log channel if configured
    if LOGS_CHANNEL:
        try:
            context.bot.send_message(
                LOGS_CHANNEL,
                f"🌐 <b>Global Unban</b>\n"
                f"<b>User:</b> {user_mention}\n"
                f"<b>User ID:</b> <code>{user_id}</code>\n"
                f"<b>By:</b> {user.mention_html()} (<code>{user.id}</code>)\n"
                f"<b>Affected groups:</b> {unban_count}",
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Failed to send ungban log: {e}")

def register_ban_handlers(dispatcher):
    """Register ban-related command handlers."""
    dispatcher.add_handler(CommandHandler("ban", ban))
    dispatcher.add_handler(CommandHandler("unban", unban))
    dispatcher.add_handler(CommandHandler("kick", kick))
    dispatcher.add_handler(CommandHandler("mute", mute))
    dispatcher.add_handler(CommandHandler("unmute", unmute))
    dispatcher.add_handler(CommandHandler("warn", warn))
    dispatcher.add_handler(CommandHandler("unwarn", unwarn))
    dispatcher.add_handler(CommandHandler("gban", gban))
    dispatcher.add_handler(CommandHandler("ungban", ungban))