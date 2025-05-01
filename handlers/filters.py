from telegram import Update, ParseMode
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, Filters
from loguru import logger
from database import db
from utils.decorators import admin_only, send_typing, log_command

@admin_only
@send_typing
@log_command
def add_filter(update: Update, context: CallbackContext) -> None:
    """Add a filter to the chat."""
    message = update.message
    chat = update.effective_chat
    user = update.effective_user
    
    # Check if filter keyword and response are provided
    if not context.args:
        message.reply_text(
            "Please provide a keyword and response for the filter.\n\n"
            "Example: /filter hello Hello there!"
        )
        return
    
    # Get filter keyword and response
    keyword = context.args[0].lower()
    
    # Check for response
    if len(context.args) < 2 and not message.reply_to_message:
        message.reply_text("Please provide a response for the filter or reply to a message.")
        return
    
    # Get response from reply or arguments
    if message.reply_to_message:
        if message.reply_to_message.text:
            response = message.reply_to_message.text_html
        elif message.reply_to_message.caption:
            response = message.reply_to_message.caption_html
        else:
            message.reply_text("I can only save text messages as filter responses.")
            return
    else:
        response = " ".join(context.args[1:])
    
    # Save filter to database
    db.db.filters.update_one(
        {"chat_id": chat.id, "filter_name": keyword},
        {"$set": {
            "chat_id": chat.id,
            "filter_name": keyword,
            "response": response,
            "created_by": user.id
        }},
        upsert=True
    )
    
    # Send confirmation
    message.reply_html(
        f"✅ Filter <code>{keyword}</code> added successfully!"
    )
    
    logger.info(f"Filter '{keyword}' added in {chat.id} by {user.id}")

@admin_only
@send_typing
@log_command
def remove_filter(update: Update, context: CallbackContext) -> None:
    """Remove a filter from the chat."""
    message = update.message
    chat = update.effective_chat
    user = update.effective_user
    
    # Check if filter keyword is provided
    if not context.args:
        message.reply_text(
            "Please specify which filter you want to remove.\n\n"
            "Example: /stopfilter hello"
        )
        return
    
    # Get filter keyword
    keyword = context.args[0].lower()
    
    # Check if filter exists
    filter_data = db.db.filters.find_one({"chat_id": chat.id, "filter_name": keyword})
    
    if not filter_data:
        message.reply_text(f"There is no filter for '{keyword}' in this chat.")
        return
    
    # Remove filter
    db.db.filters.delete_one({"chat_id": chat.id, "filter_name": keyword})
    
    # Send confirmation
    message.reply_html(
        f"✅ Filter <code>{keyword}</code> removed successfully!"
    )
    
    logger.info(f"Filter '{keyword}' removed from {chat.id} by {user.id}")

@send_typing
def list_filters(update: Update, context: CallbackContext) -> None:
    """List all filters in the chat."""
    message = update.message
    chat = update.effective_chat
    
    # Get all filters for this chat
    filters = list(db.db.filters.find({"chat_id": chat.id}))
    
    if not filters:
        message.reply_text("There are no filters in this chat.")
        return
    
    # Create filters list
    filters_text = "<b>Filters in this chat:</b>\n"
    for i, filter_data in enumerate(filters, 1):
        filters_text += f"{i}. <code>{filter_data['filter_name']}</code>\n"
    
    # Send the list
    message.reply_html(filters_text)

def handle_filters(update: Update, context: CallbackContext) -> None:
    """Handle incoming messages and check for filters."""
    message = update.message
    chat = update.effective_chat
    
    # Skip empty messages
    if not message.text:
        return
    
    # Get all filters for this chat
    filters = list(db.db.filters.find({"chat_id": chat.id}))
    
    if not filters:
        return  # No filters for this chat
    
    # Check if message contains any filter keywords
    text = message.text.lower()
    
    for filter_data in filters:
        keyword = filter_data["filter_name"].lower()
        
        # Check if keyword is in message
        if keyword in text.split():
            # Send the filter response
            message.reply_html(filter_data["response"])
            return  # Only respond to the first matching filter

def register_filters_handlers(dispatcher):
    """Register filters-related command handlers."""
    dispatcher.add_handler(CommandHandler("filter", add_filter))
    dispatcher.add_handler(CommandHandler("stopfilter", remove_filter))
    dispatcher.add_handler(CommandHandler("filters", list_filters))
    
    # Handle messages for filters (lower priority)
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_filters), group=1)