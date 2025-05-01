from telegram import Update, ParseMode
from telegram.ext import CommandHandler, CallbackContext
from telegram.error import BadRequest
from loguru import logger
from database import db
from utils.decorators import admin_only, send_typing, log_command
from utils.helpers import extract_user_and_reason

@admin_only
@send_typing
@log_command
def promote(update: Update, context: CallbackContext) -> None:
    """Promote a user to admin in the group."""
    message = update.message
    chat = update.effective_chat
    user = update.effective_user
    
    # Extract user to promote
    user_id, reason = extract_user_and_reason(update, context)
    
    if not user_id:
        message.reply_text("You need to specify a user to promote.")
        return
    
    # Try to promote the user
    try:
        chat.promote_member(
            user_id=user_id,
            can_change_info=True,
            can_delete_messages=True,
            can_invite_users=True,
            can_restrict_members=True,
            can_pin_messages=True
        )
        
        # Get user info
        promoted_user = context.bot.get_chat_member(chat.id, user_id).user
        
        # Send success message
        message.reply_html(
            f"✅ <b>Promoted:</b> {promoted_user.mention_html()}\n"
            f"👮‍♂️ <b>By:</b> {user.mention_html()}"
        )
        
        logger.info(f"User {user.id} promoted {user_id} in {chat.id}")
    
    except BadRequest as e:
        message.reply_text(f"Could not promote user: {e.message}")
        logger.error(f"Failed to promote user: {e}")

@admin_only
@send_typing
@log_command
def demote(update: Update, context: CallbackContext) -> None:
    """Demote an admin to regular user."""
    message = update.message
    chat = update.effective_chat
    user = update.effective_user
    
    # Extract user to demote
    user_id, reason = extract_user_and_reason(update, context)
    
    if not user_id:
        message.reply_text("You need to specify a user to demote.")
        return
    
    # Try to demote the user
    try:
        chat.promote_member(
            user_id=user_id,
            can_change_info=False,
            can_delete_messages=False,
            can_invite_users=False,
            can_restrict_members=False,
            can_pin_messages=False,
            can_manage_voice_chats=False
        )
        
        # Get user info
        demoted_user = context.bot.get_chat_member(chat.id, user_id).user
        
        # Send success message
        message.reply_html(
            f"⬇️ <b>Demoted:</b> {demoted_user.mention_html()}\n"
            f"👮‍♂️ <b>By:</b> {user.mention_html()}"
        )
        
        logger.info(f"User {user.id} demoted {user_id} in {chat.id}")
    
    except BadRequest as e:
        message.reply_text(f"Could not demote user: {e.message}")
        logger.error(f"Failed to demote user: {e}")

@admin_only
@send_typing
@log_command
def pin(update: Update, context: CallbackContext) -> None:
    """Pin a message in the group."""
    message = update.message
    chat = update.effective_chat
    
    # Check if the command is a reply to a message
    if not message.reply_to_message:
        message.reply_text("Reply to a message to pin it.")
        return
    
    # Get whether to notify members or not
    notify = not any(arg.lower() in ["quiet", "silent", "nonotify"] for arg in context.args)
    
    # Try to pin the message
    try:
        message.reply_to_message.pin(disable_notification=not notify)
        
        if not notify:
            # If quiet pin, delete the command message
            message.delete()
    except BadRequest as e:
        message.reply_text(f"Could not pin message: {e.message}")
        logger.error(f"Failed to pin message: {e}")

@admin_only
@send_typing
@log_command
def unpin(update: Update, context: CallbackContext) -> None:
    """Unpin a message in the group."""
    message = update.message
    chat = update.effective_chat
    
    # Check if it's a reply to a specific message to unpin
    if message.reply_to_message:
        try:
            message.reply_to_message.unpin()
            message.reply_text("Message unpinned.")
        except BadRequest as e:
            message.reply_text(f"Could not unpin message: {e.message}")
            logger.error(f"Failed to unpin specific message: {e}")
    else:
        # If no reply, unpin the latest pinned message
        try:
            context.bot.unpin_chat_message(chat.id)
            message.reply_text("Latest pinned message has been unpinned.")
        except BadRequest as e:
            message.reply_text(f"Could not unpin message: {e.message}")
            logger.error(f"Failed to unpin latest message: {e}")

