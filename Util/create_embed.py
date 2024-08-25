import discord
from pytz import timezone
from datetime import datetime

from Util.dicts import emojiDict
from hockey import hockey

RECORD_TEMPLATE = "{}-{}-{}"

async def create_game(game):
	away_id = game['awayTeam']['id']
	#team = await hockey.get_team(away_id)
	away_team = await hockey.get_team(away_id)
	home_id = game['homeTeam']['id']
	#team = await hockey.get_team(home_id)
	home_team = await hockey.get_team(home_id)

	if game['gameType'] == 2:
		away_wins, away_losses, away_ot = game['awayTeam']['record'].split('-')
		home_wins, home_losses, home_ot = game['homeTeam']['record'].split('-')

		away_record = RECORD_TEMPLATE.format(away_wins, away_losses, away_ot)
		home_record = RECORD_TEMPLATE.format(home_wins, home_losses, home_ot)

		away_pts = int(away_wins) * 2 + int(away_ot)
		home_pts = int(home_wins) * 2 + int(home_ot)
		away_record = f"{away_pts} PTS " + away_record
		home_record = f"{home_pts} PTS " + home_record
	else:
		away_record = ""
		home_record = ""

	venue = game['venue']['default']

	utctz = timezone('UTC')
	esttz = timezone('US/Eastern')
	time = game['startTimeUTC']
	utc = datetime.strptime(time, "%Y-%m-%dT%H:%M:%SZ")
	utc2 = utctz.localize(utc)
	est = utc2.astimezone(esttz)

	epoch = int(est.timestamp())

	if game['gameScheduleState'] == 'TBD':
		time = 'TBD'
	else:
		time = f"<t:{epoch}:t>" #time = datetime.strftime(est,  "%-I:%M %p")
	date = f"<t:{epoch}:D>" #date = datetime.strftime(est,  "%B %-d, %Y")

	embed = discord.Embed(title=date, color=0xff0000)
	embed.add_field(name=away_team, value=away_record, inline=True)
	#embed.add_field(name="\u200b", value="\u200b", inline=True)
	embed.add_field(name=home_team, value=home_record, inline=True)
	embed.add_field(name="Time", value=time, inline=False)
	embed.add_field(name="Venue", value=venue, inline=True)
	#embed.set_footer(text=cmd)

	return embed

# Create a leaderboard embed
# Args: ranks - a dict containing the records of the users, keys are user IDs, values are list of wins, losses, win%, rank number
#       updated_at - a string containing the time the leaderboard was last updated
# footer: Last updated at <updated_at>
# omit embed field names 
async def create_leaderboard(ranks: dict, updated_at: str):
	ranks_str = ""
	embed = discord.Embed(color=0xff0000)
	embed.set_footer(text=f"Last updated at {updated_at}")
	for user_id, record in ranks.items():
		ranks_str += f"{record[3]}. <@{user_id}> {record[0]}-{record[1]} ({round(record[2]*100, 3)}%)\n"
		#embed.add_field(name="\u200b", value=f"{record[3]}. <@{user_id}> {record[0]}-{record[1]} ({round(record[2]*100, 3)}%)", inline=False)
	embed.description = ranks_str.strip()
	return embed

# Create a user picks embed
async def create_user_picks_embed(user: str, picks: list, date: str):
	embed = discord.Embed(title=f"{user}'s Picks for {date}", color=0xff0000)
	picks_str = ""

	for i, pick in enumerate(picks):
		picks_str += f"{i+1}. {pick}\n"
	
	embed.description = picks_str.strip()
	return embed