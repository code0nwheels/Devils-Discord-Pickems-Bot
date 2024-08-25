import discord

from discord.ext import commands

from background.Pickems import Pickems

intents = discord.Intents.default()
intents.message_content = True

with open("token.txt", "r") as f:
    token = f.read()

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

bot.run(token)