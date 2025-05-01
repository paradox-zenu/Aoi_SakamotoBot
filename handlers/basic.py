from telegram import Update, ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, Filters
from loguru import logger
from config import SUPPORT_CHAT, VERSION, OWNER_ID
from database import db
from utils.decorators import send_typing, log_command
from utils.helpers import get_readable_time

def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    chat_type = update.effective_chat.type
    
    # Save user to database
    db.save_user(
        user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    # Different responses based on chat type
    if chat_type == "private":
        keyboard = [
            [
                InlineKeyboardButton("➕ Add me to your group", url=f"https://t.me/{context.bot.username}?startgroup=true"),
                InlineKeyboardButton("📢 Support", url=f"https://t.me/{SUPPORT_CHAT}")
            ],
            [
                InlineKeyboardButton("📚 Commands", callback_data="help_main"),
                InlineKeyboardButton("🔍 About", callback_data="about")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        update.message.reply_html(
            f"Hello {user.mention_html()}! 👋\n\n"
            f"I'm a powerful group management bot with global ban capabilities. "
            f"I can help you manage your groups efficiently!\n\n"
            f"Click the buttons below to learn more or add me to your group.",
            reply_markup=reply_markup
        )
    else:
        # Save group to database
        db.save_group(
            update.effective_chat.id,
            update.effective_chat.title,
            update.effective_chat.type
        )
        
        update.message.reply_text(
            f"Hello there! I'm ready to help manage this group.\n"
            f"Use /help to see available commands."
        )

def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    chat_type = update.effective_chat.type
    
    help_text = (
        "🤖 <b>Available Commands</b>\n\n"
        "<b>Basic Commands:</b>\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/ping - Check bot's response time\n"
        "/info - Get info about a user\n\n"
        
        "<b>Admin Commands:</b>\n"
        "/ban - Ban a user\n"
        "/unban - Unban a user\n"
        "/kick - Kick a user\n"
        "/mute - Mute a user\n"
        "/unmute - Unmute a user\n"
        "/warn - Warn a user\n"
        "/unwarn - Remove warnings\n\n"
        
        "<b>Group Management:</b>\n"
        "/welcome - Set welcome message\n"
        "/rules - Set group rules\n"
        "/note - Save a note\n"
        "/get - Get a saved note\n"
        "/filter - Add a word filter\n\n"
        
        "<b>Global Commands (Admin only):</b>\n"
        "/gban - Globally ban a user\n"
        "/ungban - Remove global ban\n"
        "/stats - Show bot statistics\n"
    )
    
    if chat_type == "private":
        keyboard = [
            [
                InlineKeyboardButton("Admin Commands", callback_data="help_admin"),
                InlineKeyboardButton("User Commands", callback_data="help_user")
            ],
            [
                InlineKeyboardButton("Global Commands", callback_data="help_global"),
                InlineKeyboardButton("Back", callback_data="start")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        update.message.reply_html(help_text, reply_markup=reply_markup)
    else:
        update.message.reply_html(
            "Contact me in PM for the help menu!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Help", url=f"https://t.me/{context.bot.username}?start=help")]
            ])
        )

@send_typing
@log_command
def ping(update: Update, context: CallbackContext) -> None:
    """Check the bot's response time."""
    message = update.message
    start_time = message.date.timestamp()
    
    reply = message.reply_text("Pinging...")
    end_time = reply.date.timestamp()
    
    response_time = (end_time - start_time) * 1000
    
    reply.edit_text(
        f"🏓 Pong!\n"
        f"⏱ Response Time: {response_time:.2f}ms\n"
        f"🤖 Bot Uptime: {get_readable_time(context.bot_data.get('uptime', 0))}"
    )

@send_typing
@log_command
def info_command(update: Update, context: CallbackContext) -> None:
    """Get information about a user."""
    message = update.message
    chat = update.effective_chat
    
    # Check if the command is a reply to someone else
    if message.reply_to_message:
        user = message.reply_to_message.from_user
    elif len(context.args) > 0:
        # Try to get user by username or ID
        try:
            user_id = int(context.args[0]) if context.args[0].isdigit() else context.args[0]
            user = context.bot.get_chat_member(chat.id, user_id).user
        except Exception:
            message.reply_text("I couldn't find that user. Try replying to their message or use their ID/username.")
            return
    else:
        # If no arguments, show info about the command sender
        user = update.effective_user
    
    # Get user data from database
    user_data = db.get_user(user.id) or {}
    
    # Check if user is globally banned
    is_gbanned = db.is_user_gbanned(user.id)
    
    # Get user warnings if in a group
    warnings = []
    if chat.type != "private":
        warnings = db.get_warns(chat.id, user.id)
    
    # Create info message
    user_info = (
        f"👤 <b>User Info:</b>\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"🔖 Name: {user.mention_html()}\n"
    )
    
    if user.username:
        user_info += f"🔗 Username: @{user.username}\n"
    
    # Add warning count if applicable
    if warnings:
        user_info += f"⚠️ Warnings: {len(warnings)}\n"
    
    # Add global ban status
    if is_gbanned:
        ban_info = db.db.gbans.find_one({"user_id": user.id})
        user_info += (
            f"🚫 <b>This user is globally banned!</b>\n"
            f"📝 Reason: {ban_info.get('reason', 'No reason provided')}\n"
        )
    
    # Add special status (if any)
    if user.id == OWNER_ID:
        user_info += "👑 Status: Bot Owner\n"
    
    # Send the info
    message.reply_html(user_info)

@send_typing
def about(update: Update, context: CallbackContext) -> None:
    """Show information about the bot."""
    about_text = (
        f"<b>🤖 Bot Information</b>\n\n"
        f"Version: {VERSION}\n"
        f"Uptime: {get_readable_time(context.bot_data.get('uptime', 0))}\n\n"
        f"This bot combines the best features of @Lena_MilizeBot and @MissRose_Bot "
        f"with global ban capabilities to help you manage your Telegram groups effectively.\n\n"
        f"<b>Credits:</b>\n"
        f"• Built with python-telegram-bot\n"
        f"• MongoDB for database\n\n"
        f"<b>Support:</b> @{SUPPORT_CHAT}"
    )
    
    keyboard = [[InlineKeyboardButton("Back to Start", callback_data="start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_html(about_text, reply_markup=reply_markup)

def user_joined(update: Update, context: CallbackContext) -> None:
    """Log when users join and check for global bans."""
    for member in update.message.new_chat_members:
        if member.is_bot and member.id == context.bot.id:
            # Bot was added to a group
            db.save_group(
                update.effective_chat.id,
                update.effective_chat.title,
                update.effective_chat.type
            )
            logger.info(f"Bot added to group {update.effective_chat.title} ({update.effective_chat.id})")
            continue
            
        # Save user to database
        db.save_user(
            member.id,
            username=member.username,
            first_name=member.first_name,
            last_name=member.last_name
        )
        
        # Check if user is globally banned
        if db.is_user_gbanned(member.id):
            ban_info = db.db.gbans.find_one({"user_id": member.id})
            
            # Ban user and send message
            try:
                update.effective_chat.ban_member(member.id)
                update.effective_message.reply_html(
                    f"❌ <b>Banned user detected!</b>\n\n"
                    f"User {member.mention_html()} is globally banned and has been banned from this group.\n"
                    f"📝 Reason: {ban_info.get('reason', 'No reason provided')}"
                )
                logger.info(f"Banned globally banned user {member.id} from {update.effective_chat.id}")
            except Exception as e:
                logger.error(f"Failed to ban globally banned user: {e}")

def button_handler(update: Update, context: CallbackContext) -> None:
    """Handle callback queries from inline keyboards."""
    query = update.callback_query
    query.answer()
    
    # Get callback data
    data = query.data
    
    if data == "start":
        # Edit message with start menu
        keyboard = [
            [
                InlineKeyboardButton("➕ Add me to your group", url=f"https://t.me/{context.bot.username}?startgroup=true"),
                InlineKeyboardButton("📢 Support", url=f"https://t.me/{SUPPORT_CHAT}")
            ],
            [
                InlineKeyboardButton("📚 Commands", callback_data="help_main"),
                InlineKeyboardButton("🔍 About", callback_data="about")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(
            f"Hello {update.effective_user.mention_html()}! 👋\n\n"
            f"I'm a powerful group management bot with global ban capabilities. "
            f"I can help you manage your groups efficiently!\n\n"
            f"Click the buttons below to learn more or add me to your group.",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    
    elif data == "help_main":
        # Show main help menu
        help_text = (
            "🤖 <b>Available Commands</b>\n\n"
            "<b>Basic Commands:</b>\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n"
            "/ping - Check bot's response time\n"
            "/info - Get info about a user\n\n"
            
            "<b>Admin Commands:</b>\n"
            "/ban - Ban a user\n"
            "/unban - Unban a user\n"
            "/kick - Kick a user\n"
            "/mute - Mute a user\n"
            "/unmute - Unmute a user\n"
            "/warn - Warn a user\n"
            "/unwarn - Remove warnings\n\n"
            
            "<b>Group Management:</b>\n"
            "/welcome - Set welcome message\n"
            "/rules - Set group rules\n"
            "/note - Save a note\n"
            "/get - Get a saved note\n"
            "/filter - Add a word filter\n\n"
            
            "<b>Global Commands (Admin only):</b>\n"
            "/gban - Globally ban a user\n"
            "/ungban - Remove global ban\n"
            "/stats - Show bot statistics\n"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("Admin Commands", callback_data="help_admin"),
                InlineKeyboardButton("User Commands", callback_data="help_user")
            ],
            [
                InlineKeyboardButton("Global Commands", callback_data="help_global"),
                InlineKeyboardButton("Back", callback_data="start")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(help_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    elif data == "about":
        # Show about information
        about_text = (
            f"<b>🤖 Bot Information</b>\n\n"
            f"Version: {VERSION}\n"
            f"Uptime: {get_readable_time(context.bot_data.get('uptime', 0))}\n\n"
            f"This bot combines the best features of @Lena_MilizeBot and @MissRose_Bot "
            f"with global ban capabilities to help you manage your Telegram groups effectively.\n\n"
            f"<b>Credits:</b>\n"
            f"• Built with python-telegram-bot\n"
            f"• MongoDB for database\n\n"
            f"<b>Support:</b> @{SUPPORT_CHAT}"
        )
        
        keyboard = [[InlineKeyboardButton("Back to Start", callback_data="start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(about_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    # Helper pages
    elif data.startswith("help_"):
        category = data.split("_")[1]
        
        if category == "admin":
            text = (
                "<b>👮‍♂️ Admin Commands</b>\n\n"
                "/ban - Ban a user from the group\n"
                "/unban - Unban a user\n"
                "/kick - Kick a user without banning\n"
                "/mute - Restrict a user from sending messages\n"
                "/unmute - Allow a muted user to send messages\n"
                "/warn - Give a warning to a user\n"
                "/unwarn - Remove warnings from a user\n"
                "/promote - Promote a user to admin\n"
                "/demote - Demote an admin to regular user\n"
                "/pin - Pin a message in the chat\n"
                "/unpin - Unpin a message\n"
                "/purge - Delete multiple messages at once\n"
            )
        elif category == "user":
            text = (
                "<b>👤 User Commands</b>\n\n"
                "/start - Start the bot\n"
                "/help - Show help message\n"
                "/ping - Check bot's response time\n"
                "/info - Get info about a user\n"
                "/id - Get your user ID or chat ID\n"
                "/rules - View group rules\n"
                "/report - Report a user to admins\n"
                "/get - Get a saved note\n"
            )
        elif category == "global":
            text = (
                "<b>🌐 Global Commands</b>\n\n"
                "<i>These commands are restricted to bot admins:</i>\n\n"
                "/gban - Globally ban a user from all groups\n"
                "/ungban - Remove a user from global ban list\n"
                "/stats - Show bot statistics\n"
                "/broadcast - Send message to all chats\n"
                "/update - Update bot (owner only)\n"
                "/restart - Restart bot (owner only)\n"
            )
        else:
            text = "Invalid help category"
        
        keyboard = [[InlineKeyboardButton("Back to Help", callback_data="help_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

def register_basic_handlers(dispatcher):
    """Register basic command handlers."""
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("ping", ping))
    dispatcher.add_handler(CommandHandler("info", info_command))
    
    # Join handlers
    dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, user_joined))
    
    # Callback query handler for buttons
    dispatcher.add_handler(CallbackQueryHandler(button_handler))