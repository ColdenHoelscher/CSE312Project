from flask import Flask, render_template
import pymongo
import flask
import leagues

app = Flask(__name__)

mongo_client = pymongo.MongoClient("mongo")
database1 = mongo_client["312Project"]  # username database
username_table = database1["usernames"]  # username collection

pools = {
    1: ["Luka Doncic", "Stephen Curry", "Ja Morant", "Trae Young", "Darius Garland"], #center
    2: ["Luka Doncic", "Stephen Curry", "Ja Morant", "Trae Young", "Darius Garland"], #power forward
    3: ["Luka Doncic", "Stephen Curry", "Ja Morant", "Trae Young", "Darius Garland"], #small forward
    4: ["Luka Doncic", "Stephen Curry", "Ja Morant", "Trae Young", "Darius Garland"], #point guard
    5: ["Luka Doncic", "Stephen Curry", "Ja Morant", "Trae Young", "Darius Garland"]  #shooting guard
}

def sanitizeText(text):
    if(not isinstance(text, str)):
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
            warning1 = "username not valid"
            return render_template("index.html", loginStatus=warning1)
        else:
            desiredDict = username_table.find_one({"username": formUsername})
            if desiredDict["password"] == formPassword:  # go to profile username and pw matched
                return render_template("profile.html", User=formUsername)
            else:  # password incorrect
                warning2 = "password incorrect"
                return render_template("index.html", loginStatus=warning2)
    else:
        noWarning = ""
        return render_template("index.html", loginStatus=noWarning)

@app.route('/profile',methods=['POST', 'GET'])
def profileAction():
    if flask.request.method == "GET":
        return render_template("leaguesettings.html")

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if flask.request.method == 'POST':
        formUsername = sanitizeText(flask.request.form['uname'])
        formPassword = flask.request.form['psw']
        if(not validateText(formUsername) and not validateText(formPassword)): #check to make sure its not empty or null
            return render_template("signup.html", signUpStatus="Invalid input")

        desiredEntry = list(username_table.find({"username": formUsername}))
        if len(desiredEntry) != 0:
            return render_template("signup.html", signUpStatus="Username already exists")

        username_table.insert_one({"username": formUsername, "password": formPassword})
        return render_template("profile.html", User=formUsername)
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

@app.route('/league', methods=['POST', 'GET'])
def league_creation_page():
    if flask.request.method == 'POST':
        lname = flask.request.form['lname']
        plist = flask.request.form['plist'].split("\r\n")
        result = leagues.create_league(lname, plist)
        if not result:
            print("Creation Failed")
        leagues.set_points(lname, "ok", 100)
        return render_template("index.html")
    else:
        return render_template("leaguesettings.html")

if __name__ == '__main__':
    app.run(host="0.0.0.0")
