# Telegram Management Bot

A comprehensive Telegram bot that combines features from @Lena_MilizeBot and @MissRose_Bot with added global ban/unban functionality. Built with Python using the Telethon library and MongoDB for data storage.

## Features

- User management (ban, kick, mute, etc.)
- Global ban/unban system
- Welcome messages
- Notes and filters
- MongoDB integration
- Heroku deployment support
- Error handling and logging

## Requirements

- Python 3.8 or higher
- MongoDB server
- Telegram API credentials (API ID and API Hash)
- Bot token from BotFather

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/telegram-management-bot.git
cd telegram-management-bot
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure the bot

Create a `.env` file in the project root directory:

```
# Bot API Credentials
API_ID=123456
API_HASH=abcdef1234567890abcdef1234567890
BOT_TOKEN=1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ

# Database Connection
MONGODB_URI=mongodb://localhost:27017/telegram_bot

# Bot Owner and Privileged Users
OWNER_ID=1234567890
SUDO_USERS=1234567890,9876543210
SUPPORT_USERS=
WHITELIST_USERS=

# Bot Settings
COMMAND_PREFIX=!
BOT_USERNAME=YourBotUsername
```

### 4. Run the bot

```bash
python bot.py
```

## Deployment to Heroku

### 1. Create Heroku app

```bash
heroku create your-telegram-bot
```

### 2. Add MongoDB add-on

```bash
heroku addons:create mongolab
```

### 3. Set environment variables

```bash
heroku config:set API_ID=123456
heroku config:set API_HASH=abcdef1234567890abcdef1234567890
heroku config:set BOT_TOKEN=1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ
heroku config:set OWNER_ID=1234567890
heroku config:set SUDO_USERS=1234567890,9876543210
heroku config:set BOT_USERNAME=YourBotUsername
```

### 4. Deploy to Heroku

```bash
git push heroku main
```

## Command Reference

### Basic Commands
- `/start` - Start the bot
- `/help` - Show help message
- `/ping` - Check bot's response time
- `/id` - Get user/chat ID
- `/info` - Get user information

### Admin Commands
- `/ban <user> [reason]` - Ban a user
- `/unban <user>` - Unban a user
- `/kick <user> [reason]` - Kick a user
- `/mute <user> [duration] [reason]` - Mute a user
- `/unmute <user>` - Unmute a user
- `/pin` - Pin a message
- `/unpin` - Unpin a message
- `/unpinall` - Unpin all messages

### Global Ban Commands (Sudo users only)
- `/gban <user> [reason]` - Globally ban a user
- `/ungban <user>` - Remove global ban from a user
- `/gbanlist` - List all globally banned users

### Notes Commands
- `/save <name> <content>` - Save a note
- `/get <name>` - Get a note
- `#<name>` - Get a note
- `/notes` - List all notes
- `/clear <name>` - Delete a note

### Filters Commands
- `/filter <keyword> <content>` - Add a filter
- `/filters` - List all filters
- `/stop <keyword>` - Delete a filter

### Welcome Commands
- `/setwelcome <message>` - Set welcome message
- `/welcome on/off` - Toggle welcome messages
- `/welcome` - Show current welcome settings
- `/resetwelcome` - Reset to default welcome

## Project Structure

```
telegram-management-bot/
├── bot.py                  # Main bot file
├── requirements.txt        # Python dependencies
├── Procfile               # Heroku Procfile
├── runtime.txt            # Python runtime for Heroku
├── .env                   # Environment variables (not committed)
├── .env.example           # Example environment variables
├── config.yaml            # Additional configuration
├── .gitignore             # Git ignore file
├── README.md              # Project documentation
├── src/                   # Source code
│   ├── config.py          # Configuration handler
│   ├── database/          # Database handlers
│   │   ├── __init__.py
│   │   └── database.py
│   ├── handlers/          # Command handlers
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── basic.py
│   │   ├── errors.py
│   │   ├── filters.py
│   │   ├── gban.py
│   │   ├── notes.py
│   │   └── welcome.py
│   └── utils/             # Utility functions
│       ├── __init__.py
│       ├── logger.py
│       ├── permissions.py
│       └── time.py
└── logs/                  # Log files (not committed)
```

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgements

- [Telethon](https://github.com/LonamiWebs/Telethon)
- Inspired by [@Lena_MilizeBot](https://t.me/Lena_MilizeBot) and [@MissRose_Bot](https://t.me/MissRose_Bot)