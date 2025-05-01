#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telethon import functions
from loguru import logger
from typing import Optional, Union

async def check_admin_rights(event, client, permission=None):
    """Check if the user has the specified admin rights.
    
    Args:
        event: Telethon event
        client: Telethon client
        permission: Specific permission to check (e.g., "ban_users", "pin_messages")
        
    Returns:
        bool: True if the user has the required permissions, False otherwise
    """
    # Get the sender
    sender = await event.get_sender()
    
    # Get the chat
    chat = await event.get_chat()
    
    # Always allow in private chats
    if event.is_private:
        return True
    
    # Always allow the owner
    if sender.id == client.config.owner_id:
        return True
    
    # Check if the user is in the sudo or support list
    if client.config.is_sudo(sender.id) or client.config.is_support(sender.id):
        return True
    
    try:
        # Get the sender's permissions in the chat
        sender_perms = await client.get_permissions(chat, sender)
        
        # Check if the user is an admin
        if not sender_perms.is_admin:
            await event.respond("You need to be an admin to use this command.")
            return False
        
        # If no specific permission is required, being an admin is enough
        if not permission:
            return True
        
        # Check for specific permission
        if permission == "pin_messages" and not sender_perms.pin_messages:
            await event.respond("You need to have the 'Pin Messages' permission to use this command.")
            return False
            
        if permission == "ban_users" and not sender_perms.ban_users:
            await event.respond("You need to have the 'Ban Users' permission to use this command.")
            return False
            
        if permission == "add_admins" and not sender_perms.add_admins:
            await event.respond("You need to have the 'Add Admins' permission to use this command.")
            return False
            
        if permission == "change_info" and not sender_perms.change_info:
            await event.respond("You need to have the 'Change Info' permission to use this command.")
            return False
            
        if permission == "delete_messages" and not sender_perms.delete_messages:
            await event.respond("You need to have the 'Delete Messages' permission to use this command.")
            return False
            
        if permission == "invite_users" and not sender_perms.invite_users:
            await event.respond("You need to have the 'Invite Users' permission to use this command.")
            return False
            
        return True
    except Exception as e:
        logger.error(f"Error checking admin rights: {e}")
        await event.respond("An error occurred while checking permissions.")
        return False

async def has_admin_rights(client, chat_id, user_id, permission=None):
    """Check if a user has admin rights in a chat.
    
    Args:
        client: Telethon client
        chat_id: ID of the chat
        user_id: ID of the user
        permission: Specific permission to check
        
    Returns:
        bool: True if the user has the required permissions, False otherwise
    """
    # Always allow the owner
    if user_id == client.config.owner_id:
        return True
    
    # Check if the user is in the sudo or support list
    if client.config.is_sudo(user_id) or client.config.is_support(user_id):
        return True
    
    try:
        # Get the user's permissions in the chat
        user_perms = await client.get_permissions(chat_id, user_id)
        
        # Check if the user is an admin
        if not user_perms.is_admin:
            return False
        
        # If no specific permission is required, being an admin is enough
        if not permission:
            return True
        
        # Check for specific permission
        if permission == "pin_messages" and not user_perms.pin_messages:
            return False
            
        if permission == "ban_users" and not user_perms.ban_users:
            return False
            
        if permission == "add_admins" and not user_perms.add_admins:
            return False
            
        if permission == "change_info" and not user_perms.change_info:
            return False
            
        if permission == "delete_messages" and not user_perms.delete_messages:
            return False
            
        if permission == "invite_users" and not user_perms.invite_users:
            return False
            
        return True
    except Exception as e:
        logger.error(f"Error checking admin rights: {e}")
        return False

async def check_user_permission(event, client, min_level="user"):
    """Check if a user has the minimum required permission level.
    
    Args:
        event: Telethon event
        client: Telethon client
        min_level: Minimum required permission level
                  ("owner", "sudo", "support", "whitelisted", "user")
                  
    Returns:
        bool: True if the user has the required permission level, False otherwise
    """
    # Get the sender
    sender = await event.get_sender()
    user_id = sender.id
    
    # Check permission level
    if min_level == "owner" and not client.config.is_owner(user_id):
        await event.respond("This command can only be used by the bot owner.")
        return False
        
    if min_level == "sudo" and not client.config.is_sudo(user_id):
        await event.respond("This command can only be used by sudo users.")
        return False
        
    if min_level == "support" and not client.config.is_support(user_id):
        await event.respond("This command can only be used by support users.")
        return False
        
    if min_level == "whitelisted" and not client.config.is_whitelisted(user_id):
        await event.respond("This command can only be used by whitelisted users.")
        return False
    
    return True