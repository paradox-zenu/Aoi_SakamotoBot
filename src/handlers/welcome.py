#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telethon import events
from loguru import logger
from typing import Dict, Optional
from datetime import datetime

def register_welcome_handlers(client, database, config):
    """Register welcome message handlers.
    
    Args:
        client: Telethon client instance
        database: Database instance
        config: Config instance
    """
    
    @client.on(events.ChatAction())
    async def welcome_handler(event):
        """Handler for welcome messages when users join the chat."""
        # Only trigger on user joins
        if not (event.user_joined or event.user_added):
            return
        
        # Skip in private chats
        if event.is_private:
            return
        
        # Get chat settings
        chat = await event.get_chat()
        chat_data = await database.get_chat(chat.id)
        
        if not chat_data:
            # Create a default chat entry if it doesn't exist
            chat_data = {
                "chat_id": chat.id,
                "chat_title": chat.title,
                "welcome_enabled": True,
                "welcome_message": "Welcome to {chat_title}, {mention}!",
                "created_at": datetime.now()
            }
            await database.save_chat(chat_data)
        
        # Check if welcome messages are enabled
        if not chat_data.get("welcome_enabled", True):
            return
        
        # Get the welcome message template
        welcome_message = chat_data.get("welcome_message", "Welcome to {chat_title}, {mention}!")
        
        # Get the user who joined
        user_id = event.user_id
        try:
            user = await client.get_entity(user_id)
        except Exception as e:
            logger.error(f"Error getting user entity: {e}")
            return
        
        # Format the welcome message
        try:
            formatted_message = _format_welcome_message(welcome_message, user, chat)
            
            # Send the welcome message
            await event.respond(formatted_message, parse_mode="html")
            logger.info(f"Welcome message sent in chat {chat.id} for user {user_id}")
        except Exception as e:
            logger.error(f"Error sending welcome message: {e}")

    @client.on(events.NewMessage(pattern=r"^[!?/]setwelcome(?:\s+(.+))?$"))
    async def setwelcome_command(event):
        """Handler for the setwelcome command."""
        # Check if the event is in a private chat
        if event.is_private:
            await event.respond("Welcome messages can only be set in groups.")
            return
        
        # Check if the user has permission to set welcome message
        if not await _check_admin_rights(event, client):
            await event.respond("You need to be an admin to set welcome messages.")
            return
        
        # Get command arguments
        args = event.pattern_match.group(1)
        
        # If no arguments provided, check if the command is a reply to a message
        if not args:
            if event.reply_to_msg_id:
                replied_msg = await event.get_reply_message()
                welcome_message = replied_msg.text or replied_msg.caption or ""
            else:
                await event.respond(
                    "Please provide a welcome message or reply to a message.\n\n"
                    "You can use these placeholders:\n"
                    "- `{mention}`: Mention the user\n"
                    "- `{first}`: User's first name\n"
                    "- `{last}`: User's last name\n"
                    "- `{fullname}`: User's full name\n"
                    "- `{username}`: User's username\n"
                    "- `{id}`: User's ID\n"
                    "- `{chat_title}`: The chat's title\n"
                    "- `{chat_id}`: The chat's ID\n"
                )
                return
        else:
            welcome_message = args
        
        # Update the chat settings
        chat = await event.get_chat()
        chat_data = await database.get_chat(chat.id)
        
        if not chat_data:
            chat_data = {
                "chat_id": chat.id,
                "chat_title": chat.title,
                "welcome_enabled": True,
                "created_at": datetime.now()
            }
        
        chat_data["welcome_message"] = welcome_message
        await database.save_chat(chat_data)
        
        # Show a preview of the welcome message
        user = await event.get_sender()
        preview = _format_welcome_message(welcome_message, user, chat)
        
        await event.respond(
            f"Welcome message has been set. Here's a preview:\n\n{preview}",
            parse_mode="html"
        )
        logger.info(f"Welcome message set in chat {chat.id} by user {event.sender_id}")

    @client.on(events.NewMessage(pattern=r"^[!?/]welcome(\s+.*)?$"))
    async def welcome_command(event):
        """Handler for the welcome command."""
        # Check if the event is in a private chat
        if event.is_private:
            await event.respond("Welcome settings can only be managed in groups.")
            return
        
        # Get command arguments
        args = event.pattern_match.group(1)
        args = args.strip() if args else None
        
        # Get chat settings
        chat = await event.get_chat()
        chat_data = await database.get_chat(chat.id)
        
        if not chat_data:
            chat_data = {
                "chat_id": chat.id,
                "chat_title": chat.title,
                "welcome_enabled": True,
                "welcome_message": "Welcome to {chat_title}, {mention}!",
                "created_at": datetime.now()
            }
            await database.save_chat(chat_data)
        
        # If no arguments, show current settings
        if not args:
            welcome_enabled = chat_data.get("welcome_enabled", True)
            welcome_message = chat_data.get("welcome_message", "Welcome to {chat_title}, {mention}!")
            
            status = "enabled" if welcome_enabled else "disabled"
            
            # Show a preview of the current welcome message
            user = await event.get_sender()
            preview = _format_welcome_message(welcome_message, user, chat)
            
            await event.respond(
                f"**Welcome Settings:**\n\n"
                f"Status: {status}\n\n"
                f"Current welcome message:\n{preview}\n\n"
                f"To change settings:\n"
                f"- `/welcome on` or `/welcome off` to toggle\n"
                f"- `/setwelcome <message>` to change the message",
                parse_mode="html"
            )
            return
        
        # Check if the user has permission to change welcome settings
        if not await _check_admin_rights(event, client):
            await event.respond("You need to be an admin to change welcome settings.")
            return
        
        # Handle welcome on/off
        if args.lower() == "on":
            chat_data["welcome_enabled"] = True
            await database.save_chat(chat_data)
            await event.respond("Welcome messages are now enabled.")
            logger.info(f"Welcome messages enabled in chat {chat.id} by user {event.sender_id}")
        elif args.lower() == "off":
            chat_data["welcome_enabled"] = False
            await database.save_chat(chat_data)
            await event.respond("Welcome messages are now disabled.")
            logger.info(f"Welcome messages disabled in chat {chat.id} by user {event.sender_id}")
        else:
            await event.respond("Invalid option. Use `/welcome on` or `/welcome off`.")

    @client.on(events.NewMessage(pattern=r"^[!?/]resetwelcome$"))
    async def resetwelcome_command(event):
        """Handler for the resetwelcome command."""
        # Check if the event is in a private chat
        if event.is_private:
            await event.respond("Welcome messages can only be reset in groups.")
            return
        
        # Check if the user has permission to reset welcome message
        if not await _check_admin_rights(event, client):
            await event.respond("You need to be an admin to reset welcome messages.")
            return
        
        # Reset the welcome message to default
        chat = await event.get_chat()
        chat_data = await database.get_chat(chat.id)
        
        if not chat_data:
            chat_data = {
                "chat_id": chat.id,
                "chat_title": chat.title,
                "welcome_enabled": True,
                "created_at": datetime.now()
            }
        
        chat_data["welcome_message"] = "Welcome to {chat_title}, {mention}!"
        await database.save_chat(chat_data)
        
        # Show a preview of the default welcome message
        user = await event.get_sender()
        preview = _format_welcome_message("Welcome to {chat_title}, {mention}!", user, chat)
        
        await event.respond(
            f"Welcome message has been reset to default. Here's a preview:\n\n{preview}",
            parse_mode="html"
        )
        logger.info(f"Welcome message reset in chat {chat.id} by user {event.sender_id}")
    
    # Helper functions
    async def _check_admin_rights(event, client):
        """Check if the user has admin rights in the chat."""
        # Get chat and sender
        chat = await event.get_chat()
        sender = await event.get_sender()
        
        # Always allow in private chats
        if event.is_private:
            return True
        
        try:
            # Get chat permissions
            participant = await client.get_permissions(chat, sender)
            
            # Check if user is admin or creator
            return participant.is_admin or participant.is_creator
        except Exception as e:
            logger.error(f"Error checking admin rights: {e}")
            return False

    def _format_welcome_message(template, user, chat):
        """Format a welcome message with placeholders."""
        # Get user attributes
        first_name = user.first_name or ""
        last_name = getattr(user, "last_name", "") or ""
        fullname = f"{first_name} {last_name}".strip()
        username = f"@{user.username}" if getattr(user, "username", None) else ""
        mention = f"<a href='tg://user?id={user.id}'>{first_name}</a>"
        user_id = user.id
        
        # Get chat attributes
        chat_title = chat.title
        chat_id = chat.id
        
        # Replace placeholders
        message = template
        message = message.replace("{mention}", mention)
        message = message.replace("{first}", first_name)
        message = message.replace("{last}", last_name)
        message = message.replace("{fullname}", fullname)
        message = message.replace("{username}", username)
        message = message.replace("{id}", str(user_id))
        message = message.replace("{chat_title}", chat_title)
        message = message.replace("{chat_id}", str(chat_id))
        
        return message