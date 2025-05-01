# Advanced Telegram Moderation Bot

A powerful Telegram moderation bot with global ban capabilities, combining the best features of @Lena_MilizeBot and @MissRose_Bot.

## Features

- **Global Ban System**: Ban users across all groups where the bot is admin
- **Advanced Group Management**: Customizable welcome messages, notes, filters
- **User Tracking**: Keep track of user warnings and infractions
- **Spam Protection**: Detect and prevent spam messages
- **Detailed Logging**: Complete logs of all moderation actions

## Setup

### Prerequisites

- Python 3.8+
- MongoDB database
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))

### Installation

1. Clone this repository:
```
git clone https://github.com/yourusername/telegram-moderation-bot.git
cd telegram-moderation-bot
```

2. Install the requirements:
```
pip install -r requirements.txt
```

3. Create a `.env` file by copying the example:
```
cp .env.example .env
```

4. Edit the `.env` file with your configuration details:
```
# Bot Configuration
BOT_TOKEN=your_bot_token_from_botfather
BOT_USERNAME=your_bot_username
OWNER_ID=your_telegram_id
SUDO_USERS=admin1_id,admin2_id
SUPPORT_CHAT=your_support_chat_username
LOGS_CHANNEL=logs_channel_id

# MongoDB Configuration
MONGO_URI=your_mongodb_connection_string
DB_NAME=moderationbot
```

5. Start the bot:
```
python app.py
```

### Deploying to Heroku

1. Make sure you have the Heroku CLI installed
2. Login to Heroku:
```
heroku login
```

3. Create a new Heroku app:
```
heroku create your-bot-name
```

4. Add the MongoDB add-on or use your own MongoDB instance:
```
heroku addons:create mongolab:sandbox
```

5. Set the environment variables:
```
heroku config:set BOT_TOKEN=your_bot_token
heroku config:set OWNER_ID=your_telegram_id
# Set other variables as needed
```

6. Deploy the bot:
```
git push heroku main
```

7. Start the worker:
```
heroku ps:scale worker=1
```

## Commands

### Basic Commands
- `/start` - Start the bot
- `/help` - Show help message
- `/ping` - Check bot's response time
- `/info` - Get info about a user

### Admin Commands
- `/ban` - Ban a user from the group
- `/unban` - Unban a user
- `/kick` - Kick a user without banning
- `/mute` - Mute a user
- `/unmute` - Unmute a user
- `/warn` - Warn a user
- `/unwarn` - Remove warnings from a user
- `/promote` - Promote a user to admin
- `/demote` - Demote an admin to regular user
- `/pin` - Pin a message in the chat
- `/unpin` - Unpin a message
- `/purge` - Delete multiple messages at once

### Group Management
- `/welcome` - Set welcome message
- `/togglewelcome` - Toggle welcome messages
- `/setrules` - Set group rules
- `/rules` - View group rules
- `/note` - Save a note
- `/get` - Get a saved note
- `/notes` - List all notes
- `/filter` - Add a word filter
- `/stopfilter` - Remove a filter
- `/filters` - List all filters

### Global Commands (Admin Only)
- `/gban` - Globally ban a user
- `/ungban` - Remove global ban

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Credits

- Based on the functionality of @Lena_MilizeBot and @MissRose_Bot
- Built with python-telegram-bot
- Uses MongoDB for database storage