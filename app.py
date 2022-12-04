from flask import Flask, render_template, session
from flask_socketio import SocketIO, emit, send
import pymongo
import flask
import bcrypt
import secrets
import draft
import leagues
import secretkey

app = Flask(__name__)
app.secret_key = secretkey.secretkey
app.config['SECRET_KEY'] = secretkey.secretkey
socketio = SocketIO(app)

mongo_client = pymongo.MongoClient("mongo")
database1 = mongo_client["312Project"]  # username database
username_table = database1["usernames"]  # username collection
draft_table = database1["drafting"]  # draft info
roster_table = database1["rosters"]



# pools = {
#     1: ["Luka Doncic", "Stephen Curry", "Ja Morant", "Trae Young", "Darius Garland"],  # center
#     2: ["Luka Doncic", "Stephen Curry", "Ja Morant", "Trae Young", "Darius Garland"],  # power forward
#     3: ["Luka Doncic", "Stephen Curry", "Ja Morant", "Trae Young", "Darius Garland"],  # small forward
#     4: ["Luka Doncic", "Stephen Curry", "Ja Morant", "Trae Young", "Darius Garland"],  # point guard
#     5: ["Luka Doncic", "Stephen Curry", "Ja Morant", "Trae Young", "Darius Garland"]  # shooting guard
# }


def sanitizeText(text):
    if (not isinstance(text, str)):
        return
    return text.replace('&', '&#38;').replace('<', '&#60;').replace('>', '&#62;')


def validateText(text):
    return text and len(text.strip()) != 0


@app.route('/', methods=['POST', 'GET'])
def login():  # put application's code here for login page
    if flask.request.method == 'POST':
        formUsername = sanitizeText(flask.request.form['uname'])
        formPassword = flask.request.form['psw']

        desiredEntry = list(username_table.find({"username": formUsername}))
        if len(desiredEntry) == 0:  # username is not in the database
            warning1 = "No account associated with this username."
            return render_template("index.html", loginStatus=warning1)
        else:
            desiredDict = username_table.find_one({"username": formUsername})
            if bcrypt.checkpw(formPassword.encode(), desiredDict["password"]):  # go to profile username and pw matched
                # Update authToken
                token = secrets.token_hex(20)
                hashedToken = bcrypt.hashpw(token.encode(), bcrypt.gensalt())
                username_table.update_one({"username": formUsername}, {"$set": {"authToken": hashedToken}})
                session["token"] = hashedToken  # Create cookie for authentication token
                # Implement code for viewing leagues
                leaguesList = list(leagues.league_table.find({}))
                joinedLeagues = desiredDict["joinedLeagues"]
                ownedLeagues = desiredDict["createdLeagues"]
                do_draft = decideUserTurn()
                return render_template("profile.html", User=formUsername, leagues=leaguesList, leaguesJ=joinedLeagues, leaguesC=ownedLeagues,
                                       doSocket=do_draft)
            else:  # password incorrect
                warning2 = "password incorrect"
                return render_template("index.html", loginStatus=warning2)
    else:
        noWarning = ""
        return render_template("index.html", loginStatus=noWarning)


@app.route('/profile', methods=['POST', 'GET'])  # goes to league creation page
def profileAction():
    if flask.request.method == "GET":
        if not session.get("token"):
            return render_template("index.html")
        return render_template("leaguesettings.html")

