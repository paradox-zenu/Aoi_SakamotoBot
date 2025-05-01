#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telethon import events
from loguru import logger
import traceback
import sys
import asyncio
from typing import Optional, Dict, Any, Type
from datetime import datetime

def register_error_handlers(client, database, config):
    """Register error handlers for exception handling.
    
    Args:
        client: Telethon client instance
        database: Database instance
        config: Config instance
    """
    
    async def log_error(error_type: str, error: Exception, event: Optional[events.NewMessage] = None, context: Optional[Dict[str, Any]] = None) -> None:
        """Log an error to both the logger and database.
        
        Args:
            error_type: Type of error (e.g., "Event Handler", "System")
            error: The exception that occurred
            event: Optional event that triggered the error
            context: Optional additional context
        """
        try:
            error_data = {
                "type": error_type,
                "error": str(error),
                "traceback": traceback.format_exc(),
                "timestamp": datetime.utcnow()
            }
            
            if event:
                error_data.update({
                    "chat_id": event.chat_id,
                    "user_id": event.sender_id,
                    "message_id": event.id,
                    "event_type": event.event_type
                })
            
            if context:
                error_data.update(context)
            
            # Log to database
            await client.db.errors.insert_one(error_data)
            
            # Log to file
            logger.error(f"{error_type} Error: {error}")
            logger.error(traceback.format_exc())
            
            # Notify owner if critical
            if _is_critical_error(error):
                await _notify_owner(client, config, error_type, error, error_data)
                
        except Exception as e:
            logger.error(f"Error in error logging: {e}")
    
    @client.on(events.NewMessage)
    async def handle_errors(event):
        """Global error handler for all message events."""
        try:
            # Let the event be processed normally
            await event.continue_propagation()
        except Exception as e:
            # Log the error
            await log_error("Event Handler", e, event)
            
            # Send user-friendly message
            try:
                await event.respond(
                    "An error occurred while processing your request. "
                    "The bot administrators have been notified."
                )
            except Exception as respond_error:
                logger.error(f"Failed to send error message: {respond_error}")

    # Override the default error handler for telethon
    client.add_event_handler(
        handle_errors,
        events.NewMessage()
    )
    
    # Set up a system-wide exception hook
    def handle_uncaught_exception(exc_type: Type[BaseException], exc_value: BaseException, exc_traceback: traceback.TracebackType) -> None:
        """Handle uncaught exceptions at the system level."""
        if issubclass(exc_type, KeyboardInterrupt):
            # Pass through keyboard interrupt for clean shutdown
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        # Log the exception
        asyncio.create_task(
            log_error(
                "System",
                exc_value,
                context={
                    "exc_type": exc_type.__name__,
                    "traceback": "".join(traceback.format_tb(exc_traceback))
                }
            )
        )
    
    # Set the system exception hook
    sys.excepthook = handle_uncaught_exception
    
    # Helper functions
    def _is_critical_error(error: Exception) -> bool:
        """Determine if an error is critical and requires immediate attention."""
        critical_types = (
            PermissionError,
            ConnectionError,
            OSError,
            MemoryError,
            SystemError
        )
        
        return isinstance(error, critical_types) or any(
            str(critical_type.__name__) in str(error.__class__)
            for critical_type in critical_types
        )
    
    async def _notify_owner(client, config, error_type: str, error: Exception, error_data: Dict[str, Any]) -> None:
        """Send a notification to the bot owner about a critical error."""
        if not config.owner_id:
            return
        
        try:
            # Ensure the client is connected
            if not client.is_connected():
                await client.connect()
            
            # Build the error message
            error_message = (
                f"⚠️ **Critical {error_type} Error**\n\n"
                f"**Error Type:** {error.__class__.__name__}\n"
                f"**Error Message:** {str(error)}\n\n"
            )
            
            if "chat_id" in error_data:
                error_message += f"**Chat ID:** `{error_data['chat_id']}`\n"
            if "user_id" in error_data:
                error_message += f"**User ID:** `{error_data['user_id']}`\n"
            
            error_message += f"\n**Traceback:**\n```{error_data['traceback'][:1000]}```"
            
            # Send the message to the owner
            await client.send_message(
                config.owner_id,
                error_message,
                parse_mode="markdown"
            )
        except Exception as e:
            logger.error(f"Failed to notify owner about critical error: {e}")
    
    # Initialize error collection in database
    async def init_error_collection():
        """Initialize the errors collection with proper indexes."""
        try:
            await client.db.errors.create_index([("timestamp", -1)])
            await client.db.errors.create_index([("type", 1)])
            await client.db.errors.create_index([("chat_id", 1)])
            await client.db.errors.create_index([("user_id", 1)])
        except Exception as e:
            logger.error(f"Failed to initialize error collection: {e}")
    
    # Run initialization
    asyncio.create_task(init_error_collection())