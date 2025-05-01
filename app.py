import time
import os
import sys
from dotenv import load_dotenv
from telegram import Bot, Update, BotCommand
from telegram.ext import Updater, Dispatcher, CallbackContext
from telegram.utils.request import Request
from telegram.error import TelegramError
from loguru import logger

# Import configuration
from config import BOT_TOKEN, BOT_USERNAME, OWNER_ID

# Import handlers
from handlers import (
    register_admin_handlers,
    register_ban_handlers,
    register_basic_handlers,
    register_welcome_handlers,
    register_notes_handlers,
    register_filters_handlers
)

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("logs/bot_{time}.log", rotation="500 MB", retention="10 days", level="INFO")

logger.info("Starting bot...")

def setup_commands(dispatcher: Dispatcher) -> None:
    """Setup bot commands in telegram UI."""
    bot_commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("help", "Get help and list of commands"),
        BotCommand("ban", "Ban a user from the group"),
        BotCommand("unban", "Unban a user"),
        BotCommand("kick", "Kick a user without banning"),
        BotCommand("mute", "Mute a user"),
        BotCommand("unmute", "Unmute a user"),
        BotCommand("warn", "Warn a user"),
        BotCommand("unwarn", "Remove warnings from a user"),
        BotCommand("gban", "Globally ban a user (admin only)"),
        BotCommand("ungban", "Remove global ban (admin only)"),
        BotCommand("welcome", "Set a welcome message"),
        BotCommand("note", "Save a note"),
        BotCommand("get", "Get a saved note"),
        BotCommand("filter", "Add a word filter"),
        BotCommand("ping", "Check bot's response time"),
        BotCommand("info", "Get info about a user")
    ]
    
    try:
        dispatcher.bot.set_my_commands(bot_commands)
        logger.info("Bot commands have been set")
    except TelegramError as e:
        logger.error(f"Failed to set bot commands: {e}")

def main() -> None:
    """Start the bot."""
    # Load environment variables
    load_dotenv()
    
    if not BOT_TOKEN:
        logger.error("No bot token provided. Set the BOT_TOKEN environment variable.")
        sys.exit(1)
    
    # Create request with large connection pool
    request = Request(con_pool_size=8)
    
    # Create bot, updater and dispatcher with our custom request object
    bot = Bot(token=BOT_TOKEN, request=request)
    
    try:
        bot_info = bot.get_me()
        logger.info(f"Bot info: @{bot_info.username} (ID: {bot_info.id})")
    except TelegramError as e:
        logger.error(f"Failed to connect to Telegram: {e}")
        sys.exit(1)
    
    updater = Updater(bot=bot, use_context=True)
    dispatcher = updater.dispatcher
    
    # Store bot start time
    dispatcher.bot_data["uptime"] = time.time()
    
    # Register handlers
    register_basic_handlers(dispatcher)
    register_admin_handlers(dispatcher)
    register_ban_handlers(dispatcher)
    register_welcome_handlers(dispatcher)
    register_notes_handlers(dispatcher)
    register_filters_handlers(dispatcher)
    
    # Setup commands
    setup_commands(dispatcher)
    
    # Start the Bot
    if BOT_USERNAME:
        logger.info(f"Bot connected successfully! @{BOT_USERNAME}")
    else:
        logger.info("Bot connected successfully!")
    
    # Send startup message to owner
    if OWNER_ID:
        try:
            bot.send_message(
                chat_id=OWNER_ID,
                text=f"✅ Bot has been started!\nUptime: {time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        except TelegramError:
            logger.warning("Could not send startup message to owner")
    
    # Start polling
    updater.start_polling(drop_pending_updates=True)
    logger.info("Bot is polling for updates")
    
    # Run the bot until Ctrl-C
    updater.idle()
    logger.info("Bot is shutting down...")

if __name__ == "__main__":
    main()