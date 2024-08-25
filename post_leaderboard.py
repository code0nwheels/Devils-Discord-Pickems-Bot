import discord

from datetime import datetime
from pytz import timezone
from tzlocal import get_localzone
from Util.Leaderboard import Leaderboard

# get the bot's token from token.txt 
with open('token.txt', 'r') as f:
    token = f.read()

# create the bot
bot = discord.Bot()

bot.load_extension('sql.database')

# on ready
@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

    try:
        # get the latest records updated at
        records_updated = await bot.get_cog('Database').get_records_updated_at()
        print('Records updated at: {}'.format(records_updated))
        # compare the latest records updated at to the current time
        localtz = get_localzone()
        esttz = timezone('US/Eastern')
        curdt = localtz.localize(datetime.now())
        est = curdt.astimezone(esttz)
        
        if records_updated.date() == est.date():
            # create leaderboard object
            leaderboard = Leaderboard(bot)

            # post leaderboard message
            await leaderboard.post_leaderboard()
    except Exception as e:
        print(e)

    # close the bot
    await bot.close()

# run the bot
bot.run(token)