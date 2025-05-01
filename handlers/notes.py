from telegram import Update, ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, Filters
from loguru import logger
from database import db
from utils.decorators import admin_only, send_typing, log_command

@admin_only
@send_typing
@log_command
def save_note(update: Update, context: CallbackContext) -> None:
    """Save a note for the chat."""
    message = update.message
    chat = update.effective_chat
    user = update.effective_user
    
    # Check if note name and content are provided
    if not context.args:
        message.reply_text(
            "Please provide a name for the note.\n\n"
            "Example: /save example This is an example note"
        )
        return
    
    # Get note name and content
    note_name = context.args[0].lower()
    
    # Check for content
    if len(context.args) < 2 and not message.reply_to_message:
        message.reply_text("Please provide content for the note or reply to a message.")
        return
    
    # Get content from reply or arguments
    if message.reply_to_message:
        if message.reply_to_message.text:
            content = message.reply_to_message.text_html
        elif message.reply_to_message.caption:
            content = message.reply_to_message.caption_html
        else:
            message.reply_text("I can only save text messages as notes.")
            return
    else:
        content = " ".join(context.args[1:])
    
    # Save note to database
    db.save_note(chat.id, note_name, content, user.id)
    
    # Send confirmation
    message.reply_html(
        f"✅ Note <code>{note_name}</code> saved successfully!"
    )
    
    logger.info(f"Note '{note_name}' saved in {chat.id} by {user.id}")

@send_typing
def get_note(update: Update, context: CallbackContext) -> None:
    """Get a saved note."""
    message = update.message
    chat = update.effective_chat
    
    # Check if note name is provided
    if not context.args:
        message.reply_text(
            "Please specify which note you want to get.\n\n"
            "Example: /get example"
        )
        return
    
    # Get note name
    note_name = context.args[0].lower()
    
    # Get note from database
    note = db.get_note(chat.id, note_name)
    
    if not note:
        message.reply_text(f"There is no note saved with name '{note_name}'.")
        return
    
    # Send the note
    message.reply_html(note["content"])

@send_typing
def get_note_hashtag(update: Update, context: CallbackContext) -> None:
    """Get a note using #notename format."""
    message = update.message
    chat = update.effective_chat
    text = message.text
    
    # Check if message starts with a hashtag
    if not text or not text.startswith("#"):
        return
    
    # Get note name
    note_name = text[1:].lower().split()[0]
    
    # Get note from database
    note = db.get_note(chat.id, note_name)
    
    if not note:
        return  # Silently ignore if note doesn't exist
    
    # Send the note
    message.reply_html(note["content"])

@admin_only
@send_typing
@log_command
def delete_note(update: Update, context: CallbackContext) -> None:
    """Delete a saved note."""
    message = update.message
    chat = update.effective_chat
    user = update.effective_user
    
    # Check if note name is provided
    if not context.args:
        message.reply_text(
            "Please specify which note you want to delete.\n\n"
            "Example: /delnote example"
        )
        return
    
    # Get note name
    note_name = context.args[0].lower()
    
    # Check if note exists
    note = db.get_note(chat.id, note_name)
    
    if not note:
        message.reply_text(f"There is no note saved with name '{note_name}'.")
        return
    
    # Delete note
    db.delete_note(chat.id, note_name)
    
    # Send confirmation
    message.reply_html(
        f"✅ Note <code>{note_name}</code> deleted successfully!"
    )
    
    logger.info(f"Note '{note_name}' deleted from {chat.id} by {user.id}")

@send_typing
def list_notes(update: Update, context: CallbackContext) -> None:
    """List all saved notes in the chat."""
    message = update.message
    chat = update.effective_chat
    
    # Get all notes for this chat
    notes = db.get_all_notes(chat.id)
    
    if not notes:
        message.reply_text("There are no saved notes in this chat.")
        return
    
    # Create notes list
    notes_text = "<b>Notes in this chat:</b>\n"
    for i, note in enumerate(notes, 1):
        notes_text += f"{i}. <code>{note['note_name']}</code>\n"
    
    notes_text += "\nYou can get these notes by using /get notename or #notename"
    
    # Send the list
    message.reply_html(notes_text)

def register_notes_handlers(dispatcher):
    """Register notes-related command handlers."""
    dispatcher.add_handler(CommandHandler("save", save_note))
    dispatcher.add_handler(CommandHandler("note", save_note))  # Alias for save
    dispatcher.add_handler(CommandHandler("get", get_note))
    dispatcher.add_handler(CommandHandler("delnote", delete_note))
    dispatcher.add_handler(CommandHandler("notes", list_notes))
    
    # Handle #note format
    dispatcher.add_handler(MessageHandler(Filters.regex(r"^#[a-zA-Z0-9_]+"), get_note_hashtag))