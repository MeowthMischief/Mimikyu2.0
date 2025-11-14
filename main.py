import discord
from discord.ext import commands
import os
import asyncio
from database import Database
from config import EMBED_COLOR, PREFIX

# Setup intents
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

# Create bot instance with configurable prefix and case insensitive commands
# Remove default help command to use custom one
bot = commands.Bot(
    command_prefix=commands.when_mentioned_or(PREFIX), 
    intents=intents, 
    case_insensitive=True, 
    help_command=None
)

# Initialize database
db = None

@bot.event
async def on_ready():
    global db
    # Initialize database connection
    mongodb_uri = os.getenv('MONGODB_URI')
    db = Database(mongodb_uri)
    await db.connect()
    
    # Make database accessible to cogs
    bot.db = db
    
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} guilds')
    print(f'Command prefix: {PREFIX} or @{bot.user.name}')
    
    # Load cogs FIRST
    await load_cogs()
    
    # THEN sync slash commands globally (after cogs are loaded)
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} slash command(s)')
        # Print the command names for debugging
        for cmd in synced:
            print(f'  - /{cmd.name}')
    except Exception as e:
        print(f'Failed to sync commands: {e}')

async def load_cogs():
    """Load all cogs from the cogs folder"""
    cogs_list = [
        'cogs.event',
        'cogs.pokemonlist',
        'cogs.helprelease', 
        'cogs.helpevolve',
        'cogs.pokemonquesthelper',
        'cogs.helpcommands'
    ]
    
    for cog in cogs_list:
        try:
            await bot.load_extension(cog)
            print(f'Loaded cog: {cog}')
        except Exception as e:
            print(f'Failed to load cog {cog}: {e}')

@bot.event
async def on_message(message):
    """Process commands from messages"""
    if message.author.bot:
        return
    
    await bot.process_commands(message)

@bot.event
async def on_message_edit(before, after):
    """Process commands from edited messages"""
    if after.author.bot:
        return
    
    await bot.process_commands(after)

@bot.event
async def on_command_error(ctx, error):
    """Global error handler"""
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.reply(f'❌ Missing required argument: `{error.param.name}`', mention_author=False)
    elif isinstance(error, commands.MissingPermissions):
        await ctx.reply('❌ You do not have permission to use this command.', mention_author=False)
    elif isinstance(error, commands.BadArgument):
        await ctx.reply(f'❌ Invalid argument provided. Please check your input.', mention_author=False)
    else:
        await ctx.reply(f'❌ An error occurred: {str(error)}', mention_author=False)
        print(f'Error in command {ctx.command}: {error}')

# Run the bot
if __name__ == '__main__':
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print('Error: DISCORD_TOKEN not found in environment variables')
    else:
        bot.run(token)
