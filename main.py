import discord
import os
from discord.ext import commands
from background.Pickems import Pickems
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(intents=intents)

bot.load_extension('sql.database')
bot.load_extension('cogs.bot_commands')

#TODO:
# - Best way to store user button clicks?
#       - one array per team?
# - Can you get the button ID anywhere?
# - Best way to let users edit their responses?

@bot.event
async def on_ready():
    p = Pickems(bot)
    bot.loop.create_task(p.run())

bot.run(os.getenv('TOKEN'))