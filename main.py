import sys
import os
import discord
import logging
import logging.config
import json
from discord.ext import commands
from ext.constants import PATHS, EXTENSIONS
from database import setup_database, verify_database

# Fungsi untuk memuat konfigurasi dari file config.json
def load_config(file_name):
    with open(file_name, 'r') as file:
        config = json.load(file)
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

# Membaca konfigurasi dari file config.json dengan validasi
config = load_config(PATHS.CONFIG)
logger.debug("Konfigurasi telah dibaca")

# Inisialisasi intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
logger.debug("Intents telah diinisialisasi")

# Setup dan verifikasi database
try:
    setup_database()
    if not verify_database():
        raise Exception("Database verification failed")
except Exception as e:
    logger.error(f'Failed to setup or verify the database: {type(e).__name__} - {e}')
    sys.exit(1)

# Inisialisasi bot
bot = commands.Bot(command_prefix='!', intents=intents)
bot.owner_id = int(config.get('admin_id'))
logger.debug("Bot telah diinisialisasi")

# Memuat cogs
initial_extensions = EXTENSIONS.ALL

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
        await bot.start(config.get('token'))
    except Exception as e:
        logger.error(f'Failed to start bot: {type(e).__name__} - {e}')
        print(f'Failed to start bot: {type(e).__name__} - {e}')

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())