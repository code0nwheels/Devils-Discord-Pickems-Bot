import discord
from pytz import timezone
from tzlocal import get_localzone
from discord.utils import get

import discord.ext.pages as pages

from Util import create_embed

class Leaderboard():
    def __init__(self, bot) -> None:
        self.bot = bot
        self.db = bot.get_cog('Database')
    
    # set up a paginator for the leaderboard embeds
    # each page will be a leaderboard embed with 10 leaderboards each
    # Args: leaderboards - dict of leaderboards containing user_id, wins, losses; user_id is key
    async def setup_paginator(self):
        # fetch most recent records updated_at from db
        records_updated = await self.db.get_records_updated_at()
        # get the leaderboard from db
        leaderboard_ = await self.db.get_leaderboard()
            
        # convert records_updated to ET
        localtz = get_localzone()
        esttz = timezone('US/Eastern')

        curdt = localtz.localize(records_updated)
        est = curdt.astimezone(esttz)
        
        # format est to month day, year at h:mm; ex: January 1, 2021 at 4:30am
        est_str = est.strftime('%B %d, %Y at %I:%M%p ET')

        # list of leaderboards
        leaderboards_list = {}

        # create leaderboard embeds
        embeds = []

        for i, leaderboard in enumerate(leaderboard_):
            # add leaderboard to leaderboards_list
            leaderboards_list[leaderboard] = leaderboard_[leaderboard]

            # if 10 leaderboards have been added to leaderboards_list, create leaderboard embed
            if (i + 1) % 10 == 0:
                embed = await create_embed.create_leaderboard(leaderboards_list, est_str)
                embeds.append(embed)
                leaderboards_list.clear()
        if leaderboards_list:
            embed = await create_embed.create_leaderboard(leaderboards_list, est_str)
            embeds.append(embed)

        # create paginator
        paginator = pages.Paginator(pages=embeds)

        # set up buttons
        paginator.add_button(
            pages.PaginatorButton(
                "first", label='<<', style=discord.ButtonStyle.red, loop_label="fst"
            )
        )
        paginator.add_button(
            pages.PaginatorButton(
                "prev", label="<", style=discord.ButtonStyle.green, loop_label="prv"
            )
        )
        paginator.add_button(
            pages.PaginatorButton(
                "page_indicator", style=discord.ButtonStyle.gray, disabled=True
            )
        )
        paginator.add_button(
            pages.PaginatorButton(
                "next", label='>', style=discord.ButtonStyle.green, loop_label="nxt"
            )
        )
        paginator.add_button(
            pages.PaginatorButton(
                "last", label='>>', style=discord.ButtonStyle.red, loop_label="lst"
            )
        )

        return paginator
    
    # get a user's rank in the leaderboard; use get_user_leaderboard_position in Database.py
    # Args: user_id - user's id
    # Returns: rank - user's rank and record in leaderboard
    async def get_user_position(self, user_id):
        return await self.db.get_user_leaderboard_position(user_id)
    
    # post leaderboard embed to channel
    async def post_leaderboard(self):
        # fetch most recent records updated_at from db
        records_updated = await self.db.get_records_updated_at()
        # convert records_updated to ET
        localtz = get_localzone()
        esttz = timezone('US/Eastern')
        curdt = localtz.localize(records_updated)
        est = curdt.astimezone(esttz)
        
        # format est to month day, year at h:mm; ex: January 1, 2021 at 4:30am
        est_str = est.strftime('%B %d, %Y at %I:%M%p ET')

        # get leaderboards from db
        leaderboards = await self.db.get_leaderboard()

        if leaderboards:
            # get first 10 leaderboards
            leaderboards_list = {}
            for i, leaderboard in enumerate(leaderboards):
                leaderboards_list[leaderboard] = leaderboards[leaderboard]
                if i == 9:
                    break
            
            # create leaderboard embed
            embed = await create_embed.create_leaderboard(leaderboards_list, est_str)

            # post embed to channel
            # find channel by name
            channel = get(self.bot.get_all_channels(), name='leaderboard')
            await channel.send(embed=embed)