@app.route('/logout', methods=['GET'])  # logs user out returning to index.html and invalidating token cookie
def logoutAction():
    if flask.request.method == 'GET':
        session["token"] = b'invalid'  # Doesn't match old token stored in database
        return render_template("index.html")


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if flask.request.method == 'POST':
        formUsername = sanitizeText(flask.request.form['uname'])
        formPassword = flask.request.form['psw']
        if (not validateText(formUsername) and not validateText(formPassword)):  # check to make sure its not empty or null
            return render_template("signup.html", signUpStatus="Invalid input")

        desiredEntry = list(username_table.find({"username": formUsername}))
        if len(desiredEntry) != 0:
            return render_template("signup.html", signUpStatus="Username already exists")

        # Implement code for viewing leagues
        leaguesList = list(leagues.league_table.find({}))
        # store salted hash of psw, create token for cookie, store hashed token
        hashedPW = bcrypt.hashpw(formPassword.encode(), bcrypt.gensalt())
        token = secrets.token_hex(20)
        hashedToken = bcrypt.hashpw(token.encode(), bcrypt.gensalt())
        username_table.insert_one({"username": formUsername, "password": hashedPW, "authToken": hashedToken, "joinedLeagues": [], "createdLeagues": []})
        session["token"] = hashedToken  # Create cookie for authentication token
        do_draft = decideUserTurn()
        return render_template("profile.html", User=formUsername, leagues=leaguesList, doSocket=do_draft)
    else:
        return render_template("signup.html", signUpStatus="")


@app.route('/changename', methods=['POST'])
def change_name_form():
    old_name = flask.request.form['oldname']
    new_name = flask.request.form['newname']
    result = leagues.change_name(old_name, new_name)
    if not result:
        print("Could not change name")
    return render_template("index.html")


@app.route('/makeleague', methods=['POST', 'GET'])
def league_creation_page():
    if flask.request.method == 'POST':
        lname = flask.request.form['lname']
        result = leagues.create_league(lname)
        if not result:
            print("Creation Failed")
        # leagues.set_points(lname, "ok", 100)
        # before return edit username table entry to show they created and joined this league
        retrievedDoc = username_table.find_one({"authToken": session["token"]})
        updatedCreated = retrievedDoc['createdLeagues']
        updatedJoined = retrievedDoc['joinedLeagues']
        updatedCreated.append(leagues.escape_all(lname))
        updatedJoined.append(leagues.escape_all(lname))
        username_table.update_one({"authToken": session["token"]}, {"$set": {"joinedLeagues": updatedJoined, "createdLeagues": updatedCreated}})
        return render_template("index.html")
    else:
        return render_template("leaguesettings.html")


# This route puts the user selected league from view leagues menu into their joined leagues list if not already there
@app.route('/viewLeagues', methods=['GET'])
def joinLeague():
    option = flask.request.args.get("unjoined")
    validLeague = list(leagues.league_table.find({"name": option}))
    if validLeague != 0:
        retrievedDoc = username_table.find_one({"authToken": session["token"]})
        updatedJoined = retrievedDoc['joinedLeagues']
        if option not in updatedJoined:
            updatedJoined.append(option)
            username_table.update_one({"authToken": session["token"]}, {"$set": {"joinedLeagues": updatedJoined}})
    leaguesList = list(leagues.league_table.find({}))
    retDoc = username_table.find_one({"authToken": session["token"]})
    finalJoined = retDoc['joinedLeagues']
    do_draft = decideUserTurn()
    return render_template("profile.html", User=retDoc['username'], leagues=leaguesList, leaguesJ=finalJoined, doSocket=do_draft)


@app.route('/viewJoinedL', methods=['GET'])
def viewJoinedLeague():
    option = flask.request.args.get("joined")
    validLeague = list(leagues.league_table.find({"name": option}))
    if validLeague != 0:
        return render_template("startleague.html")
    else:
        leaguesList = list(leagues.league_table.find({}))
        retDoc = username_table.find_one({"authToken": session["token"]})
        finalJoined = retDoc['joinedLeagues']
        do_draft = decideUserTurn()
        return render_template("profile.html", User=retDoc['username'], leagues=leaguesList, leaguesJ=finalJoined, doSocket=do_draft)


