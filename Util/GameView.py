from discord.ui import Button, View
from discord import ButtonStyle

from datetime import datetime
from pytz import timezone
from tzlocal import get_localzone

from Util.dicts import emojiDict, teamDict

class GameView(View):
    def __init__(self, bot, game_id, away_id, away_team, home_id, home_team, season, disabled=False) -> None:
        super().__init__()
        self.game_id = game_id
        self.away_id = away_id
        self.away_team = away_team
        self.home_id = home_id
        self.home_team = home_team

        self.db = bot.get_cog('Database')

        away_emoji = None
        home_emoji = None
        away_button_style = ButtonStyle.gray
        home_button_style = ButtonStyle.gray

        if away_id == 1:
            away_button_style = ButtonStyle.red
        if home_id == 1:
            home_button_style = ButtonStyle.red

        if str(away_id) in emojiDict:
            away_emoji = emojiDict[str(away_id)]
        
        if str(home_id) in emojiDict:
            home_emoji = emojiDict[str(home_id)]

        away_button = Button(label=away_team, custom_id=f"{game_id}-{away_id}-{season}", emoji=away_emoji, disabled=disabled, style=away_button_style)
        self.add_item(away_button)
        away_button.callback = self.button_callback

        home_button = Button(label=home_team, custom_id=f"{game_id}-{home_id}-{season}", emoji=home_emoji, disabled=disabled, style=home_button_style)
        self.add_item(home_button)
        home_button.callback = self.button_callback

        self.timeout = None
    
    async def button_callback(self, interaction):
        localtz = get_localzone()
        esttz = timezone('US/Eastern')

        curdt = localtz.localize(datetime.now())
        est = curdt.astimezone(esttz)

        user_id = interaction.user.id
        game_id = interaction.custom_id.split('-')[0]
        team_id = interaction.custom_id.split('-')[1]
        season = interaction.custom_id.split('-')[2]
        team_name = teamDict[str(team_id)]

        pick = await self.db.get_pick(user_id, game_id)

        if pick:
            if pick != team_id:
                if await self.db.update_pick(user_id, game_id, team_id, est):
                    await interaction.response.send_message(f"Pick updated to {team_name}!", ephemeral=True, delete_after=5)
                else:
                    await interaction.response.send_message(f"Something went wrong! Try again in a few minutes.", ephemeral=True, delete_after=5)
            else:
                await interaction.response.send_message(f"You already picked {team_name}!", ephemeral=True, delete_after=5)
        else:
            if await self.db.create_pick(user_id, game_id, team_id, season, est):
                await interaction.response.send_message(f"You picked {team_name}!", ephemeral=True, delete_after=5)
            else:
                await interaction.response.send_message(f"Something went wrong! Try again in a few minutes.", ephemeral=True, delete_after=5)