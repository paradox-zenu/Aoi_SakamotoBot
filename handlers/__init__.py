from handlers.admin import register_admin_handlers
from handlers.bans import register_ban_handlers
from handlers.basic import register_basic_handlers
from handlers.welcome import register_welcome_handlers
from handlers.notes import register_notes_handlers
from handlers.filters import register_filters_handlers

__all__ = [
    "register_admin_handlers",
    "register_ban_handlers",
    "register_basic_handlers",
    "register_welcome_handlers",
    "register_notes_handlers",
    "register_filters_handlers"
]