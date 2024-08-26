import mysql.connector
import requests
import sys
import os

from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database info
dbinfo = [os.getenv('DB_USER'), os.getenv('DB_PASSWORD'), os.getenv('DB_NAME')]
# Connect to the database
db = mysql.connector.connect(host='localhost', port=3306,
								user=dbinfo[0], password=dbinfo[1],
								db=dbinfo[2])
# Create a cursor
cursor = db.cursor()

#delete ppd game from picks table
def delete_ppd_game(game_id):
    cursor.execute("DELETE FROM Picks WHERE game_id = {}".format(game_id))

def get_games(date=None):
    # check if a date was passed in
    if date:
        day = date
    #get all games from previous day from nhl api and return them
    else:
        day = datetime.now() - timedelta(days=1)
        day = day.strftime("%Y-%m-%d")
    url = "https://api-web.nhle.com/v1/schedule/{}".format(day)

    r = requests.get(url)
    try:
        games = r.json()['gameWeek'][0]['games']
        if len(games) == 0:
            return None
    except:
        return None #no games played yesterday

    if len(games) == 0:
        return None
    
    #calculate the number of regular season games played
    num_games = 0
    season = ''
    for game in games:
        if game['gameType'] == 2:
            # check if game is ppd or cancelled
            if game['gameScheduleState'] == 'PPD' or game['gameScheduleState'] == 'CNCL':
                delete_ppd_game(game['id'])
            else:
               num_games += 1
               if season == '':
                   season = game['season']
    
    #if there are no regular season games played, return None
    if num_games == 0:
        return None

    return games, season

def get_game_winners(games):
    #get all game winners from previous day and return them
    winners = []
    for game in games:
        # make sure game is regular season and over
        if game['gameType'] == 2 and game['gameState'] in ['FINAL', 'OFF']:
            if game['awayTeam']['score'] > game['homeTeam']['score']:
                winners.append(str(game['awayTeam']['id']))
            else:
                winners.append(str(game['homeTeam']['id']))
    return winners

def get_picked_teams(date=None):
    user_picks = {}
    if date:
        cursor.execute("SELECT user_id, team_id FROM Picks WHERE cast(picked_at as DATE) = '{}'".format(date))
    #from the database, get all users picks from previous day store picks in dict where user_id is key and return the dict
    else:
        cursor.execute("SELECT user_id, team_id FROM Picks WHERE cast(picked_at as DATE) = cast(now() - interval 1 day as DATE)")
    for row in cursor.fetchall():
        if row[0] in user_picks:
            user_picks[row[0]].append(row[1])
        else:
            user_picks[row[0]] = [row[1]]
    
    return user_picks

def record_exists(user, season):
    #check if user's record exists
    cursor.execute("SELECT * FROM Records WHERE user_id = {} AND season = '{}'".format(user, season))
    if cursor.fetchone():
        return True
    else:
        return False

def create_record(user, season):
    #create user's record
    cursor.execute("INSERT INTO Records (user_id, wins, losses, season) VALUES ({}, 0, 0, '{}')".format(user, season))

def update_record(user, win, season):
    #update user's record
    # get now
    now = datetime.now()

    if win:
        cursor.execute("UPDATE Records SET wins = wins + 1, updated_at = '{}', season = '{}' WHERE user_id = {}".format(now, season, user))
    else:
        cursor.execute("UPDATE Records SET losses = losses + 1, updated_at = '{}', season = '{}' WHERE user_id = {}".format(now, season, user))

try:
    day = None
    if len(sys.argv) > 1:
        day = sys.argv[1]
    games, season = get_games(day)
    if games:
        winners = get_game_winners(games)
        user_picks = get_picked_teams(day)
        print(user_picks)

        for user in user_picks:
            if not record_exists(user, season):
                create_record(user, season)
            for pick in user_picks[user]:
                update_record(user, pick in winners, season)
        db.commit()
except Exception as e:
    #
    print(e)
    db.rollback()
finally:
    cursor.close()
    db.close()