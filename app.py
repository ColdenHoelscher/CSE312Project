from flask import Flask, render_template, session
from flask_socketio import SocketIO, emit
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
                return render_template("profile.html", User=formUsername, leagues=leaguesList, leaguesJ=joinedLeagues, leaguesC=ownedLeagues)
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
        return render_template("profile.html", User=formUsername, leagues=leaguesList)
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

    return render_template("profile.html", User=retDoc['username'], leagues=leaguesList, leaguesJ=finalJoined)


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
        return render_template("profile.html", User=retDoc['username'], leagues=leaguesList, leaguesJ=finalJoined)


@socketio.on('start draft')
def call_draft(incoming):
    print('received: ' + str(incoming))
    draft.start_draft(str(incoming))


if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0")