"""
Auto-DC Bot Main File
Author: fdyytu
Created at: 2025-03-07 18:04:56 UTC
Last Modified: 2025-03-10 22:30:07 UTC
"""

import sys
import os
import discord
import logging
import traceback
from discord.ext import commands
from pathlib import Path

print("Starting bot initialization...")  # Debug output

# Buat direktori logs jika belum ada
try:
    Path("logs").mkdir(exist_ok=True)
    print("Logs directory checked")  # Debug output
except Exception as e:
    print(f"Error creating logs directory: {e}")

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/bot.log', encoding='utf-8')
    ]
)

print("Logging setup complete")  # Debug output

# Load config
try:
    config_path = "config/config.json"
    print(f"Attempting to load config from: {config_path}")  # Debug output
    
    if not os.path.exists(config_path):
        print(f"Config file not found at {config_path}")
        sys.exit(1)
        
    with open(config_path, 'r') as f:
        config = json.load(f)
    print("Config loaded successfully")  # Debug output
except Exception as e:
    print(f"Error loading config: {e}")
    traceback.print_exc()
    sys.exit(1)

# Bot setup
class Bot(commands.Bot):
    def __init__(self):
        print("Initializing bot...")  # Debug output
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(
            command_prefix=config.get('prefix', '!'),
            intents=intents
        )
        print("Bot initialized")  # Debug output

    async def setup_hook(self):
        print("Setting up bot...")  # Debug output
        for ext in ['cogs.admin', 'cogs.utils']:
            try:
                await self.load_extension(ext)
                print(f"Loaded extension: {ext}")  # Debug output
            except Exception as e:
                print(f"Failed to load extension {ext}: {e}")
                traceback.print_exc()

    async def on_ready(self):
        print(f"Bot is ready. Logged in as {self.user}")

async def main():
    try:
        print("Starting main...")  # Debug output
        bot = Bot()
        async with bot:
            print("Attempting to start bot...")  # Debug output
            await bot.start(config['token'])
    except KeyboardInterrupt:
        print("Bot stopped by user")
    except Exception as e:
        print(f"Error running bot: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    print("Script started")  # Debug output
    import asyncio
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Fatal error: {e}")
        traceback.print_exc()