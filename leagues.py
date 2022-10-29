import json

import pymongo
import app

mongo_client = pymongo.MongoClient("mongo")
database = mongo_client["312Project"]
league_table = database["leagues"]
player_table = database["players"]


# Returns true if successful, false if not.
def create_league(name, players):
    result = list(league_table.find({"name": name}))
    if len(result) != 0:
        return False
    pnames = []
    for player in players:
        player_name = escape_all(player)
        pnames.append(player_name)
        player_table.insert_one({"name": player_name, "points": 0})
    ldata = {"name": escape_all(name), "players": pnames}
    league_table.insert_one(ldata)
    return True


# Returns true if successful, false if not.
def change_name(old_name, newname):
    name = escape_all(old_name)
    result = list(league_table.find({"name": name}))
    if len(result) == 0:
        # League given does not exist, can't change name.
        return False
    else:
        league_table.update_one({"name": name}, {"$set": {"name": newname}})
        return True

def escape_all(text):
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    return text.replace("'", '&#39;')