@admin_only
@send_typing
@log_command
def set_chat_title(update: Update, context: CallbackContext) -> None:
    """Set the group title."""
    message = update.message
    chat = update.effective_chat
    
    # Get new title from args
    if not context.args:
        message.reply_text("Please provide a new title for the chat.")
        return
    
    new_title = " ".join(context.args)
    
    # Enforce title length limit
    if len(new_title) > 255:
        message.reply_text("Chat title must be less than 255 characters.")
        return
    
    # Try to set the new title
    try:
        context.bot.set_chat_title(chat.id, new_title)
        message.reply_text(f"Chat title changed to: {new_title}")
        logger.info(f"Chat title changed in {chat.id} by {update.effective_user.id}")
        
        # Update in database
        db.save_group(chat.id, new_title, chat.type)
    except BadRequest as e:
        message.reply_text(f"Could not set chat title: {e.message}")
        logger.error(f"Failed to set chat title: {e}")

@admin_only
@send_typing
@log_command
def set_chat_description(update: Update, context: CallbackContext) -> None:
    """Set the group description."""
    message = update.message
    chat = update.effective_chat
    
    # Get new description from args
    if not context.args:
        message.reply_text("Please provide a new description for the chat.")
        return
    
    new_description = " ".join(context.args)
    
    # Try to set the new description
    try:
        context.bot.set_chat_description(chat.id, new_description)
        message.reply_text("Chat description updated successfully.")
        logger.info(f"Chat description changed in {chat.id} by {update.effective_user.id}")
    except BadRequest as e:
        message.reply_text(f"Could not set chat description: {e.message}")
        logger.error(f"Failed to set chat description: {e}")

@admin_only
@send_typing
@log_command
def set_rules(update: Update, context: CallbackContext) -> None:
    """Set the group rules."""
    message = update.message
    chat = update.effective_chat
    
    # Get rules text from args
    if not context.args:
        message.reply_text("Please provide the rules for this group.")
        return
    
    rules_text = " ".join(context.args)
    
    # Save rules to database
    db.save_setting(chat.id, "rules", rules_text)
    
    message.reply_text("Group rules have been updated!")
    logger.info(f"Rules updated in {chat.id} by {update.effective_user.id}")

@send_typing
def rules(update: Update, context: CallbackContext) -> None:
    """Display the group rules."""
    message = update.message
    chat = update.effective_chat
    
    # Get rules from database
    rules_text = db.get_setting(chat.id, "rules")
    
    if not rules_text:
        message.reply_text(
            "No rules have been set for this group yet.\n\n"
            "Ask an admin to set rules using the /setrules command."
        )
        return
    
    message.reply_html(
        f"<b>Rules for {chat.title}:</b>\n\n{rules_text}"
    )

@admin_only
@send_typing
@log_command
def purge(update: Update, context: CallbackContext) -> None:
    """Delete all messages from the replied message to the current one."""
    message = update.message
    chat = update.effective_chat
    
    # Check if the command is a reply
    if not message.reply_to_message:
        message.reply_text("Reply to a message to start purging from.")
        return
    
    message_id = message.reply_to_message.message_id
    delete_to = message.message_id
    
    # Count messages to delete
    count = delete_to - message_id
    
    # Check if trying to delete too many messages
    if count > 100:
        message.reply_text("You can only purge up to 100 messages at a time.")
        count = 100
    
    # Delete messages
    try:
        for m_id in range(message_id, delete_to + 1):
            try:
                context.bot.delete_message(chat.id, m_id)
            except BadRequest:
                pass
        
        # Send success message and auto-delete it after 5 seconds
        confirmation = message.reply_text(f"Purged {count} messages.", quote=False)
        
        # Schedule deletion of confirmation message
        context.job_queue.run_once(
            lambda _: context.bot.delete_message(chat.id, confirmation.message_id),
            5
        )
        
        logger.info(f"Purged {count} messages in {chat.id} by {update.effective_user.id}")
    
    except BadRequest as e:
        message.reply_text(f"Could not purge messages: {e.message}")
        logger.error(f"Failed to purge messages: {e}")

def register_admin_handlers(dispatcher):
    """Register admin command handlers."""
    dispatcher.add_handler(CommandHandler("promote", promote))
    dispatcher.add_handler(CommandHandler("demote", demote))
    dispatcher.add_handler(CommandHandler("pin", pin))
    dispatcher.add_handler(CommandHandler("unpin", unpin))
    dispatcher.add_handler(CommandHandler("title", set_chat_title))
    dispatcher.add_handler(CommandHandler("description", set_chat_description))
    dispatcher.add_handler(CommandHandler("setrules", set_rules))
    dispatcher.add_handler(CommandHandler("rules", rules))
    dispatcher.add_handler(CommandHandler("purge", purge))