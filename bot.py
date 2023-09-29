import re
import os
import json
import openai
import discord
import logging
from collections import deque
from discord.ext import commands
import requests
from datetime import datetime
import mysql.connector.pooling

# Define MySQL connection pool configuration
dbconfig = {
    "pool_name": "mypool",
    "pool_size": 20,
    "host": "",
    "user": "",
    "password": "",
    "database": "",
}

owners = [1066525772807942235]


# Create a connection pool
connection_pool = mysql.connector.pooling.MySQLConnectionPool(**dbconfig)

# Create a dictionary to store user-specific conversation histories
user_conversations = {}


def get_mysql_connection():
    return connection_pool.get_connection()


def log_message(role, content):
    try:
        mysql_connection = get_mysql_connection()
        mysql_cursor = mysql_connection.cursor()

        sql_query = "INSERT INTO message_logs (role, content) VALUES (%s, %s)"
        values = (role, content)
        mysql_cursor.execute(sql_query, values)
        mysql_connection.commit()

        # Close the cursor and release the connection back to the pool
        mysql_cursor.close()
        mysql_connection.close()
    except Exception as e:
        print(f"Error logging message: {e}")

# Initialize the message_logs table if it doesn't exist
def create_message_logs_table():
    try:
        mysql_connection = get_mysql_connection()
        mysql_cursor = mysql_connection.cursor()

        create_table_query = """
        CREATE TABLE IF NOT EXISTS message_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            role VARCHAR(255) NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """

        mysql_cursor.execute(create_table_query)
        mysql_connection.commit()

        # Close the cursor and release the connection back to the pool
        mysql_cursor.close()
        mysql_connection.close()
    except Exception as e:
        print(f"Error creating message_logs table: {e}")

# Call this function to create the table
create_message_logs_table()

script_dir = os.path.dirname(os.path.realpath(__file__))
config_path = os.path.join(script_dir, 'config.json')
with open(config_path) as config_file:
    config = json.load(config_file)

logger = logging.getLogger('discord')

openai.api_key = config["openai_api_key"]

intents = discord.Intents.all()
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix="<@{bot.user.id}>", intents=intents)

history = deque()
history_length = 0

context = config["context"]

global_personality = config["global_personality"]
id=0
def get_user(user):
    for entry in context:
        if entry["discord_name"].lower() == user.lower():
            return entry
    return None

def get_messages(sender, recipient, message):
    sender = sender.lower()
    sender_role = "assistant" if sender == "assistant" else "user"
    role = recipient.lower() if sender == "assistant" else sender

    user = get_user(role)
    personality = user['personality'] if user else config["global_personality"]

    bot_context=config["system_context"]

    system_role={"role": "system", "content": f"{bot_context}."}

    prefix='' if sender_role == 'assistant' else f"{personality}"
    add_message({"role": sender_role, "content": f"{prefix} {message}"})

    return [
      system_role,
      *[{"role": obj['role'], "content": obj['content']} for obj in history]
    ]

async def perform_google_search(message, text):
    api_key_google = ""
    cse_id = ""

    url = f'https://www.googleapis.com/customsearch/v1?q={text}&key={api_key_google}&cx={cse_id}'
    image_search_url = f'https://www.googleapis.com/customsearch/v1?q={text}&key={api_key_google}&cx={cse_id}&searchType=image'

    #web search
    response = requests.get(url)
    data = response.json()

    #image search
    image_response = requests.get(image_search_url)
    image_data = image_response.json()
    #extract images from data
    image_results = image_data.get('items', [])[:5]

    results_displayed = 0
    source_links = []

    # Extract and display the relevant information from the JSON response
    for item in data.get('items', []):
        title = item.get('title', 'No title available')
        snippet = item.get('snippet', 'No snippet available')
        link = item.get('link', 'No link available')

        snippet = ' '.join(snippet.split()[:150])  # Adjust the number of words to increase the length

        results_displayed += 1
        source_links.append(link)

        if results_displayed >= 4:  # Change this number to control the number of results displayed
            break

    text_to_summarize = '\n'.join([f'{title}\n{snippet}' for item in data.get('items', [])])
    
    add_message({"role": "user", "content": text})

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that can write short paragraphs and give answers from provided content."},
            {"role": "user", "content": text_to_summarize},
            {"role": "assistant", "content": f"Please provide a most suitable concised answer from {text_to_summarize} related to {text}"}
        ]
    )

    assistant_summary = response['choices'][0]['message']['content']
    add_message({"role": "assistant", "content": assistant_summary})

    #add individual image to the history
    for result in image_results:
        add_message({"role": "assistant", "content": result['link']})
    # Send the search results, source links and images to the channel
    await message.channel.send(assistant_summary)
    await message.channel.send(source_links)
    await message.channel.send("Image Results:")
    for result in image_results:
        await message.channel.send(result['link'])
    logger.info(f"Search result:" + assistant_summary)

