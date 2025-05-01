#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telethon import events, Button
from loguru import logger

def register_basic_handlers(client, database, config):
    """Register basic command handlers.
    
    Args:
        client: Telethon client instance
        database: Database instance
        config: Config instance
    """
    
    @client.on(events.NewMessage(pattern=r"^[!?/]start$"))
    async def start_command(event):
        """Handler for the start command."""
        if event.is_private:
            # This is a private chat with the bot
            sender = await event.get_sender()
            
            # Get or create user in database
            user_data = await database.get_user(sender.id)
            if not user_data:
                user_data = {
                    "user_id": sender.id,
                    "first_name": sender.first_name,
                    "last_name": getattr(sender, "last_name", ""),
                    "username": getattr(sender, "username", ""),
                    "is_bot": sender.bot,
                    "created_at": datetime.now()
                }
                await database.save_user(user_data)
                logger.info(f"New user saved to database: {sender.id}")
            
            # Send welcome message
            bot_info = await client.get_me()
            welcome_text = (
                f"Hello {sender.first_name}! I'm {bot_info.first_name}, a group management bot.\n\n"
                f"I can help you manage your groups with various commands.\n"
                f"Add me to a group and make me admin to use my features."
            )
            
            buttons = [
                [Button.url("Add me to a group", f"https://t.me/{bot_info.username}?startgroup=start")],
                [Button.inline("Help", data="help_main")]
            ]
            
            await event.respond(welcome_text, buttons=buttons)
            logger.info(f"Start command executed by user {sender.id}")
        else:
            # This is a group chat
            chat = await event.get_chat()
            
            # Get or create chat in database
            chat_data = await database.get_chat(chat.id)
            if not chat_data:
                chat_data = {
                    "chat_id": chat.id,
                    "chat_title": chat.title,
                    "chat_type": "group" if hasattr(chat, "deactivated") else "supergroup",
                    "created_at": datetime.now()
                }
                await database.save_chat(chat_data)
                logger.info(f"New chat saved to database: {chat.id}")
            
            # Send welcome message
            bot_info = await client.get_me()
            welcome_text = (
                f"Hello! I'm {bot_info.first_name}, a group management bot.\n\n"
                f"Make sure I have the necessary admin permissions to function properly."
            )
            
            await event.respond(welcome_text)
            logger.info(f"Start command executed in chat {chat.id} by user {event.sender_id}")

    @client.on(events.CallbackQuery(data=lambda d: d.startswith(b"help_")))
    async def help_callback(event):
        """Handle help menu callbacks."""
        data = event.data.decode("utf-8")
        sender = await event.get_sender()
        
        if data == "help_main":
            text = (
                "**Available Commands**\n\n"
                "Choose a category to see more commands:"
            )
            
            buttons = [
                [Button.inline("Admin Commands", data="help_admin")],
                [Button.inline("Notes", data="help_notes")],
                [Button.inline("Filters", data="help_filters")],
                [Button.inline("Welcome", data="help_welcome")]
            ]
            
            await event.edit(text, buttons=buttons)
        
        elif data == "help_admin":
            text = (
                "**Admin Commands**\n\n"
                "• `/ban <user> [reason]` - Ban a user\n"
                "• `/unban <user>` - Unban a user\n"
                "• `/kick <user> [reason]` - Kick a user\n"
                "• `/mute <user> [duration] [reason]` - Mute a user\n"
                "• `/unmute <user>` - Unmute a user\n"
                "• `/pin` - Pin a message\n"
                "• `/unpin` - Unpin a message\n"
                "• `/unpinall` - Unpin all messages\n"
            )
            
            buttons = [[Button.inline("Back", data="help_main")]]
            
            await event.edit(text, buttons=buttons)
        
        elif data == "help_notes":
            text = (
                "**Notes Commands**\n\n"
                "• `/save <name> <content>` - Save a note\n"
                "• `/get <name>` - Get a note\n"
                "• `#<name>` - Get a note\n"
                "• `/notes` - List all notes\n"
                "• `/clear <name>` - Delete a note\n"
            )
            
            buttons = [[Button.inline("Back", data="help_main")]]
            
            await event.edit(text, buttons=buttons)
        
        elif data == "help_filters":
            text = (
                "**Filters Commands**\n\n"
                "• `/filter <keyword> <content>` - Add a filter\n"
                "• `/filters` - List all filters\n"
                "• `/stop <keyword>` - Delete a filter\n"
            )
            
            buttons = [[Button.inline("Back", data="help_main")]]
            
            await event.edit(text, buttons=buttons)
        
        elif data == "help_welcome":
            text = (
                "**Welcome Commands**\n\n"
                "• `/setwelcome <message>` - Set welcome message\n"
                "• `/welcome on/off` - Toggle welcome messages\n"
                "• `/welcome` - Show current welcome settings\n"
                "• `/resetwelcome` - Reset to default welcome\n"
            )
            
            buttons = [[Button.inline("Back", data="help_main")]]
            
            await event.edit(text, buttons=buttons)
        
        logger.info(f"Help menu {data} viewed by user {sender.id}")
        await event.answer()
    
    @client.on(events.NewMessage(pattern=r"^[!?/]help$"))
    async def help_command(event):
        """Handler for the help command."""
        # Send the main help menu
        text = (
            "**Available Commands**\n\n"
            "Choose a category to see more commands:"
        )
        
        buttons = [
            [Button.inline("Admin Commands", data="help_admin")],
            [Button.inline("Notes", data="help_notes")],
            [Button.inline("Filters", data="help_filters")],
            [Button.inline("Welcome", data="help_welcome")]
        ]
        
        await event.respond(text, buttons=buttons)
        logger.info(f"Help command executed by user {event.sender_id}")
    
    @client.on(events.NewMessage(pattern=r"^[!?/]ping$"))
    async def ping_command(event):
        """Handler for the ping command."""
        start_time = datetime.now()
        message = await event.respond("Pong!")
        end_time = datetime.now()
        
        # Calculate the round-trip time in milliseconds
        ping_time = (end_time - start_time).total_seconds() * 1000
        
        await message.edit(f"Pong! Response time: {ping_time:.2f}ms")
        logger.info(f"Ping command executed by user {event.sender_id}, response time: {ping_time:.2f}ms")

    @client.on(events.NewMessage(pattern=r"^[!?/]id$"))
    async def id_command(event):
        """Handler for the id command."""
        # Check if the command is a reply to a message
        if event.reply_to_msg_id:
            # Get the replied message
            replied_msg = await event.get_reply_message()
            from_user = await replied_msg.get_sender()
            
            # Build the response text
            text = f"User ID: `{from_user.id}`"
            if hasattr(from_user, "username") and from_user.username:
                text += f"\nUsername: @{from_user.username}"
            
            await event.respond(text)
        else:
            # Get information about the sender and the chat
            chat = await event.get_chat()
            
            # Build the response text
            if event.is_private:
                # Private chat
                sender = await event.get_sender()
                text = f"Your user ID: `{sender.id}`"
                if hasattr(sender, "username") and sender.username:
                    text += f"\nYour username: @{sender.username}"
            else:
                # Group or channel
                text = f"Chat ID: `{chat.id}`"
                if hasattr(chat, "username") and chat.username:
                    text += f"\nChat username: @{chat.username}"
                
                sender = await event.get_sender()
                text += f"\n\nYour user ID: `{sender.id}`"
                if hasattr(sender, "username") and sender.username:
                    text += f"\nYour username: @{sender.username}"
            
            await event.respond(text)
        
        logger.info(f"ID command executed by user {event.sender_id}")

    @client.on(events.NewMessage(pattern=r"^[!?/]info$"))
    async def info_command(event):
        """Handler for the info command."""
        # Check if the command is a reply to a message
        if event.reply_to_msg_id:
            # Get the replied message
            replied_msg = await event.get_reply_message()
            target_user = await replied_msg.get_sender()
        else:
            # If no reply, use the sender
            target_user = await event.get_sender()
        
        # Build the info text
        text = f"**User Info**\n\n"
        text += f"**ID:** `{target_user.id}`\n"
        text += f"**First Name:** {target_user.first_name}\n"
        
        if hasattr(target_user, "last_name") and target_user.last_name:
            text += f"**Last Name:** {target_user.last_name}\n"
        
        if hasattr(target_user, "username") and target_user.username:
            text += f"**Username:** @{target_user.username}\n"
        
        # Check if the user is a bot
        text += f"**Bot:** {'Yes' if target_user.bot else 'No'}\n"
        
        # Check if user is restricted or deleted
        if hasattr(target_user, "restricted") and target_user.restricted:
            text += "**Account Status:** Restricted\n"
        elif hasattr(target_user, "deleted") and target_user.deleted:
            text += "**Account Status:** Deleted\n"
        else:
            text += "**Account Status:** Active\n"
        
        # Add a clickable mention
        text += f"\n[User Link](tg://user?id={target_user.id})"
        
        # Get the user's profile photo
        try:
            profile_photo = await client.download_profile_photo(target_user.id, bytes)
            if profile_photo:
                await event.respond(text, file=profile_photo)
            else:
                await event.respond(text)
        except Exception as e:
            logger.error(f"Error getting profile photo: {e}")
            await event.respond(text)
        
        logger.info(f"Info command executed by user {event.sender_id}")