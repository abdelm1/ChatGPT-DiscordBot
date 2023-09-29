
# Discord Bot with OpenAI GPT-4 Integration

This Discord bot is designed to provide a versatile and interactive chatbot experience for your Discord server, powered by OpenAI's GPT-4 model. It includes features such as message logging to a MySQL database, Google search integration, and personalized responses based on user-defined personalities.

## Table of Contents

- [Features](#features)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Configuration](#configuration)
  - [Running the Bot](#running-the-bot)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Features

- Integration with OpenAI's GPT-4 model for generating chatbot responses.
- Message logging to a MySQL database for archiving and analysis.
- Google search functionality for retrieving information.
- Personalized responses based on user-defined personalities.
- Presence status customization on Discord.

## Getting Started

To get your Discord bot up and running, follow these steps:

### Prerequisites

1. **Python:** Ensure you have Python installed on your system. This script is written in Python and requires Python 3.x.

2. **Discord Bot Token:** Create a Discord bot and obtain its token. You'll need this token to authenticate your bot with the Discord API.

3. **OpenAI API Key:** You'll need an OpenAI API key. Visit the OpenAI website to obtain one.

4. **MySQL Database:** You'll need a MySQL database to store message logs. Set up a MySQL server and create a database for this purpose.

### Configuration

1. Clone this repository to your local machine:

   ```bash
   git clone https://github.com/ZPIDERr/ChatGPT-DiscordBot.git
   ```

2. Navigate to the project directory and open the `config.json` file.

3. Update the `openai_api_key` and `discord_token` fields with your OpenAI API key and Discord bot token, respectively.

4. Customize other configuration options as needed, including personalities, presence, and any additional API keys.

### Running the Bot

1. Install the required Python packages using pip:

   ```bash
   pip install -r requirements.txt
   ```

2. Run the bot script:

   ```bash
   python bot.py
   ```

Your Discord bot should now be up and running in your server.

## Usage

Interacting with the Discord bot is straightforward. Simply mention the bot in your messages to trigger its responses and use the provided commands. Here's how to get started:

1. **General Chat:** To engage with the bot in a conversation, mention it in your message. For example, `@YourBot Hello, how are you today?` The bot will respond based on the conversation context and its configured personality.

2. **Google Search:** The bot offers a powerful Google search feature. To initiate a Google search, use the `!search` command followed by your search query. For instance, `@YourBot !search Who is the president of USA right now` The bot will perform the search and provide relevant results.

Feel free to customize and expand the bot's capabilities to suit your server's needs. Experiment with different messages, questions, and commands to interact with your Discord bot effectively.


Feel free to customize and expand the bot's capabilities to suit your server's needs.


