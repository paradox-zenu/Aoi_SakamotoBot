import time
import re
from datetime import datetime
from telegram import User, Chat, Update
from telegram.ext import CallbackContext
from typing import Tuple, Optional, Union

def extract_time(time_text: str) -> Optional[int]:
    """Extract time from user input like '1h', '30m', etc."""
    time_units = {
        's': 1,
        'm': 60,
        'h': 60 * 60,
        'd': 24 * 60 * 60,
        'w': 7 * 24 * 60 * 60
    }
    
    time_regex = re.compile(r'(\d+)([smhdw])')
    match = time_regex.match(time_text.lower())
    
    if match:
        time_val, unit = match.groups()
        return int(time_val) * time_units[unit] + int(time.time())
    
    return None

def extract_user_and_reason(update: Update, context: CallbackContext) -> Tuple[Optional[int], Optional[str]]:
    """Extract user ID and reason from command."""
    message = update.effective_message
    user_id = None
    reason = None
    
    # If replying to a message and no args provided, target the replied user
    if message.reply_to_message and not context.args:
        user_id = message.reply_to_message.from_user.id
        reason = None
    elif context.args:
        # Try to extract a user ID or username from the first argument
        user_mention = context.args[0]
        
        # If user mention is an ID
        if user_mention.isdigit():
            user_id = int(user_mention)
        # If user mention is a username
        elif user_mention.startswith('@'):
            try:
                user = context.bot.get_chat(user_mention)
                user_id = user.id
            except:
                return None, None
        # If user mention is a mention
        elif message.entities and message.entities[0].type == "text_mention":
            user_id = message.entities[0].user.id
        
        # Extract reason, if any
        if len(context.args) > 1:
            reason = ' '.join(context.args[1:])
    
    return user_id, reason

def get_readable_time(seconds: int) -> str:
    """Convert seconds to a human-readable time format."""
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]
    
    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)
    
    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    
    if len(time_list) == 4:
        ping_time += f"{time_list.pop()}, "
    
    time_list.reverse()
    ping_time += ":".join(time_list)
    
    return ping_time or "0s"

def format_welcome_message(message: str, user: User, chat: Chat) -> str:
    """Format welcome message with user and chat info."""
    # Build a dict of all available placeholders
    format_dict = {
        "user_mention": user.mention_html(),
        "user_firstname": user.first_name,
        "user_lastname": user.last_name or "",
        "user_username": f"@{user.username}" if user.username else "",
        "user_id": user.id,
        "chat_title": chat.title,
        "chat_id": chat.id,
        "members_count": chat.get_member_count()
    }
    
    # Replace placeholders with actual values
    for placeholder, value in format_dict.items():
        message = message.replace(f"{{{placeholder}}}", str(value))
    
    return message