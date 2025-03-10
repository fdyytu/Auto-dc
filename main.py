import sys
import os
import discord
import sqlite3
from discord.ext import commands
import asyncio
import logging
import logging.config
from configparser import ConfigParser

# Fungsi untuk memuat konfigurasi dari file config.txt
def load_config(file_name):
    config = ConfigParser()
    config.read(file_name)
    return config

logging.config.dictConfig({
    'version': 1,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(levelname)s: %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'default'
        }
    },
    'loggers': {
        __name__: {
            'level': 'INFO',
            'handlers': ['console']
        }
    }
})

logger = logging.getLogger(__name__)

# Membaca konfigurasi dari file config.txt dengan validasi
config = load_config('config.txt')
logger.debug("Konfigurasi telah dibaca")

# Inisialisasi intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
logger.debug("Intents telah diinisialisasi")

# Definisi kelas Database
class Database:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

db = None

# Koneksi ke database
try:
    db_path = config.get('DEFAULT', 'LINK_DATABASE')
    if not db_path:
        logger.error("LINK_DATABASE tidak ditemukan dalam konfigurasi")
        print("LINK_DATABASE tidak ditemukan dalam konfigurasi")
    else:
        db = Database(db_path)
        logger.debug("Koneksi ke database telah berhasil")
except Exception as e:
    logger.error(f'Failed to connect to the database: {type(e).__name__} - {e}')
    print(f'Failed to connect to the database: {type(e).__name__} - {e}')
    raise

# Inisialisasi bot
bot = commands.Bot(command_prefix='!', intents=intents)
bot.owner_id = int(config.get('DEFAULT', 'OWNER_ID'))
logger.debug("Bot telah diinisialisasi")

# Memuat cogs
initial_extensions = [
    'cog.admin',
    'cog.live',
    'cog.owner',
    'cog.donation'
]

@bot.event
async def on_ready():
    logger.info(f'Bot is ready. Logged in as {bot.user.name} ({bot.user.id})')
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    print('------')

@bot.event
async def on_command_error(ctx, error):
    logger.error(f'Error in command {ctx.command}: {type(error).__name__} - {error}')
    if isinstance(error, commands.CommandNotFound):
        await ctx.send('Command not found.')
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Missing required argument.')
    elif isinstance(error, commands.BadArgument):
        await ctx.send('Bad argument.')
    else:
        await ctx.send('An error occurred while executing the command.')

async def main():
    # Memuat extensions
    for extension in initial_extensions:
        try:
            await bot.load_extension(extension)
            logger.info(f'Loaded extension: {extension}')
            print(f'Loaded extension: {extension}')
        except Exception as e:
            logger.error(f'Failed to load extension {extension}: {type(e).__name__} - {e}')
            print(f'Failed to load extension {extension}: {type(e).__name__} - {e}')

    # Menjalankan bot
    try:
        await bot.start(config.get('DEFAULT', 'DISCORD_TOKEN'))
    except Exception as e:
        logger.error(f'Failed to start bot: {type(e).__name__} - {e}')
        print(f'Failed to start bot: {type(e).__name__} - {e}')

if __name__ == '__main__':
    asyncio.run(main())