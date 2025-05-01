#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .admin import register_admin_handlers
from .basic import register_basic_handlers
from .filters import register_filters_handlers
from .gban import register_gban_handlers
from .notes import register_notes_handlers
from .welcome import register_welcome_handlers
from .errors import register_error_handlers

def register_all_handlers(client, database, config):
    """Register all handlers for the bot.
    
    Args:
        client: Telethon client instance
        database: Database instance
        config: Config instance
    """
    # Register basic command handlers (start, help, etc.)
    register_basic_handlers(client, database, config)
    
    # Register admin command handlers (ban, kick, mute, etc.)
    register_admin_handlers(client, database, config)
    
    # Register gban/ungban handlers
    register_gban_handlers(client, database, config)
    
    # Register notes handlers
    register_notes_handlers(client, database, config)
    
    # Register filters handlers
    register_filters_handlers(client, database, config)
    
    # Register welcome message handlers
    register_welcome_handlers(client, database, config)
    
    # Register error handlers last
    register_error_handlers(client, database, config)

__all__ = ["register_all_handlers"]