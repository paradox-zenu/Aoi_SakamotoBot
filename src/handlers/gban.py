#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telethon import events, Button
from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChatBannedRights, ChannelParticipantsAdmins
from loguru import logger
from typing import List, Dict, Optional
from datetime import datetime
from ..utils.permissions import check_user_permission

# Ban rights for gbanned users
GBAN_RIGHTS = ChatBannedRights(
    until_date=None,
    view_messages=True,
    send_messages=True,
    send_media=True,
    send_stickers=True,
    send_gifs=True,
    send_games=True,
    send_inline=True,
    embed_links=True
)

def register_gban_handlers(client, database, config):
    """Register global ban command handlers.
    
    Args:
        client: Telethon client instance
        database: Database instance
        config: Config instance
    """
    
    @client.on(events.NewMessage(pattern=r"^[!?/]gban(?:\s+(.+))?$"))
    async def gban_command(event):
        """Handler for the gban command."""
        # Check if the user has permission to use the gban command
        sender_id = event.sender_id
        if not config.is_sudo(sender_id):
            await event.respond("You don't have permission to use this command. This incident will be reported.")
            logger.warning(f"Unauthorized gban attempt by user {sender_id}")
            return
        
        # Get target user and reason
        args = event.pattern_match.group(1)
        if not args and not event.reply_to_msg_id:
            await event.respond("Please specify a user to globally ban or reply to their message.")
            return
        
        target_user, reason = await _parse_gban_args(event, args, client)
        if not target_user:
            await event.respond("Could not find the specified user.")
            return
        
        # Check if we can gban this user
        if not await _can_gban(target_user.id, config):
            await event.respond(f"Cannot globally ban user {target_user.first_name}. They might be an owner or have special privileges.")
            return
        
        # Check if user is already gbanned
        existing_gban = await database.get_gban(target_user.id)
        if existing_gban:
            # User is already gbanned, update the reason if provided
            if reason:
                await database.add_gban(target_user.id, reason, sender_id)
                await event.respond(f"User {target_user.first_name} is already globally banned. Updated reason: {reason}")
            else:
                old_reason = existing_gban.get("reason", "No reason provided")
                await event.respond(f"User {target_user.first_name} is already globally banned. Reason: {old_reason}")
            return
        
        # Add user to gban list
        await database.add_gban(target_user.id, reason or "No reason provided", sender_id)
        
        # Send confirmation
        if reason:
            await event.respond(f"User {target_user.first_name} has been globally banned. Reason: {reason}")
        else:
            await event.respond(f"User {target_user.first_name} has been globally banned.")
        
        logger.info(f"User {target_user.id} has been globally banned by {sender_id}")
        
        # Announce to support chat if configured
        if config.backup_chat_id:
            gban_message = (
                f"#GBAN\n"
                f"User: {target_user.first_name} ({target_user.id})\n"
                f"By: {event.sender_id}\n"
                f"Reason: {reason or 'No reason provided'}"
            )
            try:
                await client.send_message(config.backup_chat_id, gban_message)
            except Exception as e:
                logger.error(f"Failed to send gban announcement: {e}")

    @client.on(events.NewMessage(pattern=r"^[!?/]ungban(?:\s+(.+))?$"))
    async def ungban_command(event):
        """Handler for the ungban command."""
        # Check if the user has permission to use the ungban command
        sender_id = event.sender_id
        if not config.is_sudo(sender_id):
            await event.respond("You don't have permission to use this command. This incident will be reported.")
            logger.warning(f"Unauthorized ungban attempt by user {sender_id}")
            return
        
        # Get target user
        args = event.pattern_match.group(1)
        if not args and not event.reply_to_msg_id:
            await event.respond("Please specify a user to globally unban or reply to their message.")
            return
        
        target_user, _ = await _parse_gban_args(event, args, client)
        if not target_user:
            # Try to handle user ID directly
            if args and args.isdigit():
                target_id = int(args)
                if await database.get_gban(target_id):
                    # User is gbanned, proceed with ungban
                    await database.remove_gban(target_id)
                    await event.respond(f"User {target_id} has been globally unbanned.")
                    logger.info(f"User {target_id} has been globally unbanned by {sender_id}")
                    
                    # Announce to support chat if configured
                    if config.backup_chat_id:
                        ungban_message = (
                            f"#UNGBAN\n"
                            f"User: {target_id}\n"
                            f"By: {event.sender_id}"
                        )
                        try:
                            await client.send_message(config.backup_chat_id, ungban_message)
                        except Exception as e:
                            logger.error(f"Failed to send ungban announcement: {e}")
                    return
            
            await event.respond("Could not find the specified user.")
            return
        
        # Check if user is gbanned
        if not await database.get_gban(target_user.id):
            await event.respond(f"User {target_user.first_name} is not globally banned.")
            return
        
        # Remove user from gban list
        await database.remove_gban(target_user.id)
        
        # Send confirmation
        await event.respond(f"User {target_user.first_name} has been globally unbanned.")
        logger.info(f"User {target_user.id} has been globally unbanned by {sender_id}")
        
        # Announce to support chat if configured
        if config.backup_chat_id:
            ungban_message = (
                f"#UNGBAN\n"
                f"User: {target_user.first_name} ({target_user.id})\n"
                f"By: {event.sender_id}"
            )
            try:
                await client.send_message(config.backup_chat_id, ungban_message)
            except Exception as e:
                logger.error(f"Failed to send ungban announcement: {e}")

    @client.on(events.NewMessage(pattern=r"^[!?/]gbanlist$"))
    async def gbanlist_command(event):
        """Handler for the gbanlist command."""
        # Check if the user has permission to view the gban list
        sender_id = event.sender_id
        if not config.is_support(sender_id):
            await event.respond("You don't have permission to use this command.")
            return
        
        # Get all gbanned users
        gbans = await database.get_gban_list()
        
        if not gbans:
            await event.respond("There are no globally banned users.")
            return
        
        # Build the response
        response = "**Globally Banned Users:**\n\n"
        for i, gban in enumerate(gbans[:30], 1):  # Limit to 30 to avoid message too long
            user_id = gban.get("user_id")
            reason = gban.get("reason", "No reason provided")
            response += f"{i}. User ID: `{user_id}` - Reason: {reason}\n"
        
        if len(gbans) > 30:
            response += f"\nAnd {len(gbans) - 30} more..."
        
        await event.respond(response)
        logger.info(f"Gbanlist command executed by user {sender_id}")

    @client.on(events.ChatAction())
    async def check_gban_on_join(event):
        """Check if a user is gbanned when they join a chat."""
        # Only check when a user joins
        if event.user_joined or event.user_added:
            # Get the user who joined
            user_id = event.user_id
            
            # Check if user is gbanned
            gban_data = await database.get_gban(user_id)
            if not gban_data:
                return
            
            # User is gbanned, ban them from this chat
            chat = await event.get_chat()
            
            try:
                # Check if the bot has permission to ban
                bot_id = (await client.get_me()).id
                chat_participant = await client.get_participants(chat, filter=ChannelParticipantsAdmins)
                bot_is_admin = any(participant.id == bot_id and participant.admin_rights.ban_users for participant in chat_participant)
                
                if not bot_is_admin:
                    logger.warning(f"Cannot ban gbanned user {user_id} in chat {chat.id}, bot is not admin or missing permissions")
                    return
                
                # Ban the user
                reason = gban_data.get("reason", "No reason provided")
                await client(EditBannedRequest(
                    chat.id,
                    user_id,
                    GBAN_RIGHTS
                ))
                
                # Send notification
                await client.send_message(
                    chat.id,
                    f"⚠️ Gbanned user detected and banned.\n"
                    f"User ID: `{user_id}`\n"
                    f"Reason: {reason}"
                )
                
                logger.info(f"Gbanned user {user_id} banned from chat {chat.id}")
            except Exception as e:
                logger.error(f"Error banning gbanned user {user_id} in chat {chat.id}: {e}")

    @client.on(events.NewMessage())
    async def check_message_from_gbanned(event):
        """Check if a message is from a gbanned user."""
        # Ignore commands and private chats
        if event.is_private:
            return
        
        # Get the sender
        sender = await event.get_sender()
        
        # Check if user is gbanned
        gban_data = await database.get_gban(sender.id)
        if not gban_data:
            return
        
        # User is gbanned, ban them from this chat
        chat = await event.get_chat()
        
        try:
            # Check if the bot has permission to ban
            bot_id = (await client.get_me()).id
            chat_participant = await client.get_participants(chat, filter=ChannelParticipantsAdmins)
            bot_is_admin = any(participant.id == bot_id and participant.admin_rights.ban_users for participant in chat_participant)
            
            if not bot_is_admin:
                logger.warning(f"Cannot ban gbanned user {sender.id} in chat {chat.id}, bot is not admin or missing permissions")
                return
            
            # Delete the message
            await event.delete()
            
            # Ban the user
            reason = gban_data.get("reason", "No reason provided")
            await client(EditBannedRequest(
                chat.id,
                sender.id,
                GBAN_RIGHTS
            ))
            
            # Send notification
            await client.send_message(
                chat.id,
                f"⚠️ Gbanned user detected and banned.\n"
                f"User: {sender.first_name} ({sender.id})\n"
                f"Reason: {reason}"
            )
            
            logger.info(f"Gbanned user {sender.id} banned from chat {chat.id}")
        except Exception as e:
            logger.error(f"Error banning gbanned user {sender.id} in chat {chat.id}: {e}")
    
    # Helper functions
    async def _parse_gban_args(event, args, client):
        """Parse arguments for gban/ungban commands.
        
        Returns:
            Tuple of (user, reason)
        """
        # Check if command is a reply
        if event.reply_to_msg_id:
            # Get the replied message
            replied_msg = await event.get_reply_message()
            target_user = await replied_msg.get_sender()
            reason = args
            return target_user, reason
        
        # No reply, parse args
        if not args:
            return None, None
        
        # Split args into user and reason
        parts = args.split(maxsplit=1)
        user_input = parts[0]
        reason = parts[1] if len(parts) > 1 else None
        
        # Try to get the user
        try:
            if user_input.isdigit():
                target_user = await client.get_entity(int(user_input))
            elif user_input.startswith("@"):
                target_user = await client.get_entity(user_input)
            else:
                # If not a username or ID, consider it part of the reason
                return None, None
            
            return target_user, reason
        except Exception as e:
            logger.error(f"Error getting user entity: {e}")
            return None, None
    
    async def _can_gban(user_id, config):
        """Check if a user can be gbanned."""
        # Can't gban owner
        if user_id == config.owner_id:
            return False
        
        # Can't gban sudo users
        if config.is_sudo(user_id):
            return False
        
        return True