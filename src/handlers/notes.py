#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telethon import events, Button
from loguru import logger
from typing import Dict, List, Optional

def register_notes_handlers(client, database, config):
    """Register notes command handlers.
    
    Args:
        client: Telethon client instance
        database: Database instance
        config: Config instance
    """
    
    @client.on(events.NewMessage(pattern=r"^[!?/]save(?:\s+(.+))?$"))
    async def save_note_command(event):
        """Handler for the save note command."""
        # Check if the event is in a private chat (we only allow notes in groups)
        if event.is_private:
            await event.respond("Notes can only be saved in groups.")
            return
        
        # Check if the user has permission to save notes
        chat = await event.get_chat()
        sender = await event.get_sender()
        if not await _check_admin_rights(event, client):
            await event.respond("You need to be an admin to save notes.")
            return
        
        # Get command arguments
        args = event.pattern_match.group(1)
        if not args:
            await event.respond("Please provide a note name and content.\nUsage: `/save note_name note content`")
            return
        
        # Split into note name and content
        parts = args.split(maxsplit=1)
        if len(parts) < 2:
            # Check if it's a reply
            if event.reply_to_msg_id:
                note_name = parts[0].lower()
                replied_msg = await event.get_reply_message()
                note_content = replied_msg.text or replied_msg.caption or ""
                
                # Check for media
                media = None
                if replied_msg.media:
                    media = {
                        "type": _get_media_type(replied_msg),
                        "file_id": _get_file_id(replied_msg)
                    }
            else:
                await event.respond("Please provide note content or reply to a message.\nUsage: `/save note_name note content`")
                return
        else:
            note_name = parts[0].lower()
            note_content = parts[1]
            media = None
        
        # Save the note
        note_data = {
            "name": note_name,
            "content": note_content,
            "media": media,
            "created_by": sender.id,
            "created_at": datetime.now()
        }
        
        await database.save_note(chat.id, note_name, note_data)
        
        await event.respond(f"Note `{note_name}` saved successfully.")
        logger.info(f"Note '{note_name}' saved in chat {chat.id} by user {sender.id}")

    @client.on(events.NewMessage(pattern=r"^[!?/]get(?:\s+(.+))?$"))
    async def get_note_command(event):
        """Handler for the get note command."""
        # Check if the event is in a private chat (notes are per-group)
        if event.is_private:
            await event.respond("Notes can only be retrieved in groups.")
            return
        
        # Get command arguments
        args = event.pattern_match.group(1)
        if not args:
            await event.respond("Please provide a note name.\nUsage: `/get note_name`")
            return
        
        # Get the note name
        note_name = args.lower()
        
        # Retrieve the note
        chat = await event.get_chat()
        note = await database.get_note(chat.id, note_name)
        
        if not note:
            await event.respond(f"Note `{note_name}` not found.")
            return
        
        # Send the note content
        await _send_note(event, client, note)
        logger.info(f"Note '{note_name}' retrieved in chat {chat.id} by user {event.sender_id}")

    @client.on(events.NewMessage(pattern=r"^[!?/]notes$"))
    async def list_notes_command(event):
        """Handler for the list notes command."""
        # Check if the event is in a private chat (notes are per-group)
        if event.is_private:
            await event.respond("Notes can only be listed in groups.")
            return
        
        # Retrieve all notes for the chat
        chat = await event.get_chat()
        notes = await database.get_all_notes(chat.id)
        
        if not notes:
            await event.respond("No notes saved in this chat.")
            return
        
        # Build the response message
        response = "**Notes in this chat:**\n\n"
        for i, note in enumerate(notes, 1):
            note_name = note.get("note_name", "unknown")
            response += f"{i}. `{note_name}` - Get with `/get {note_name}` or `#{note_name}`\n"
        
        await event.respond(response)
        logger.info(f"Notes listed in chat {chat.id} by user {event.sender_id}")

    @client.on(events.NewMessage(pattern=r"^[!?/]clear(?:\s+(.+))?$"))
    async def clear_note_command(event):
        """Handler for the clear note command."""
        # Check if the event is in a private chat (we only allow notes in groups)
        if event.is_private:
            await event.respond("Notes can only be cleared in groups.")
            return
        
        # Check if the user has permission to clear notes
        if not await _check_admin_rights(event, client):
            await event.respond("You need to be an admin to clear notes.")
            return
        
        # Get command arguments
        args = event.pattern_match.group(1)
        if not args:
            await event.respond("Please provide a note name.\nUsage: `/clear note_name`")
            return
        
        # Get the note name
        note_name = args.lower()
        
        # Delete the note
        chat = await event.get_chat()
        success = await database.delete_note(chat.id, note_name)
        
        if success:
            await event.respond(f"Note `{note_name}` has been deleted.")
            logger.info(f"Note '{note_name}' cleared in chat {chat.id} by user {event.sender_id}")
        else:
            await event.respond(f"Note `{note_name}` not found.")

    @client.on(events.NewMessage(pattern=r"^#(\w+)$"))
    async def hashtag_note_command(event):
        """Handler for hashtag note retrieval."""
        # Check if the event is in a private chat (notes are per-group)
        if event.is_private:
            return
        
        # Get the note name from the hashtag
        note_name = event.pattern_match.group(1).lower()
        
        # Retrieve the note
        chat = await event.get_chat()
        note = await database.get_note(chat.id, note_name)
        
        if note:
            # Send the note content
            await _send_note(event, client, note)
            logger.info(f"Note '{note_name}' retrieved via hashtag in chat {chat.id} by user {event.sender_id}")
    
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

    async def _send_note(event, client, note):
        """Send a note's content with any associated media."""
        content = note.get("content", "")
        media = note.get("media")
        
        try:
            if media:
                # Handle media notes
                media_type = media.get("type")
                file_id = media.get("file_id")
                
                if file_id:
                    # We would need to handle file_id retrieval based on your storage method
                    # This is a simplified example
                    await event.respond(content, file=file_id)
                else:
                    await event.respond(content)
            else:
                # Text-only note
                await event.respond(content)
        except Exception as e:
            logger.error(f"Error sending note: {e}")
            await event.respond(f"Error sending note: {str(e)}")

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