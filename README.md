# Activity Manager Bot

A Discord bot built with `discord.py` to manage server activity checks. The bot sends activity check messages to a specified channel, DMs all server members, and restricts certain commands to specific roles.

## Features
- **/help or !help**: Displays an embed with all available commands, including a banner and the requesting user's info.
- **/activity or !activity**: Sends an activity check message to a configured channel with a dynamic timestamp (2 days from now) and DMs all members. Restricted to specific roles defined in `config.json`.

## Requirements
- Python 3.8 or higher
- Discord bot token (from [Discord Developer Portal](https://discord.com/developers/applications))
- `discord.py` library

## Setup Instructions
1. **Clone or Download the Project**
   - Download the project files or clone the repository.

2. **Install Dependencies**
   - Create a virtual environment (optional but recommended):
     ```bash
     python -m venv venv
     source venv/bin/activate  # On Windows: venv\Scripts\activate
     ```
   - Install required packages:
     ```bash
     pip install -r requirements.txt
     ```

3.  **Configure the bot**
     - Open `config.json` and fill in the following:
     ```json
     {
  "server_id": 123456789012345678,
  "server_name": "Your Server Name",
  "activity_channel_id": 123456789012345678,
  "allowed_roles": [
    123456789012345678,
    123456789012345679,
    123456789012345680
  ]
}
    ```
    
    ```
     - server_id: The ID of the target server (right-click server > Copy ID with Developer Mode enabled).
     - server_name: The name of your server (e.g., "Glory Guild").
     - activity_channel_id: The ID of the channel for activity check messages (right-click channel > Copy ID).
     - allowed_roles: List of role IDs allowed to use the /activity command.
     ```

## Usage
     ```
     - /help or !help: Shows an embed with command details.
     - /activity or !activity: Sends an activity check message to the configured channel and DMs all members. Only roles listed in config.json can use this command.
     ```


# Troubleshooting
     ```
     - Bot not responding: Verify the bot token, intents, and permissions.
     - Channel/server not found: Check server_id and activity_channel_id in config.json.
     - DM failures: Some members may have DMs disabled or have blocked the bot.
     ```
