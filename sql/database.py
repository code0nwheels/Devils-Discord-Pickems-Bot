import aiomysql
import os
from discord.ext import commands
from dotenv import load_dotenv

import logging
from logging.handlers import RotatingFileHandler

class Database(commands.Cog):
	def __init__(self, bot):
		load_dotenv()

		self.bot = bot
		self.pool = None
		logging.basicConfig(level=logging.INFO)
		self.log = logging.getLogger(__name__)
		# add a rotating handler
		handler = RotatingFileHandler('log/db.log', maxBytes=5*1024*1024,
									  backupCount=5)

		# create a logging format
		formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
		handler.setFormatter(formatter)
		self.log.addHandler(handler)

	async def login(self):
		dbinfo = (os.getenv('DB_USER'), os.getenv('DB_PASSWORD'), os.getenv('DB_NAME'))

		self.pool = await aiomysql.create_pool(host='localhost', port=3306,
								user=dbinfo[0], password=dbinfo[1],
								db=dbinfo[2], loop=self.bot.loop)
	async def query(self, statement, *values):
		good = False
		if self.pool is None:
			await self.login()
		try:
			async with self.pool.acquire() as conn:
				async with conn.cursor() as cur:
					try:
						await cur.execute(statement, values)
						await conn.commit()
						good = True
					except Exception as e:
						await conn.rollback()
						self.log.exception("Error committing")
		except Exception as e:
			self.log.exception("Error")

		return good

	async def fetch(self, statement, *values):
		if self.pool is None:
			await self.login()
		data = None
		try:
			async with self.pool.acquire() as conn:
				async with conn.cursor() as cur:
					try:
						await cur.execute(statement, values)
						data = await cur.fetchall()
						await conn.commit()
					except Exception as e:
						await conn.rollback()
						self.log.exception("Error committing")
		except Exception as e:
			self.log.exception("Error")

		return data

	async def create_message(self, message_id, game_id):
		sql = """INSERT INTO Messages (message_id, game_id)
		VALUES (%s, %s);"""

		return await self.query(sql, message_id, game_id)

	async def get_message(self, game_id):
		sql = "SELECT message_id from Messages where game_id = %s;"

		m = await self.fetch(sql, game_id)

		return m[0][0] if m else None
	
	async def create_pick(self, user_id, game_id, team_id, season, picked_at):
		sql = """INSERT INTO Picks (user_id, game_id, team_id, season, picked_at)
		VALUES (%s, %s, %s, %s, %s);"""

		return await self.query(sql, user_id, game_id, team_id, season, picked_at)
	
	async def get_pick(self, user_id, game_id):
		sql = """SELECT team_id FROM Picks WHERE user_id = %s AND game_id = %s"""

		team = await self.fetch(sql, user_id, game_id)

		return team[0][0] if team else None
	
	async def update_pick(self, user_id, game_id, team_id, picked_at):
		sql = """UPDATE Picks
		SET team_id = %s, picked_at = %s
		WHERE user_id = %s AND game_id = %s;"""

		return await self.query(sql, team_id, picked_at, user_id, game_id)
	
	# get all records from the Records table
	# fields: user_id, wins, losses
	# put into a dict with user_id as key
	# return dict
	async def get_records(self):
		sql = "SELECT user_id, wins, losses FROM Records;"

		records = await self.fetch(sql)

		return {r[0]: r[1:] for r in records}
	
	# get the leaderboard from the leaderboard view
	# fields: user_id, wins, losses, win_pct, rank
	# put into a dict with user_id as key
	# return dict
	async def get_leaderboard(self):
		sql = "SELECT * FROM Leaderboard;"

		leaderboard = await self.fetch(sql)

		return {l[0]: l[1:] for l in leaderboard}
	
	# get the max updated_at from the Records table
	# return datetime
	async def get_records_updated_at(self):
		sql = "SELECT MAX(updated_at) FROM Records;"

		updated_at = await self.fetch(sql)

		return updated_at[0][0]
	
	# get the record and rank from the leaderboard view for a user
	# fields: user_id, wins, losses, win_pct, rank
	# return tuple
	async def get_user_leaderboard_position(self, user_id):
		sql = "SELECT * FROM Leaderboard WHERE user_id = %s;"

		user = await self.fetch(sql, user_id)

		return user[0] if user else None
	
	# get the user's picks for a date
	# fields: team_id
	# return list of team_ids
	async def get_user_picks(self, user_id, date):
		sql = """SELECT team_id FROM Picks
		WHERE user_id = %s AND cast(picked_at as date) = %s;"""

		picks = await self.fetch(sql, user_id, date)

		return [p[0] for p in picks]

def setup(bot):
	bot.add_cog(Database(bot))
