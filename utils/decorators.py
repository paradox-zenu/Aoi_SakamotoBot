import functools
from time import time
from typing import Callable, Any
from telegram import Update, ChatMember, ChatMemberOwner, ChatMemberAdministrator
from telegram.ext import CallbackContext
from config import OWNER_ID, SUDO_USERS
from loguru import logger

def send_typing(func: Callable) -> Callable:
    """Sends typing action while processing func command."""
    @functools.wraps(func)
    def command_func(update: Update, context: CallbackContext, *args, **kwargs) -> Any:
        if update.effective_message and update.effective_chat:
            context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        return func(update, context, *args, **kwargs)
    return command_func

def admin_only(func: Callable) -> Callable:
    """Restricts access to group admins and bot sudo users."""
    @functools.wraps(func)
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs) -> Any:
        user = update.effective_user
        chat = update.effective_chat
        message = update.effective_message
        
        # Always allow bot owner and sudo users
        if user.id == OWNER_ID or user.id in SUDO_USERS:
            return func(update, context, *args, **kwargs)
        
        if chat.type == "private":
            message.reply_text("This command can only be used in groups.")
            return None
        
        # Check if user is admin
        chat_member = chat.get_member(user.id)
        if isinstance(chat_member, (ChatMemberOwner, ChatMemberAdministrator)):
            return func(update, context, *args, **kwargs)
        
        message.reply_text("This command is restricted to admins only.")
        return None
    return wrapper

def sudo_only(func: Callable) -> Callable:
    """Restricts access to sudo users and bot owner."""
    @functools.wraps(func)
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs) -> Any:
        user = update.effective_user
        
        if user.id == OWNER_ID or user.id in SUDO_USERS:
            return func(update, context, *args, **kwargs)
        
        update.message.reply_text("This command is restricted to bot administrators only.")
        return None
    return wrapper

def owner_only(func: Callable) -> Callable:
    """Restricts access to the bot owner only."""
    @functools.wraps(func)
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs) -> Any:
        user = update.effective_user
        
        if user.id == OWNER_ID:
            return func(update, context, *args, **kwargs)
        
        update.message.reply_text("This command is restricted to the bot owner only.")
        return None
    return wrapper

def log_command(func: Callable) -> Callable:
    """Log command usage with execution time."""
    @functools.wraps(func)
    def command_func(update: Update, context: CallbackContext, *args, **kwargs) -> Any:
        user = update.effective_user
        chat = update.effective_chat
        command = update.effective_message.text.split()[0]
        
        start_time = time()
        result = func(update, context, *args, **kwargs)
        end_time = time()
        
        execution_time = round((end_time - start_time) * 1000, 2)
        
        logger.info(
            f"Command: {command} | "
            f"User: {user.id} | "
            f"Chat: {chat.id} | "
            f"Execution time: {execution_time}ms"
        )
        
        return result
    return command_func