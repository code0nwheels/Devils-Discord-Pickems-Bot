# import pycord commands
import os
import discord
from discord.commands import Option
from discord.ext import commands
from discord import default_permissions

from datetime import datetime

from background.Leaderboard import Leaderboard
from Util import create_embed
from Util.dicts import teamDict

from dotenv import load_dotenv

load_dotenv()
guild_id = int(os.getenv('GUILD_ID'))

class BotCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.leaderboard = Leaderboard(bot)

        self.db = bot.get_cog('Database')

    @commands.slash_command(guild_ids=[guild_id], name="get_leaderboard", description="Get the full leaderboard")
    async def get_leaderboard(self, ctx):
        # get the paginated leaderboard
        paginator = await self.leaderboard.setup_paginator()
        # send the paginated leaderboard
        await paginator.respond(ctx.interaction, ephemeral=True)
    
    @commands.slash_command(guild_ids=[guild_id], name="get_user_position", description="Get a user's leaderboard position")
    async def get_user_position(self, ctx, user: Option(discord.User, required = False) = None):
        # get the user
        if user is None:
            user = ctx.author
        
        # make user a string
        user_str = str(user.id)
        # get the user's position
        position = await self.leaderboard.get_user_position(user_str)

        if position:
            # extract winsm losses, and position
            wins = position[1]
            losses = position[2]
            position = position[4]

            # send the user's position
            await ctx.respond(f"{user.mention} is in position {position} with {wins} wins and {losses} losses", ephemeral=True)
        else:
            await ctx.respond(f"{user.mention} is not in the leaderboard", ephemeral=True)
    
    # command to get a user's picks for a date
    # date is optional, if not provided, get today's picks
    @commands.slash_command(guild_ids=[guild_id], name="get_picks", description="Get your picks for a date")
    async def get_picks(self, ctx, date: Option(str, required = False, description="The date of the picks in yyyy-mm-dd format. Omit for today.") = None):
        # check if date is provided; if not, get today's date. if so, check if it's a valid date and convert to datetime
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        else:
            try:
                datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                await ctx.respond("Invalid date", ephemeral=True)
                return
        
        # get the user's picks
        picks = await self.db.get_user_picks(str(ctx.author.id), date)
        # if picks is None, the user has no picks for the date
        if picks is None:
            await ctx.respond(f"{ctx.author.mention} has no picks for {date}", ephemeral=True)
        else:
            # convert team ids to team names
            picks = [teamDict[team] for team in picks]
            # create the embed
            embed = await create_embed.create_user_picks_embed(ctx.author, picks, date)
            # send the embed
            await ctx.respond(embed=embed, ephemeral=True)

    @commands.slash_command(guild_ids=[guild_id], name='kill', description='Kills the bot. ADMIN ONLY!')
    @default_permissions(administrator=True)
    async def kill(self, ctx):
        await ctx.respond("Goodbye cruel world!")
        os.system("service pickemsbot stop")
    
    @commands.slash_command(guild_ids=[guild_id], name='restart', description='Restarts the bot. ADMIN ONLY!')
    @default_permissions(administrator=True)
    async def restart(self, ctx):
        await ctx.respond("Be right back!")
        os.system("service pickemsbot restart")
    
    # post the leaderboard - ADMIN ONLY
    @commands.slash_command(guild_ids=[guild_id], name='post_leaderboard', description='Post the leaderboard. ADMIN ONLY!')
    @default_permissions(administrator=True)
    async def post_leaderboard(self, ctx):
        await self.leaderboard.post_leaderboard()
        await ctx.respond("Leaderboard posted!")

# add the cog to the bot
def setup(bot):
    bot.add_cog(BotCommands(bot))