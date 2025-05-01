import pymongo
from pymongo import MongoClient
from loguru import logger
from config import MONGO_URI, DB_NAME

class Database:
    def __init__(self):
        self.client = None
        self.db = None
        self._initialize_db()
        
    def _initialize_db(self):
        """Initialize database connection"""
        try:
            if not MONGO_URI:
                logger.error("No MongoDB URI provided. Database functionality will be disabled.")
                return
                
            self.client = MongoClient(MONGO_URI)
            self.db = self.client[DB_NAME]
            logger.success(f"Connected to MongoDB database: {DB_NAME}")
            
            # Create indexes for better query performance
            self._create_indexes()
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            
    def _create_indexes(self):
        """Create necessary indexes for collections"""
        try:
            # Users collection indexes
            self.db.users.create_index([("user_id", pymongo.ASCENDING)], unique=True)
            
            # Groups collection indexes
            self.db.groups.create_index([("chat_id", pymongo.ASCENDING)], unique=True)
            
            # Global bans collection indexes
            self.db.gbans.create_index([("user_id", pymongo.ASCENDING)], unique=True)
            
            # Warns collection indexes
            self.db.warns.create_index([
                ("chat_id", pymongo.ASCENDING), 
                ("user_id", pymongo.ASCENDING)
            ])
            
            # Notes collection indexes
            self.db.notes.create_index([
                ("chat_id", pymongo.ASCENDING), 
                ("note_name", pymongo.ASCENDING)
            ])
            
            # Filters collection indexes
            self.db.filters.create_index([
                ("chat_id", pymongo.ASCENDING), 
                ("filter_name", pymongo.ASCENDING)
            ])
            
            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.error(f"Failed to create database indexes: {e}")
    
    # User methods
    def get_user(self, user_id):
        """Get user data from database"""
        return self.db.users.find_one({"user_id": user_id})
    
    def save_user(self, user_id, username=None, first_name=None, last_name=None):
        """Save user to database"""
        user_data = {
            "user_id": user_id,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "reputation": 0,
            "warns": []
        }
        
        self.db.users.update_one(
            {"user_id": user_id},
            {"$set": user_data},
            upsert=True
        )
    
    # Group methods
    def get_group(self, chat_id):
        """Get group data from database"""
        return self.db.groups.find_one({"chat_id": chat_id})
    
    def save_group(self, chat_id, title, chat_type):
        """Save group to database"""
        group_data = {
            "chat_id": chat_id,
            "title": title,
            "type": chat_type,
            "welcome_enabled": True,
            "welcome_message": "Welcome to {chat_title}, {user_mention}!",
            "rules": "",
            "joined_at": pymongo.datetime.datetime.now()
        }
        
        self.db.groups.update_one(
            {"chat_id": chat_id},
            {"$set": group_data},
            upsert=True
        )
    
    # Global bans methods
    def get_gbans(self):
        """Get all globally banned users"""
        return list(self.db.gbans.find({}))
    
    def is_user_gbanned(self, user_id):
        """Check if user is globally banned"""
        return self.db.gbans.find_one({"user_id": user_id}) is not None
    
    def gban_user(self, user_id, by_user, reason="No reason provided"):
        """Add user to global ban list"""
        gban_data = {
            "user_id": user_id,
            "banned_by": by_user,
            "reason": reason,
            "timestamp": pymongo.datetime.datetime.now()
        }
        
        self.db.gbans.update_one(
            {"user_id": user_id},
            {"$set": gban_data},
            upsert=True
        )
    
    def ungban_user(self, user_id):
        """Remove user from global ban list"""
        self.db.gbans.delete_one({"user_id": user_id})
    
    # Warns methods
    def warn_user(self, chat_id, user_id, reason="No reason provided", warned_by=None):
        """Add a warning to a user"""
        warning = {
            "reason": reason,
            "warned_by": warned_by,
            "timestamp": pymongo.datetime.datetime.now()
        }
        
        self.db.warns.update_one(
            {"chat_id": chat_id, "user_id": user_id},
            {"$push": {"warnings": warning}},
            upsert=True
        )
        
        # Get the current warning count
        user_warns = self.db.warns.find_one({"chat_id": chat_id, "user_id": user_id})
        return len(user_warns.get("warnings", [])) if user_warns else 1
    
    def get_warns(self, chat_id, user_id):
        """Get all warnings for a user in a chat"""
        user_warns = self.db.warns.find_one({"chat_id": chat_id, "user_id": user_id})
        return user_warns.get("warnings", []) if user_warns else []
    
    def reset_warns(self, chat_id, user_id):
        """Reset all warnings for a user in a chat"""
        self.db.warns.delete_one({"chat_id": chat_id, "user_id": user_id})
    
    # Notes methods
    def save_note(self, chat_id, note_name, content, saved_by):
        """Save a note for a chat"""
        note_data = {
            "chat_id": chat_id,
            "note_name": note_name.lower(),
            "content": content,
            "saved_by": saved_by,
            "updated_at": pymongo.datetime.datetime.now()
        }
        
        self.db.notes.update_one(
            {"chat_id": chat_id, "note_name": note_name.lower()},
            {"$set": note_data},
            upsert=True
        )
    
    def get_note(self, chat_id, note_name):
        """Get a note from a chat"""
        return self.db.notes.find_one(
            {"chat_id": chat_id, "note_name": note_name.lower()}
        )
    
    def delete_note(self, chat_id, note_name):
        """Delete a note from a chat"""
        self.db.notes.delete_one(
            {"chat_id": chat_id, "note_name": note_name.lower()}
        )
    
    def get_all_notes(self, chat_id):
        """Get all notes for a chat"""
        return list(self.db.notes.find({"chat_id": chat_id}))
    
    # Settings methods
    def get_setting(self, chat_id, setting_name):
        """Get a specific setting for a chat"""
        setting = self.db.settings.find_one(
            {"chat_id": chat_id, "setting_name": setting_name}
        )
        return setting.get("value") if setting else None
    
    def save_setting(self, chat_id, setting_name, value):
        """Save a setting for a chat"""
        self.db.settings.update_one(
            {"chat_id": chat_id, "setting_name": setting_name},
            {"$set": {"value": value}},
            upsert=True
        )

# Initialize database
db = Database()