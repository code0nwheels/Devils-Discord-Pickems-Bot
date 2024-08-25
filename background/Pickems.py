import aiohttp
import asyncio
import logging
from logging.handlers import RotatingFileHandler

from Util.GameView import GameView
from Util import create_embed
from datetime import datetime, timedelta
from pytz import timezone
from tzlocal import get_localzone
from discord.utils import get

class Pickems():
    def __init__(self, bot):
        self.bot = bot

        self.db = self.bot.get_cog('Database')
        self.locked_games = []
        self.log = logging.getLogger(__name__)

        # create a rotating file logger; max 5 files, 5MB each
        # add a rotating handler
        handler = RotatingFileHandler('log/pickems.log', maxBytes=5*1024*1024,
                                      backupCount=5)
        # create a logging format
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.log.addHandler(handler)
    
    async def get_team(self, team_id):
        try:
            timeout = aiohttp.ClientTimeout(total=20)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get("https://api.nhle.com/stats/rest/en/team") as resp:
                    data = await resp.json()
        except Exception as e:
            self.log.exception(e)
            return None

        for team in data['data']:
            if team['id'] == team_id:
                return team['fullName']
    
    async def post_game(self, channel_id, embed, view):
        try:
            channel = self.bot.get_channel(channel_id)
            
            m = await channel.send(embed=embed, view=view)

            return f"{str(m.channel.id)}-{str(m.id)}"
        except Exception as e:
            self.log.exception(e)
            return None

    async def update_game(self, message, view):
        try:
            await message.edit(view=view)
        except Exception as e:
            self.log.exception(e)
            pass
    
    async def monitor_games(self):
        while True:
            try:
                games = await self.get_games()

                if games != '':
                    for game_id, game_info in games.items():
                        if game_info[5] and game_id not in self.locked_games:
                            message_id = await self.db.get_message(game_id)
                            if not message_id:
                                self.log.info(f"Game {game_id} not found in database")
                                continue
                            channel = self.bot.get_channel(int(message_id.split('-')[0]))
                            message = await channel.fetch_message(int(message_id.split('-')[1]))

                            buttons = message.components[0].children

                            if game_info[5] and not buttons[0].disabled:
                                self.log.info(f"Locking game {game_id}")
                                view = GameView(self.bot, game_id, *game_info)

                                await self.update_game(message, view)

                                if game_info[5]:
                                    self.locked_games.append(game_id)
                                    print(len(self.locked_games), len(games))
                            elif not game_info[5] and buttons[0].disabled:
                                view = GameView(self.bot, game_id, *game_info)

                                await self.update_game(message, view)

                if len(self.locked_games) == len(games):
                    self.log.info("All games locked")
                    self.locked_games = []
                    break
            except Exception as e:
                self.log.exception(e)
                pass
            await asyncio.sleep(60)


    async def get_games(self, embed=False):
        self.log.info("Getting games")
        all_games = {}
        all_embeds = {}

        localtz = get_localzone()

        curdt = localtz.localize(datetime.now())
        est = curdt.astimezone(timezone('US/Eastern'))
        date = est.strftime('%Y-%m-%d')

        try:        
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api-web.nhle.com/v1/scoreboard/now") as response:
                    games = await response.json()
            for date_ in games['gamesByDate']:
                if date_['date'] == date:
                    games = date_['games']
                    break
        except Exception as e:
            self.log.exception(e)
            if embed:
                return '', None
            return ''

        if len(games) == 0:
            self.log.info("No games today")
            return None, None

        for game in games:
            # determine if game is regular season 
            if game['gameType'] == 2:
                self.log.info(f"Found game {game['id']}")
                game_id = game['id']
                away_id = game['awayTeam']['id']       #Get away team ID for emojiDict
                away_team = await self.get_team(away_id)   #Get away team name
                home_id = game['homeTeam']['id']       #Get home team ID for emojiDict
                home_team = await self.get_team(home_id)   #Get home team name
                gamestatus = game['gameState']            #Get game status
                schedstatus = game['gameScheduleState'] #Get schedule status
                #Get game time
                game_time = game['startTimeUTC']
                # get season
                season = game['season']
                
                # determine if now in utc is before game time
                game_time = datetime.strptime(game_time, '%Y-%m-%dT%H:%M:%SZ')
                now = datetime.utcnow()

                disabled = now >= game_time or gamestatus in ['FINAL', 'LIVE', 'OFF'] or schedstatus in ['PPD', 'SUSP', 'CNCL']

                all_games[str(game_id)] = [away_id, away_team, home_id, home_team, season, disabled]

                if embed:
                    embed = await create_embed.create_game(game)
                    all_embeds[str(game_id)] = embed
        
        if len(all_games) == 0:
            self.log.info("No games today")
            return None, None
            
        if embed:
            return all_games, all_embeds
        else:
            return all_games

    async def run(self):
        count = 0

        while True:
            games, embeds = await self.get_games(True)

            if games == '' and count < 5:
                await asyncio.sleep(60)
                count += 1
                continue

            if games is not None and games != '':
                # find the daily-pickems channel
                channel = get(self.bot.get_all_channels(), name='daily-pickems')
                for game_id, game_info in games.items():
                    try:
                        view = GameView(self.bot, game_id, *game_info)

                        message_id = await self.db.get_message(game_id)
                        if not message_id:
                            message_id = await self.post_game(channel.id, embeds[game_id], view)
                            if message_id is None:
                                continue
                            await self.db.create_message(message_id, game_id)

                        self.bot.add_view(view, message_id=int(message_id.split('-')[1]))
                    except Exception as e:
                        self.log.exception(e)
                        pass
            
                await self.monitor_games()
            #sleep until 3am
            now = datetime.now()
            to = (now + timedelta(days = 1)).replace(hour=3, minute=8, second=0)
            print(f"Sleeping for {to - now}")
            await asyncio.sleep((to - now).total_seconds())