#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telethon import events, Button
from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChatBannedRights, ChannelParticipantsAdmins
from loguru import logger
from typing import List, Union
from datetime import datetime, timedelta
from ..utils.permissions import check_admin_rights, has_admin_rights
from ..utils.time import parse_time_arg

# Ban rights for various admin actions
MUTE_RIGHTS = ChatBannedRights(
    until_date=None,
    send_messages=True,
    send_media=True,
    send_stickers=True,
    send_gifs=True,
    send_games=True,
    send_inline=True,
    embed_links=True
)

BAN_RIGHTS = ChatBannedRights(
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

KICK_RIGHTS = ChatBannedRights(
    until_date=None,
    view_messages=True
)

UNBAN_RIGHTS = ChatBannedRights(
    until_date=None,
    view_messages=False,
    send_messages=False,
    send_media=False,
    send_stickers=False,
    send_gifs=False,
    send_games=False,
    send_inline=False,
    embed_links=False
)

def register_admin_handlers(client, database, config):
    """Register admin command handlers.
    
    Args:
        client: Telethon client instance
        database: Database instance
        config: Config instance
    """
    
    @client.on(events.NewMessage(pattern=r"^[!?/]ban(?:\s+(.+))?$"))
    async def ban_command(event):
        """Handler for the ban command."""
        # Check if the user has permission to ban
        if not await check_admin_rights(event, client, "ban_users"):
            return
        
        # Get the target user
        target_user, reason = await _get_target_and_reason(event)
        if not target_user:
            await event.respond("Please specify a user to ban.")
            return
        
        # Check if the target user can be banned
        if not await _can_take_action(event, client, target_user.id):
            await event.respond("I can't ban this user. They might be an admin or I don't have the required permissions.")
            return
        
        # Ban the user
        try:
            chat = await event.get_chat()
            await client(EditBannedRequest(
                chat.id,
                target_user.id,
                BAN_RIGHTS
            ))
            
            # Build the ban message
            if reason:
                ban_message = f"User {target_user.first_name} has been banned. Reason: {reason}"
            else:
                ban_message = f"User {target_user.first_name} has been banned."
            
            await event.respond(ban_message)
            logger.info(f"User {target_user.id} banned from {chat.id} by {event.sender_id}")
            
            # Save the ban action to the database
            await _log_admin_action(database, chat.id, event.sender_id, target_user.id, "ban", reason)
        except Exception as e:
            logger.error(f"Error banning user: {e}")
            await event.respond(f"An error occurred while banning the user: {str(e)}")

    @client.on(events.NewMessage(pattern=r"^[!?/]unban(?:\s+(.+))?$"))
    async def unban_command(event):
        """Handler for the unban command."""
        # Check if the user has permission to unban
        if not await check_admin_rights(event, client, "ban_users"):
            return
        
        # Get the target user
        target_user, reason = await _get_target_and_reason(event)
        if not target_user:
            await event.respond("Please specify a user to unban.")
            return
        
        # Unban the user
        try:
            chat = await event.get_chat()
            await client(EditBannedRequest(
                chat.id,
                target_user.id,
                UNBAN_RIGHTS
            ))
            
            await event.respond(f"User {target_user.first_name} has been unbanned.")
            logger.info(f"User {target_user.id} unbanned from {chat.id} by {event.sender_id}")
            
            # Save the unban action to the database
            await _log_admin_action(database, chat.id, event.sender_id, target_user.id, "unban", reason)
        except Exception as e:
            logger.error(f"Error unbanning user: {e}")
            await event.respond(f"An error occurred while unbanning the user: {str(e)}")

    @client.on(events.NewMessage(pattern=r"^[!?/]kick(?:\s+(.+))?$"))
    async def kick_command(event):
        """Handler for the kick command."""
        # Check if the user has permission to kick
        if not await check_admin_rights(event, client, "ban_users"):
            return
        
        # Get the target user
        target_user, reason = await _get_target_and_reason(event)
        if not target_user:
            await event.respond("Please specify a user to kick.")
            return
        
        # Check if the target user can be kicked
        if not await _can_take_action(event, client, target_user.id):
            await event.respond("I can't kick this user. They might be an admin or I don't have the required permissions.")
            return
        
        # Kick the user (ban and unban)
        try:
            chat = await event.get_chat()
            await client(EditBannedRequest(
                chat.id,
                target_user.id,
                KICK_RIGHTS
            ))
            
            # Build the kick message
            if reason:
                kick_message = f"User {target_user.first_name} has been kicked. Reason: {reason}"
            else:
                kick_message = f"User {target_user.first_name} has been kicked."
            
            await event.respond(kick_message)
            logger.info(f"User {target_user.id} kicked from {chat.id} by {event.sender_id}")
            
            # Save the kick action to the database
            await _log_admin_action(database, chat.id, event.sender_id, target_user.id, "kick", reason)
        except Exception as e:
            logger.error(f"Error kicking user: {e}")
            await event.respond(f"An error occurred while kicking the user: {str(e)}")

    @client.on(events.NewMessage(pattern=r"^[!?/]mute(?:\s+(.+))?$"))
    async def mute_command(event):
        """Handler for the mute command."""
        # Check if the user has permission to mute
        if not await check_admin_rights(event, client, "ban_users"):
            return
        
        # Get the command arguments
        args = event.pattern_match.group(1)
        if not args:
            await event.respond("Please specify a user to mute.")
            return
        
        # Parse the arguments to get the target user and optional time and reason
        parts = args.split()
        target_input = parts[0]
        
        # Check if the second part is a time specification
        time_delta = None
        if len(parts) > 1 and parts[1][0].isdigit():
            time_spec = parts[1]
            time_delta = parse_time_arg(time_spec)
            reason = " ".join(parts[2:]) if len(parts) > 2 else None
        else:
            reason = " ".join(parts[1:]) if len(parts) > 1 else None
        
        # Get the target user
        try:
            if target_input.isdigit():
                target_user = await client.get_entity(int(target_input))
            elif target_input.startswith("@"):
                target_user = await client.get_entity(target_input)
            else:
                # Try to get the user from the reply
                if event.reply_to_msg_id:
                    replied_msg = await event.get_reply_message()
                    target_user = await replied_msg.get_sender()
                else:
                    await event.respond("Invalid user specified.")
                    return
        except Exception as e:
            logger.error(f"Error getting target user: {e}")
            await event.respond(f"Could not find the specified user.")
            return
        
        # Check if the target user can be muted
        if not await _can_take_action(event, client, target_user.id):
            await event.respond("I can't mute this user. They might be an admin or I don't have the required permissions.")
            return
        
        # Create the mute rights
        if time_delta:
            until_date = datetime.now() + time_delta
            mute_rights = ChatBannedRights(
                until_date=until_date,
                send_messages=True,
                send_media=True,
                send_stickers=True,
                send_gifs=True,
                send_games=True,
                send_inline=True,
                embed_links=True
            )
        else:
            mute_rights = MUTE_RIGHTS
        
        # Mute the user
        try:
            chat = await event.get_chat()
            await client(EditBannedRequest(
                chat.id,
                target_user.id,
                mute_rights
            ))
            
            # Build the mute message
            mute_message = f"User {target_user.first_name} has been muted."
            if time_delta:
                mute_message += f" Duration: {_format_time_delta(time_delta)}."
            if reason:
                mute_message += f" Reason: {reason}"
            
            await event.respond(mute_message)
            logger.info(f"User {target_user.id} muted in {chat.id} by {event.sender_id}")
            
            # Save the mute action to the database
            await _log_admin_action(database, chat.id, event.sender_id, target_user.id, "mute", reason)
        except Exception as e:
            logger.error(f"Error muting user: {e}")
            await event.respond(f"An error occurred while muting the user: {str(e)}")

    @client.on(events.NewMessage(pattern=r"^[!?/]unmute(?:\s+(.+))?$"))
    async def unmute_command(event):
        """Handler for the unmute command."""
        # Check if the user has permission to unmute
        if not await check_admin_rights(event, client, "ban_users"):
            return
        
        # Get the target user
        target_user, reason = await _get_target_and_reason(event)
        if not target_user:
            await event.respond("Please specify a user to unmute.")
            return
        
        # Unmute the user
        try:
            chat = await event.get_chat()
            await client(EditBannedRequest(
                chat.id,
                target_user.id,
                ChatBannedRights(
                    until_date=None,
                    send_messages=False,
                    send_media=False,
                    send_stickers=False,
                    send_gifs=False,
                    send_games=False,
                    send_inline=False,
                    embed_links=False
                )
            ))
            
            await event.respond(f"User {target_user.first_name} has been unmuted.")
            logger.info(f"User {target_user.id} unmuted in {chat.id} by {event.sender_id}")
            
            # Save the unmute action to the database
            await _log_admin_action(database, chat.id, event.sender_id, target_user.id, "unmute", reason)
        except Exception as e:
            logger.error(f"Error unmuting user: {e}")
            await event.respond(f"An error occurred while unmuting the user: {str(e)}")

    @client.on(events.NewMessage(pattern=r"^[!?/]pin$"))
    async def pin_command(event):
        """Handler for the pin command."""
        # Check if the user has permission to pin messages
        if not await check_admin_rights(event, client, "pin_messages"):
            return
        
        # Check if the command is a reply to a message
        if not event.reply_to_msg_id:
            await event.respond("Please reply to a message to pin it.")
            return
        
        # Pin the message
        try:
            await client.pin_message(
                event.chat_id, 
                event.reply_to_msg_id,
                notify=True  # You might want to make this configurable
            )
            
            await event.respond("Message pinned successfully!")
            logger.info(f"Message {event.reply_to_msg_id} pinned in {event.chat_id} by {event.sender_id}")
        except Exception as e:
            logger.error(f"Error pinning message: {e}")
            await event.respond(f"An error occurred while pinning the message: {str(e)}")

    @client.on(events.NewMessage(pattern=r"^[!?/]unpin$"))
    async def unpin_command(event):
        """Handler for the unpin command."""
        # Check if the user has permission to pin messages
        if not await check_admin_rights(event, client, "pin_messages"):
            return
        
        # Check if the command is a reply to a message
        if not event.reply_to_msg_id:
            await event.respond("Please reply to a message to unpin it.")
            return
        
        # Unpin the message
        try:
            await client.unpin_message(
                event.chat_id,
                event.reply_to_msg_id
            )
            
            await event.respond("Message unpinned successfully!")
            logger.info(f"Message {event.reply_to_msg_id} unpinned in {event.chat_id} by {event.sender_id}")
        except Exception as e:
            logger.error(f"Error unpinning message: {e}")
            await event.respond(f"An error occurred while unpinning the message: {str(e)}")

    @client.on(events.NewMessage(pattern=r"^[!?/]unpinall$"))
    async def unpinall_command(event):
        """Handler for the unpinall command."""
        # Check if the user has permission to pin messages
        if not await check_admin_rights(event, client, "pin_messages"):
            return
        
        # Ask for confirmation
        try:
            confirm_message = await event.respond(
                "Are you sure you want to unpin all messages in this chat? This action cannot be undone.",
                buttons=[
                    [Button.inline("Yes", data="unpinall_yes")],
                    [Button.inline("No", data="unpinall_no")]
                ]
            )
            
            # Store the conversation state
            client.unpinall_messages = {
                "chat_id": event.chat_id,
                "user_id": event.sender_id,
                "message_id": confirm_message.id
            }
        except Exception as e:
            logger.error(f"Error showing unpinall confirmation: {e}")
            await event.respond(f"An error occurred: {str(e)}")
    
    @client.on(events.CallbackQuery(data=lambda d: d in [b"unpinall_yes", b"unpinall_no"]))
    async def unpinall_callback(event):
        """Callback handler for the unpinall confirmation."""
        # Get the stored conversation state
        unpinall_data = getattr(client, "unpinall_messages", None)
        if not unpinall_data:
            await event.answer("This confirmation has expired.")
            return
        
        # Check if the user who clicked is the same as the one who initiated
        if event.sender_id != unpinall_data["user_id"]:
            await event.answer("You didn't initiate this command.")
            return
        
        # Check if this is the correct chat
        if event.chat_id != unpinall_data["chat_id"]:
            await event.answer("Invalid context.")
            return
        
        # Handle the callback data
        if event.data == b"unpinall_yes":
            try:
                # Unpin all messages
                await client.unpin_message(event.chat_id)
                
                # Update the message
                await client.edit_message(
                    unpinall_data["chat_id"],
                    unpinall_data["message_id"],
                    "All messages have been unpinned."
                )
                logger.info(f"All messages unpinned in {event.chat_id} by {event.sender_id}")
            except Exception as e:
                logger.error(f"Error unpinning all messages: {e}")
                await client.edit_message(
                    unpinall_data["chat_id"],
                    unpinall_data["message_id"],
                    f"An error occurred: {str(e)}"
                )
        else:
            # User canceled the action
            await client.edit_message(
                unpinall_data["chat_id"],
                unpinall_data["message_id"],
                "Action canceled."
            )
        
        # Clear the stored data
        delattr(client, "unpinall_messages")
        await event.answer()

    # Helper functions
    async def _get_target_and_reason(event):
        """Extract target user and reason from command arguments."""
        args = event.pattern_match.group(1)
        
        # If no arguments provided, check if the command is a reply to a message
        if not args:
            if event.reply_to_msg_id:
                replied_msg = await event.get_reply_message()
                target_user = await replied_msg.get_sender()
                return target_user, None
            else:
                return None, None
        
        # Parse the arguments
        parts = args.split(maxsplit=1)
        target_input = parts[0]
        reason = parts[1] if len(parts) > 1 else None
        
        # Get the target user
        try:
            if target_input.isdigit():
                target_user = await client.get_entity(int(target_input))
            elif target_input.startswith("@"):
                target_user = await client.get_entity(target_input)
            else:
                # If argument doesn't look like a username or ID, check if it's a reply
                if event.reply_to_msg_id:
                    replied_msg = await event.get_reply_message()
                    target_user = await replied_msg.get_sender()
                    # In this case, the entire args is the reason
                    reason = args
                else:
                    return None, None
        except Exception as e:
            logger.error(f"Error getting target user: {e}")
            return None, None
        
        return target_user, reason

    async def _can_take_action(event, client, target_id):
        """Check if the bot can take action against the target user."""
        # Can't take action against the bot itself
        if target_id == (await client.get_me()).id:
            return False
        
        # Can't take action against the chat creator or admins
        chat = await event.get_chat()
        
        try:
            # Get all admins in the chat
            admin_participants = await client.get_participants(
                chat,
                filter=ChannelParticipantsAdmins
            )
            admin_ids = [admin.id for admin in admin_participants]
            
            # Check if the target is an admin
            if target_id in admin_ids:
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error checking if user can be actioned: {e}")
            return False

    async def _log_admin_action(database, chat_id, admin_id, target_id, action, reason=None):
        """Log an admin action to the database."""
        try:
            action_data = {
                "chat_id": chat_id,
                "admin_id": admin_id,
                "target_id": target_id,
                "action": action,
                "reason": reason,
                "timestamp": datetime.now()
            }
            
            # If we had an admin_actions collection, we'd save it there
            # For now, just log it
            logger.info(f"Admin action: {action_data}")
        except Exception as e:
            logger.error(f"Error logging admin action: {e}")

    def _format_time_delta(delta):
        """Format a timedelta object to a human-readable string."""
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        parts = []
        if days:
            parts.append(f"{days} day{'s' if days != 1 else ''}")
        if hours:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes:
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        if seconds:
            parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
        
        return ", ".join(parts)