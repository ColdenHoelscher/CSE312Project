import time
import pymongo


mongo_client = pymongo.MongoClient("mongo")
database = mongo_client["312Project"]
stat_table = database["stats"]



def isLogged(username):
    collection = []
    for x in stat_table.find({"username":username}):
        collection.append(x)
    print(collection)
    return collection


def addup(current,new):
    i_stat = int(current)
    n_stat = int(new)
    retval = i_stat + n_stat
    return str(retval)
    



def checkTime(timez):
    week = 604800.0
    current_time = time.time()
    if current_time - timez < week:
        return False
    else:
        return True


def input(entry):
    log  = isLogged(entry["username"])
    if len(log) > 0:
        if checkTime(log[0]["time"]):
            update_points =  entry["points"]
            update_rebounds = entry["rebounds"]
            update_assists = entry["assists"]
            current_points = log[0]["points"]
            current_rebounds = log[0]["rebounds"]
            current_assists = log[0]["assists"]
            current_time = time.time()
            stat_table.update_one({"username":entry["username"]},{"$set":{"time":current_time}})
            stat_table.update_one({"username":entry["username"]},{"$set":{"points":addup(current_points,update_points)}})
            stat_table.update_one({"username":entry["username"]},{"$set":{"rebounds":addup(current_rebounds,update_rebounds)}})
            stat_table.update_one({"username":entry["username"]},{"$set":{"assists":addup(current_assists,update_assists)}})
            score = calculate_score({"username":entry["username"],"rebounds":addup(current_rebounds,update_rebounds),"assists":addup(current_assists,update_assists),"points":addup(current_points,update_points)})
            return score
        else:
            return 0
    update_points =  entry["points"]
    update_rebounds = entry["rebounds"]
    update_assists = entry["assists"]
    score = calculate_score({"username":entry["username"],"rebounds":update_rebounds,"assists":update_assists,"points":update_points})
    current = time.time()
    stat_table.insert_one({"time":current,"username":entry["username"],"rebounds":update_rebounds,"assists":update_assists,"points":update_points,"score":score})
    return score

def calculate_score(entry):
    score =  int(entry["points"]) + int(entry["rebounds"]) * 1.2 + int(entry["assists"]) * 1.5
    return score
    











