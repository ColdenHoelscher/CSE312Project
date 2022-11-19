import pymongo

mongo_client = pymongo.MongoClient("mongo")
database = mongo_client["312Project"]
league_table = database["leagues"]


# Returns true if successful, false if not.
def create_league(name):
    result = list(league_table.find({"name": name}))
    if len(result) != 0:
        return False
    player_names = []
    player_file = open("playerlist.txt", 'r')
    players = player_file.readlines()
    for p in players:
        player_names.append(p.strip())
    league_data = {"name": escape_all(name), "isDrafting": False, "players": player_names}
    league_table.insert_one(league_data)
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
