from telegram import Update, ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, CallbackContext, Filters, MessageHandler
from loguru import logger
from database import db
from utils.decorators import admin_only, send_typing, log_command
from utils.helpers import format_welcome_message

@admin_only
@send_typing
@log_command
def set_welcome(update: Update, context: CallbackContext) -> None:
    """Set a custom welcome message for the group."""
    message = update.message
    chat = update.effective_chat
    
    # If no message specified, show current welcome message
    if not context.args:
        # Get current welcome message
        group = db.get_group(chat.id)
        welcome_message = group.get("welcome_message", "Welcome to {chat_title}, {user_mention}!") if group else "Welcome to {chat_title}, {user_mention}!"
        
        # Show current welcome message
        message.reply_html(
            f"<b>Current welcome message:</b>\n\n{welcome_message}\n\n"
            f"<i>Use /welcome [message] to set a new welcome message.</i>\n\n"
            f"<b>Available placeholders:</b>\n"
            f"{{user_mention}} - Mentions the new user\n"
            f"{{user_firstname}} - User's first name\n"
            f"{{user_lastname}} - User's last name\n"
            f"{{user_username}} - User's username\n"
            f"{{user_id}} - User's ID\n"
            f"{{chat_title}} - Group name\n"
            f"{{chat_id}} - Group ID\n"
            f"{{members_count}} - Number of members in the group"
        )
        return
    
    # Get the new welcome message
    welcome_message = " ".join(context.args)
    
    # Get group from database
    group = db.get_group(chat.id)
    
    if group:
        # Update welcome message in database
        db.db.groups.update_one(
            {"chat_id": chat.id},
            {"$set": {"welcome_message": welcome_message}}
        )
    else:
        # Create new group entry
        db.save_group(
            chat.id,
            chat.title,
            chat.type
        )
        
        # Update welcome message
        db.db.groups.update_one(
            {"chat_id": chat.id},
            {"$set": {"welcome_message": welcome_message}}
        )
    
    # Send confirmation
    message.reply_html(
        f"<b>Welcome message updated!</b>\n\n"
        f"<b>New welcome message:</b>\n"
        f"{welcome_message}\n\n"
        f"<i>Preview of the welcome message:</i>\n"
        f"{format_welcome_message(welcome_message, update.effective_user, chat)}"
    )
    
    logger.info(f"Welcome message updated in {chat.id} by {update.effective_user.id}")

@admin_only
@send_typing
@log_command
def toggle_welcome(update: Update, context: CallbackContext) -> None:
    """Toggle welcome messages in the group."""
    message = update.message
    chat = update.effective_chat
    
    # Get group from database
    group = db.get_group(chat.id)
    
    if not group:
        # Create new group entry
        db.save_group(
            chat.id,
            chat.title,
            chat.type
        )
        
        message.reply_text("Welcome messages are now enabled for this group.")
        return
    
    # Toggle welcome_enabled
    welcome_enabled = not group.get("welcome_enabled", True)
    
    # Update in database
    db.db.groups.update_one(
        {"chat_id": chat.id},
        {"$set": {"welcome_enabled": welcome_enabled}}
    )
    
    # Send confirmation
    if welcome_enabled:
        message.reply_text("Welcome messages are now enabled for this group.")
    else:
        message.reply_text("Welcome messages are now disabled for this group.")
    
    logger.info(f"Welcome messages toggled to {welcome_enabled} in {chat.id} by {update.effective_user.id}")

def welcome_new_members(update: Update, context: CallbackContext) -> None:
    """Send welcome message when new users join."""
    # Skip if the bot itself joined
    if update.message.new_chat_members[0].id == context.bot.id:
        return
    
    chat = update.effective_chat
    
    # Get group from database
    group = db.get_group(chat.id)
    
    if not group or not group.get("welcome_enabled", True):
        return  # Welcome messages disabled
    
    # Get welcome message
    welcome_message = group.get("welcome_message", "Welcome to {chat_title}, {user_mention}!")
    
    # Send welcome for each new member
    for new_member in update.message.new_chat_members:
        # Skip welcome for bots
        if new_member.is_bot:
            continue
        
        # Format welcome message
        formatted_message = format_welcome_message(welcome_message, new_member, chat)
        
        # Create rules button if rules exist
        rules = db.get_setting(chat.id, "rules")
        if rules:
            keyboard = [[InlineKeyboardButton("Group Rules", callback_data="show_rules")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_html(formatted_message, reply_markup=reply_markup)
        else:
            update.message.reply_html(formatted_message)

def register_welcome_handlers(dispatcher):
    """Register welcome-related command handlers."""
    dispatcher.add_handler(CommandHandler("welcome", set_welcome))
    dispatcher.add_handler(CommandHandler("togglewelcome", toggle_welcome))
    dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, welcome_new_members))