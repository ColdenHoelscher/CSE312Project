import random

import app
import leagues

league_table = leagues.league_table
user_table = app.username_table


# Return true if worked, false if failed
def start_draft(league_name):
    table_result = list(league_table.find({"name": league_name}))
    if len(table_result) == 0:
        print("Could not start draft, league not found.")
        return False
    league = table_result[0]
    if league['isDrafting']:
        print("Could not start draft, drafting already in progress.")
        return False
    # Set variable to true, locking anyone from joining the league
    league_table.update_one({"name": league_name}, {"$set": {"isDrafting": True}})
    # Find users in league and randomly shuffle list
    league_members = list(user_table.find({}))
    user_list = []
    for anEntry in league_members:
        if league_name in anEntry["joinedLeagues"]:
            user_list.append(anEntry["username"])
    random.shuffle(user_list)
    return user_list

    