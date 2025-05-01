#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import yaml
from dotenv import load_dotenv
from loguru import logger

class Config:
    """Configuration class for the bot."""
    
    def __init__(self):
        """Initialize the configuration by loading environment variables and config file."""
        # Load environment variables from .env file if it exists
        load_dotenv()
        
        # Bot API credentials
        self.api_id = int(os.getenv("API_ID", 0))
        self.api_hash = os.getenv("API_HASH", "")
        self.bot_token = os.getenv("BOT_TOKEN", "")
        
        # Database connection
        self.mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/telegram_bot")
        
        # Bot configuration
        self.owner_id = int(os.getenv("OWNER_ID", 0))
        self.sudo_users = self._parse_list_env("SUDO_USERS")
        self.support_users = self._parse_list_env("SUPPORT_USERS")
        self.whitelist_users = self._parse_list_env("WHITELIST_USERS")
        
        # Bot settings
        self.command_prefix = os.getenv("COMMAND_PREFIX", "!")
        self.bot_username = os.getenv("BOT_USERNAME", "")
        self.backup_chat_id = int(os.getenv("BACKUP_CHAT_ID", 0))
        
        # Load additional configuration from config.yaml if available
        self.config_file = os.getenv("CONFIG_FILE", "config.yaml")
        self._load_config_file()
        
        # Validate configuration
        self._validate_config()
    
    def _parse_list_env(self, env_name):
        """Parse a comma-separated list from an environment variable."""
        value = os.getenv(env_name, "")
        if not value:
            return []
        return [int(x.strip()) for x in value.split(",") if x.strip().isdigit()]
    
    def _load_config_file(self):
        """Load additional configuration from a YAML file."""
        if not os.path.exists(self.config_file):
            logger.warning(f"Config file {self.config_file} not found, using defaults")
            return
        
        try:
            with open(self.config_file, "r") as file:
                yaml_config = yaml.safe_load(file)
                
            if not yaml_config:
                return
                
            # Update configuration with values from YAML file
            for key, value in yaml_config.items():
                if hasattr(self, key) and getattr(self, key) == "":
                    setattr(self, key, value)
                    
            logger.info(f"Loaded configuration from {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to load config file: {e}")
    
    def _validate_config(self):
        """Validate the configuration to ensure required values are set."""
        if self.api_id == 0:
            logger.warning("API_ID is not set")
        if not self.api_hash:
            logger.warning("API_HASH is not set")
        if not self.bot_token:
            logger.warning("BOT_TOKEN is not set")
        if self.owner_id == 0:
            logger.warning("OWNER_ID is not set")
    
    def is_owner(self, user_id):
        """Check if a user is the bot owner."""
        return user_id == self.owner_id
    
    def is_sudo(self, user_id):
        """Check if a user has sudo privileges."""
        return user_id in self.sudo_users or self.is_owner(user_id)
    
    def is_support(self, user_id):
        """Check if a user has support privileges."""
        return user_id in self.support_users or self.is_sudo(user_id)
    
    def is_whitelisted(self, user_id):
        """Check if a user is whitelisted."""
        return user_id in self.whitelist_users or self.is_support(user_id)