#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from loguru import logger
from telethon import TelegramClient, events
from src.config import Config
from src.database import Database
from src.utils.logger import setup_logger
from src.handlers import register_all_handlers

async def main():
    """Main function to initialize and start the bot."""
    # Setup logging
    setup_logger()
    logger.info("Starting bot...")

    # Load configuration
    try:
        config = Config()
        logger.info("Configuration loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return

    # Initialize database connection
    try:
        database = Database(config.mongodb_uri)
        await database.connect()
        logger.info("Connected to MongoDB successfully")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        return

    # Initialize the Telegram client
    try:
        client = TelegramClient(
            "bot_session",
            api_id=config.api_id,
            api_hash=config.api_hash
        )
        await client.start(bot_token=config.bot_token)
        bot_info = await client.get_me()
        logger.info(f"Bot started as @{bot_info.username}")
    except Exception as e:
        logger.error(f"Failed to initialize Telegram client: {e}")
        return

    # Register all handlers
    try:
        register_all_handlers(client, database, config)
        logger.info("All handlers registered successfully")
    except Exception as e:
        logger.error(f"Failed to register handlers: {e}")
        return

    # Store the database and config in the client for easy access
    client.db = database
    client.config = config

    try:
        # Run the client until disconnected
        logger.info("Bot is running. Press Ctrl+C to stop")
        await client.run_until_disconnected()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        await database.disconnect()
        logger.info("Database connection closed")
        await client.disconnect()
        logger.info("Bot disconnected")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())