async def generate_response(message):
    try:
        if message.author == bot.user:
            return

        if message.content.startswith("!search"):
            query = message.content.replace("!search", "").strip()
            logger.info(f"User {message.author.name} initiated a search: {query}")
            await perform_google_search(message, query)
            logger.info("Added query to the history")
            return

        def call_openai_api():
            logger.info('Making a call to the OpenAI API')
            return openai.ChatCompletion.create(
                model=config["model"],
                messages=get_messages(message.author.name, 'assistant', message.content)
            )

        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="a " + message.author.name))
        async with message.channel.typing():
            global id
            user_message = message.content
            logger.info(f"User {message.author.mention}: message: {user_message}")
            id=id+1
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_message("user","["+timestamp+"] --\n"+str(id)+" " + message.author.mention + ": " + user_message)
            
            response = await bot.loop.run_in_executor(None, call_openai_api)
            content = response['choices'][0]['message']['content']
            logger.info(f"Bot response: {content}")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_message('assistant', timestamp + " " + content)
            
            await message.reply(content)
            
            logger.info("Tokens: " + str(response["usage"]["total_tokens"]))

        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=config["presence"]))

    except Exception as e:
        message.reply(config["error_message"])
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=config["presence"]))
        logging.error(f"Error generating response: {e}", exc_info=True)


def add_message(message):
    global history_length
    message_length = len(str(message))
    logger.info(f'Adding message of length {message_length} to history')

    while history_length > config["memory_characters"]:
        oldest_message = history.popleft()
        history_length -= len(str(oldest_message))
        logger.info(f'Removed message from history. Current history length is {history_length}')

    history.append(message)
    history_length += message_length
    logger.info(f'Added message to history. Current history length is {history_length}')

@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user} (ID: {bot.user.id})')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=config["presence"]))
    
    # Fetch message logs from the MySQL database
    try:
        mysql_connection = get_mysql_connection()
        mysql_cursor = mysql_connection.cursor()

        mysql_cursor.execute("SELECT role, content FROM message_logs")
        message_logs = mysql_cursor.fetchall()
        
        # Clear the existing history and load messages from the database
        history.clear()
        for row in message_logs:
            role, content = row
            add_message({"role": role, "content": content})
        
        logger.info(f"Fetched and stored {len(message_logs)} message logs.")
        
        # Close the cursor and release the connection back to the pool
        mysql_cursor.close()
        mysql_connection.close()
    except Exception as e:
        logger.error(f"Error fetching message logs from MySQL: {e}", exc_info=True)

    await bot.tree.sync()


@bot.event
async def on_message(message):
    if message.content.startswith(f'<@{bot.user.id}> !allow'):
        # Extract the server ID from the message content
        server_id = message.content.split(' ')[2]
        print("server_id", server_id)
        # Check if the user who issued the command is the bot owner
        if message.author.id in owners:
            try:
                # Insert the server ID into the authorized_servers table in MySQL
                sql_query = "INSERT INTO authorized_servers (server_id) VALUES (%s)"
                values = (server_id,)
                mysql_connection = get_mysql_connection()  # Get a connection from the pool
                mysql_cursor = mysql_connection.cursor()
                mysql_cursor.execute(sql_query, values)
                mysql_connection.commit()
                await message.channel.send(f"Bot is now authorized for server {server_id}.")
                
                # Close the cursor and release the connection back to the pool
                mysql_cursor.close()
                mysql_connection.close()
            except Exception as e:
                await message.channel.send(f"An error occurred: {e}")
        else:
            await message.channel.send("You are not authorized to use this command.")
    elif message.content.startswith(f'<@{bot.user.id}> !unallow'):
        # Check if the user who issued the command is the bot owner
        if message.author.id in owners:
            # Split the message content to get the server ID
            split_content = message.content.split(' ')
            if len(split_content) == 3:
                server_id = split_content[2]
                try:
                    # Delete the server ID from the authorized_servers table in MySQL
                    sql_query = "DELETE FROM authorized_servers WHERE server_id = %s"
                    values = (server_id,)
                    mysql_connection = get_mysql_connection()  # Get a connection from the pool
                    mysql_cursor = mysql_connection.cursor()
                    mysql_cursor.execute(sql_query, values)
                    mysql_connection.commit()
                    await message.channel.send(f"Bot is no longer authorized for server {server_id}.")
                    
                    # Close the cursor and release the connection back to the pool
                    mysql_cursor.close()
                    mysql_connection.close()
                except Exception as e:
                    await message.channel.send(f"An error occurred: {e}")
            else:
                await message.channel.send("Invalid command format. Use `<@{bot.user.id}> !unallow server_id`.")
        else:
            await message.channel.send("You are not authorized to use this command.")
    elif message.content.startswith(f'<@{bot.user.id}>'):
        # Extract the user ID from the message content
        user_id = re.findall(r'<@!?(\d+)>', message.content)[0]
        message.content = message.content.replace(f'<@{user_id}>', '').strip()

        # Check if the server is in the authorized_servers table
        check_query = "SELECT COUNT(*) FROM authorized_servers WHERE server_id = %s"
        values = (message.guild.id,)

        try:
            mysql_connection = get_mysql_connection()  # Get a connection from the pool
            mysql_cursor = mysql_connection.cursor()

            mysql_cursor.execute(check_query, values)
            result = mysql_cursor.fetchone()
            if result and result[0] > 0:
                # Process messages only from authorized servers
                await generate_response(message)
            else:
                # Respond to messages from unauthorized servers
                await message.channel.send("This server is not authorized to use the bot.")
                
            # Close the cursor and release the connection back to the pool
            mysql_cursor.close()
            mysql_connection.close()
        except Exception as e:
            await message.channel.send(f"An error occurred: {e}")


bot.run(config["discord_token"])
