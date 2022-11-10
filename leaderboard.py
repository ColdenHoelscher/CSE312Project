from leagues import league_table, player_table




def create_leaderboard(name):
    leaderboard = {}
    player_list = []
    leauge = league_table.find_one({"name":name})   #grabbing the selected leauge
    players =  league_table.find({'name':name})
    for user in players:
        player_list = user['players']
    for x in player_list:
        leaderboard[x] = 0
   # ret_val = sorted(leaderboard,key=leaderboard.get,reverse=True)
    return leaderboard

    
