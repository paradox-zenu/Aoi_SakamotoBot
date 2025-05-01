#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import motor.motor_asyncio
from loguru import logger
from typing import Optional, Dict, List, Any
from datetime import datetime
from pymongo import ASCENDING, DESCENDING, IndexModel

class Database:
    """Class to handle database operations with MongoDB."""
    
    def __init__(self, uri: str):
        """Initialize the database connection.
        
        Args:
            uri: MongoDB connection URI
        """
        self.uri = uri
        self.client = None
        self.db = None
        self._rate_limits = {}
    
    async def connect(self):
        """Connect to the MongoDB database."""
        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(self.uri)
            self.db = self.client.get_database()
            
            # Initialize collections
            self._init_collections()
            
            # Create indexes
            await self._create_indexes()
            
            logger.info(f"Connected to MongoDB database: {self.db.name}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from the MongoDB database."""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
    
    def _init_collections(self):
        """Initialize collection references."""
        # Core collections
        self.chats = self.db.chats
        self.users = self.db.users
        self.blacklist = self.db.blacklist
        self.rate_limits = self.db.rate_limits
        
        # Feature-specific collections
        self.notes = self.db.notes
        self.filters = self.db.filters
        self.warnings = self.db.warnings
        self.gbans = self.db.gbans
        self.locks = self.db.locks
        self.admin_actions = self.db.admin_actions
    
    async def _create_indexes(self):
        """Create database indexes for optimized queries."""
        try:
            # User indexes
            await self.users.create_indexes([
                IndexModel([("user_id", ASCENDING)], unique=True),
                IndexModel([("username", ASCENDING)], sparse=True),
                IndexModel([("created_at", DESCENDING)])
            ])
            
            # Chat indexes
            await self.chats.create_indexes([
                IndexModel([("chat_id", ASCENDING)], unique=True),
                IndexModel([("chat_title", ASCENDING)]),
                IndexModel([("created_at", DESCENDING)])
            ])
            
            # Notes indexes
            await self.notes.create_indexes([
                IndexModel([("chat_id", ASCENDING), ("note_name", ASCENDING)], unique=True),
                IndexModel([("created_at", DESCENDING)])
            ])
            
            # Filters indexes
            await self.filters.create_indexes([
                IndexModel([("chat_id", ASCENDING), ("keyword", ASCENDING)], unique=True),
                IndexModel([("created_at", DESCENDING)])
            ])
            
            # GBan indexes
            await self.gbans.create_indexes([
                IndexModel([("user_id", ASCENDING)], unique=True),
                IndexModel([("banned_at", DESCENDING)])
            ])
            
            # Warnings indexes
            await self.warnings.create_indexes([
                IndexModel([("chat_id", ASCENDING), ("user_id", ASCENDING)]),
                IndexModel([("timestamp", DESCENDING)])
            ])
            
            # Rate limits indexes
            await self.rate_limits.create_indexes([
                IndexModel([("key", ASCENDING)], unique=True),
                IndexModel([("expires_at", DESCENDING)], expireAfterSeconds=0)
            ])
            
            # Admin actions indexes
            await self.admin_actions.create_indexes([
                IndexModel([("chat_id", ASCENDING), ("admin_id", ASCENDING)]),
                IndexModel([("timestamp", DESCENDING)])
            ])
            
            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            raise
    
    # Rate limiting methods
    async def check_rate_limit(self, key: str, limit: int, window: int) -> bool:
        """Check if an action is rate limited.
        
        Args:
            key: Unique identifier for the rate limit (e.g., "user_123_command")
            limit: Maximum number of actions allowed in the time window
            window: Time window in seconds
            
        Returns:
            bool: True if action is allowed, False if rate limited
        """
        try:
            now = datetime.utcnow()
            expires_at = now + timedelta(seconds=window)
            
            # Get current count
            doc = await self.rate_limits.find_one({"key": key})
            
            if not doc:
                # First action in window
                await self.rate_limits.insert_one({
                    "key": key,
                    "count": 1,
                    "expires_at": expires_at
                })
                return True
            
            if doc["count"] >= limit:
                return False
            
            # Increment count
            await self.rate_limits.update_one(
                {"key": key},
                {
                    "$inc": {"count": 1},
                    "$set": {"expires_at": expires_at}
                }
            )
            return True
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return True  # Allow action on error
    
    # User methods
    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user data from database."""
        return await self.users.find_one({"user_id": user_id})
    
    async def save_user(self, user_data: Dict) -> None:
        """Save or update user data in database."""
        user_id = user_data.get("user_id")
        if not user_id:
            logger.error("Cannot save user without user_id")
            return
        
        await self.users.update_one(
            {"user_id": user_id},
            {"$set": user_data},
            upsert=True
        )
    
    async def get_users_by_username(self, username: str) -> List[Dict]:
        """Get users by username (case insensitive)."""
        cursor = self.users.find({"username": {"$regex": f"^{username}$", "$options": "i"}})
        return await cursor.to_list(length=None)
    
    # Chat methods
    async def get_chat(self, chat_id: int) -> Optional[Dict]:
        """Get chat data from database."""
        return await self.chats.find_one({"chat_id": chat_id})
    
    async def save_chat(self, chat_data: Dict) -> None:
        """Save or update chat data in database."""
        chat_id = chat_data.get("chat_id")
        if not chat_id:
            logger.error("Cannot save chat without chat_id")
            return
        
        await self.chats.update_one(
            {"chat_id": chat_id},
            {"$set": chat_data},
            upsert=True
        )
    
    async def get_all_chats(self) -> List[Dict]:
        """Get all chats."""
        return await self.chats.find().to_list(length=None)
    
    # GBan methods
    async def get_gban(self, user_id: int) -> Optional[Dict]:
        """Get gban data for a user."""
        return await self.gbans.find_one({"user_id": user_id})
    
    async def add_gban(self, user_id: int, reason: str, banned_by: int) -> None:
        """Add a user to the global ban list."""
        gban_data = {
            "user_id": user_id,
            "reason": reason,
            "banned_by": banned_by,
            "banned_at": datetime.utcnow(),
        }
        await self.gbans.update_one(
            {"user_id": user_id},
            {"$set": gban_data},
            upsert=True
        )
    
    async def remove_gban(self, user_id: int) -> bool:
        """Remove a user from the global ban list.
        
        Returns:
            True if a user was removed, False if user wasn't gbanned
        """
        result = await self.gbans.delete_one({"user_id": user_id})
        return result.deleted_count > 0
    
    async def get_gban_list(self) -> List[Dict]:
        """Get all gbanned users."""
        return await self.gbans.find().sort("banned_at", DESCENDING).to_list(length=None)
    
    # Notes methods
    async def get_note(self, chat_id: int, note_name: str) -> Optional[Dict]:
        """Get a note from a specific chat."""
        return await self.notes.find_one({
            "chat_id": chat_id,
            "note_name": note_name.lower()
        })
    
    async def save_note(self, chat_id: int, note_name: str, note_data: Dict) -> None:
        """Save a note to a specific chat."""
        note_data.update({
            "chat_id": chat_id,
            "note_name": note_name.lower(),
            "updated_at": datetime.utcnow()
        })
        await self.notes.update_one(
            {"chat_id": chat_id, "note_name": note_name.lower()},
            {"$set": note_data},
            upsert=True
        )
    
    async def delete_note(self, chat_id: int, note_name: str) -> bool:
        """Delete a note from a specific chat.
        
        Returns:
            True if note was deleted, False if note didn't exist
        """
        result = await self.notes.delete_one({
            "chat_id": chat_id,
            "note_name": note_name.lower()
        })
        return result.deleted_count > 0
    
    async def get_all_notes(self, chat_id: int) -> List[Dict]:
        """Get all notes for a specific chat."""
        return await self.notes.find({"chat_id": chat_id}).sort("note_name", ASCENDING).to_list(length=None)

    # Filters methods
    async def get_filter(self, chat_id: int, keyword: str) -> Optional[Dict]:
        """Get a filter from a specific chat."""
        return await self.filters.find_one({
            "chat_id": chat_id,
            "keyword": keyword.lower()
        })
    
    async def save_filter(self, chat_id: int, keyword: str, filter_data: Dict) -> None:
        """Save a filter to a specific chat."""
        filter_data.update({
            "chat_id": chat_id,
            "keyword": keyword.lower(),
            "updated_at": datetime.utcnow()
        })
        await self.filters.update_one(
            {"chat_id": chat_id, "keyword": keyword.lower()},
            {"$set": filter_data},
            upsert=True
        )
    
    async def delete_filter(self, chat_id: int, keyword: str) -> bool:
        """Delete a filter from a specific chat."""
        result = await self.filters.delete_one({
            "chat_id": chat_id,
            "keyword": keyword.lower()
        })
        return result.deleted_count > 0
    
    async def get_all_filters(self, chat_id: int) -> List[Dict]:
        """Get all filters for a specific chat."""
        return await self.filters.find({"chat_id": chat_id}).sort("keyword", ASCENDING).to_list(length=None)
    
    # Warning methods
    async def get_warnings(self, chat_id: int, user_id: int) -> List[Dict]:
        """Get all warnings for a user in a specific chat."""
        cursor = self.warnings.find({"chat_id": chat_id, "user_id": user_id}).sort("timestamp", ASCENDING)
        return await cursor.to_list(length=None)
    
    async def add_warning(self, chat_id: int, user_id: int, reason: str, warned_by: int) -> int:
        """Add a warning for a user in a specific chat.
        
        Returns:
            Current warning count for the user
        """
        warning_data = {
            "chat_id": chat_id,
            "user_id": user_id,
            "reason": reason,
            "warned_by": warned_by,
            "timestamp": datetime.utcnow()
        }
        await self.warnings.insert_one(warning_data)
        
        # Return the current warning count
        warnings = await self.get_warnings(chat_id, user_id)
        return len(warnings)
    
    async def reset_warnings(self, chat_id: int, user_id: int) -> int:
        """Reset all warnings for a user in a specific chat.
        
        Returns:
            Number of warnings that were reset
        """
        result = await self.warnings.delete_many({
            "chat_id": chat_id,
            "user_id": user_id
        })
        return result.deleted_count
    
    # Admin action logging
    async def log_admin_action(self, chat_id: int, admin_id: int, target_id: int, action: str, reason: Optional[str] = None) -> None:
        """Log an admin action.
        
        Args:
            chat_id: ID of the chat where action was taken
            admin_id: ID of the admin who took the action
            target_id: ID of the user targeted by the action
            action: Type of action taken (e.g., "ban", "kick", "mute")
            reason: Optional reason for the action
        """
        action_data = {
            "chat_id": chat_id,
            "admin_id": admin_id,
            "target_id": target_id,
            "action": action,
            "reason": reason,
            "timestamp": datetime.utcnow()
        }
        await self.admin_actions.insert_one(action_data)
    
    async def get_admin_actions(self, chat_id: int, limit: int = 50) -> List[Dict]:
        """Get recent admin actions in a chat.
        
        Args:
            chat_id: ID of the chat
            limit: Maximum number of actions to return
            
        Returns:
            List of admin actions, sorted by most recent first
        """
        cursor = self.admin_actions.find({"chat_id": chat_id}).sort("timestamp", DESCENDING).limit(limit)
        return await cursor.to_list(length=None)