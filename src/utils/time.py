#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import timedelta
import re
from loguru import logger

def parse_time_arg(time_str):
    """Parse a time argument string into a timedelta object.
    
    Formats supported:
    - Xm = X minutes
    - Xh = X hours
    - Xd = X days
    
    Args:
        time_str: Time string to parse
        
    Returns:
        timedelta: The parsed time duration
    """
    if not time_str:
        return None
    
    # Try to parse the time string
    match = re.match(r"^(\d+)([mhd])$", time_str.lower())
    if not match:
        logger.warning(f"Invalid time format: {time_str}")
        return None
    
    amount, unit = match.groups()
    amount = int(amount)
    
    if unit == 'm':
        return timedelta(minutes=amount)
    elif unit == 'h':
        return timedelta(hours=amount)
    elif unit == 'd':
        return timedelta(days=amount)
    
    logger.warning(f"Invalid time unit: {unit}")
    return None

def format_timedelta(delta):
    """Convert a timedelta to a human-readable string.
    
    Args:
        delta: timedelta object
        
    Returns:
        str: Human-readable time string
    """
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
    
    if not parts:
        return "0 seconds"
    
    return ", ".join(parts)