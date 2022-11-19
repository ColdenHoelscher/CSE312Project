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
    league['isDrafting'] = True
    league_members = list(user_table.find({"joinedLeagues": league_name}))
    random.shuffle(league_members)
    print(league_members)

    