@app.route('/draft', methods=['GET'])
def doDraft():
    option = flask.request.args.get("owned")
    # Update league_table isDrafting and add entry to draft_table
    random_list = draft.start_draft(option)
    league_data = leagues.league_table.find_one({"name": option})
    picks_left = {}
    for user in random_list:
        picks_left[user] = 5  # each user will have 5 picks initially (this number will decrement with every pick)
    draft_entry = {"leagueName": option, "unpickedPlayers": league_data["players"], "picksLeft": picks_left, "userList": random_list}
    draft_table.insert_one(draft_entry)
    # Now reload profile html and conditional decides if websocket connection will establish
    retDoc = username_table.find_one({"authToken": session["token"]})
    leaguesList = list(leagues.league_table.find({}))
    finalJoined = retDoc['joinedLeagues']
    do_draft = decideUserTurn()
    return render_template("profile.html", User=retDoc['username'], leagues=leaguesList, leaguesJ=finalJoined, doSocket=do_draft)

def decideUserTurn():
    wanted_entry = username_table.find_one({"authToken": session["token"]})
    # Iterate through joinedLeagues and check if they are drafting and username in front of userList in league
    username = wanted_entry['username']
    joined_leagues = wanted_entry["joinedLeagues"]
    for league in joined_leagues:
        league_data = leagues.league_table.find_one({"name": league})
        if league_data["isDrafting"] == True:  # Check if draft in progress
            draft_data = draft_table.find_one({"leagueName": league})
            user_list = draft_data['userList']
            if username in user_list and user_list[0] == username:  # Check if it's the user's turn
                return True
    return False

@socketio.on('message')
def updateRoster(pick):
    print("User: " + pick)
    # check if roster_table has matching league entry, if not make one
    # first get draft_table entry
    wanted_entry = username_table.find_one({"authToken": session["token"]})
    username = wanted_entry['username']
    draft_league = list(draft_table.find({}))
    draft_info = draft_league[0]  # simple placeholder for now until loop below finishes
    for entry in draft_league:
        if username in entry['userList']:
            draft_info = entry  # draft_info now has needed picksLeft and userList
    roster_entry = list(roster_table.find({"leagueName": draft_info['leagueName']}))
    if len(roster_entry) == 0:
        scoresDict = {}
        rosterDict = {}
        for aVal in draft_info['userList']:
            scoresDict[aVal] = 0
            rosterDict[aVal] = []
        enter_dict = {"leagueName": draft_info['leagueName'], "scoresDict": scoresDict, "rosterDict": rosterDict}
        roster_table.insert_one(enter_dict)
    # now process pick using draft_info and roster_entry[0]
    remaining_players = draft_info['unpickedPlayers']
    if pick == "see players":  # if user wants to see available players send them that
        player_message = ""
        for aPlayer in remaining_players:
            player_message = player_message + "\n" + aPlayer
        send(player_message)
    # do this if they don't wish to see available players
    else:
        picks_dict = draft_info['picksLeft']
        picks_remaining = picks_dict[username]
        if pick in remaining_players:
            if picks_remaining > 0:
                message = pick + "added to roster."
                # update rosterDict
                wantedRosterEntry = roster_table.find_one({"leagueName": draft_info['leagueName']})
                oldRosterDict = wantedRosterEntry['rosterDict']
                oldRosterList = oldRosterDict[username]
                oldRosterList.append(pick)
                oldRosterDict[username] = oldRosterList
                roster_table.update_one({"leagueName": draft_info['leagueName']}, {"$set": {"rosterDict": oldRosterDict}})
                # update unpickedPlayers and picksLeft
                remaining_players.remove(pick)
                picks_user = draft_info['picksLeft']
                new_number_left = picks_user[username] - 1
                picks_user[username] = new_number_left
                draft_table.update_one({"leagueName": draft_info['leagueName']}, {"$set": {"unpickedPlayers": remaining_players, "picksLeft": picks_user}})
                # if picksLeft now zero update userList
                if new_number_left == 0:
                    old_user_list = draft_info['userList']
                    old_user_list.remove(username)
                    draft_table.update_one({"leagueName": draft_info['leagueName']}, {"$set": {"userList": old_user_list}})
                send(message)
            else:  # inform user they used up their picks
                no_picks = "No more picks left"
                send(no_picks)
        else:  # inform user player isn't available
            not_available = "Player isn't available"
            send(not_available)


if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0")