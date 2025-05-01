import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_USERNAME = os.getenv("BOT_USERNAME", "")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
SUDO_USERS = list(map(int, os.getenv("SUDO_USERS", "").split(","))) if os.getenv("SUDO_USERS") else []
SUPPORT_CHAT = os.getenv("SUPPORT_CHAT", "")
LOGS_CHANNEL = int(os.getenv("LOGS_CHANNEL", "0"))

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "moderationbot")

# Collections
GROUPS_COLLECTION = "groups"
USERS_COLLECTION = "users"
GBANS_COLLECTION = "gbans"
WARNS_COLLECTION = "warns"
NOTES_COLLECTION = "notes"
FILTERS_COLLECTION = "filters"
SETTINGS_COLLECTION = "settings"

# Feature Flags
ENABLE_GLOBAL_BANS = os.getenv("ENABLE_GLOBAL_BANS", "true").lower() == "true"
ENABLE_SPAM_PROTECTION = os.getenv("ENABLE_SPAM_PROTECTION", "true").lower() == "true"
ENABLE_WELCOME_MSG = os.getenv("ENABLE_WELCOME_MSG", "true").lower() == "true"
ENABLE_ANALYTICS = os.getenv("ENABLE_ANALYTICS", "true").lower() == "true"

# Time constants (in seconds)
BAN_TIME_LIMIT = int(os.getenv("BAN_TIME_LIMIT", "7200"))  # 2 hours default
MESSAGE_DELETION_TIMEOUT = int(os.getenv("MESSAGE_DELETION_TIMEOUT", "15"))  # 15 seconds default

# Version info
VERSION = "1.0.0"