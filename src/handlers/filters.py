#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telethon import events
from loguru import logger
import re
from typing import Dict, List, Optional

def register_filters_handlers(client, database, config):
    """Register filters command handlers.
    
    Args:
        client: Telethon client instance
        database: Database instance
        config: Config instance
    """
    
    @client.on(events.NewMessage(pattern=r"^[!?/]filter(?:\s+(.+))?$"))
    async def filter_command(event):
        """Handler for the filter command."""
        # Check if the event is in a private chat (we only allow filters in groups)
        if event.is_private:
            await event.respond("Filters can only be used in groups.")
            return
        
        # Check if the user has permission to add filters
        if not await _check_admin_rights(event, client):
            await event.respond("You need to be an admin to add filters.")
            return
        
        # Get command arguments
        args = event.pattern_match.group(1)
        if not args:
            await event.respond("Please provide a keyword and response.\nUsage: `/filter keyword response`")
            return
        
        # Split into keyword and response
        parts = args.split(maxsplit=1)
        if len(parts) < 2:
            # Check if it's a reply
            if event.reply_to_msg_id:
                keyword = parts[0].lower()
                replied_msg = await event.get_reply_message()
                response = replied_msg.text or replied_msg.caption or ""
                
                # Check for media
                media = None
                if replied_msg.media:
                    media = {
                        "type": _get_media_type(replied_msg),
                        "file_id": _get_file_id(replied_msg)
                    }
            else:
                await event.respond("Please provide a response or reply to a message.\nUsage: `/filter keyword response`")
                return
        else:
            keyword = parts[0].lower()
            response = parts[1]
            media = None
        
        # Save the filter
        chat = await event.get_chat()
        sender = await event.get_sender()
        
        filter_data = {
            "keyword": keyword,
            "response": response,
            "media": media,
            "created_by": sender.id,
            "created_at": datetime.now()
        }
        
        await database.save_filter(chat.id, keyword, filter_data)
        
        await event.respond(f"Filter for `{keyword}` saved successfully.")
        logger.info(f"Filter '{keyword}' saved in chat {chat.id} by user {sender.id}")

    @client.on(events.NewMessage(pattern=r"^[!?/]filters$"))
    async def list_filters_command(event):
        """Handler for the list filters command."""
        # Check if the event is in a private chat (filters are per-group)
        if event.is_private:
            await event.respond("Filters can only be listed in groups.")
            return
        
        # Retrieve all filters for the chat
        chat = await event.get_chat()
        filters = await database.get_all_filters(chat.id)
        
        if not filters:
            await event.respond("No filters saved in this chat.")
            return
        
        # Build the response message
        response = "**Filters in this chat:**\n\n"
        for i, filter_item in enumerate(filters, 1):
            keyword = filter_item.get("keyword", "unknown")
            response += f"{i}. `{keyword}`\n"
        
        await event.respond(response)
        logger.info(f"Filters listed in chat {chat.id} by user {event.sender_id}")

    @client.on(events.NewMessage(pattern=r"^[!?/]stop(?:\s+(.+))?$"))
    async def stop_filter_command(event):
        """Handler for the stop filter command."""
        # Check if the event is in a private chat (we only allow filters in groups)
        if event.is_private:
            await event.respond("Filters can only be stopped in groups.")
            return
        
        # Check if the user has permission to stop filters
        if not await _check_admin_rights(event, client):
            await event.respond("You need to be an admin to stop filters.")
            return
        
        # Get command arguments
        args = event.pattern_match.group(1)
        if not args:
            await event.respond("Please provide a filter keyword.\nUsage: `/stop keyword`")
            return
        
        # Get the keyword
        keyword = args.lower()
        
        # Delete the filter
        chat = await event.get_chat()
        success = await database.delete_filter(chat.id, keyword)
        
        if success:
            await event.respond(f"Filter `{keyword}` has been stopped.")
            logger.info(f"Filter '{keyword}' stopped in chat {chat.id} by user {event.sender_id}")
        else:
            await event.respond(f"Filter `{keyword}` not found.")

    @client.on(events.NewMessage())
    async def check_filters(event):
        """Handler to check if a message matches any filters."""
        # Ignore commands, private chats, and messages from the bot itself
        if event.is_private or event.out or event.raw_text.startswith(("/", "!", "?")):
            return
        
        # Get all filters for the chat
        chat = await event.get_chat()
        filters = await database.get_all_filters(chat.id)
        
        if not filters:
            return
        
        # Check if message matches any filters
        message_text = event.raw_text.lower()
        
        for filter_item in filters:
            keyword = filter_item.get("keyword", "").lower()
            if not keyword:
                continue
            
            # Check if keyword matches as a word (not part of another word)
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, message_text):
                # Send the filter response
                await _send_filter_response(event, client, filter_item)
                logger.info(f"Filter '{keyword}' triggered in chat {chat.id} by message from {event.sender_id}")
                break
    
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

    async def _send_filter_response(event, client, filter_item):
        """Send a filter's response with any associated media."""
        response = filter_item.get("response", "")
        media = filter_item.get("media")
        
        try:
            if media:
                # Handle media filters
                media_type = media.get("type")
                file_id = media.get("file_id")
                
                if file_id:
                    # We would need to handle file_id retrieval based on your storage method
                    # This is a simplified example
                    await event.respond(response, file=file_id)
                else:
                    await event.respond(response)
            else:
                # Text-only filter
                await event.respond(response)
        except Exception as e:
            logger.error(f"Error sending filter response: {e}")

    def _get_media_type(message):
        """Get the type of media from a message."""
        if message.photo:
            return "photo"
        elif message.document:
            return "document"
        elif message.audio:
            return "audio"
        elif message.video:
            return "video"
        elif message.sticker:
            return "sticker"
        elif message.voice:
            return "voice"
        elif message.video_note:
            return "video_note"
        else:
            return None

    def _get_file_id(message):
        """Get the file_id from a message with media."""
        # This is a placeholder - actual implementation depends on how you store files
        # For simplicity, we're just returning a reference to the message
        return f"{message.chat_id}:{message.id}"