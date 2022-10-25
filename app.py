from flask import Flask, render_template
from flask_pymongo import PyMongo
import pymongo
import flask

app = Flask(__name__)

mongo_client = pymongo.MongoClient("mongo")
database1 = mongo_client["312Project"]  # username database
username_table = database1["usernames"]  # username collection

def sanitizeText(text):
    if(not isinstance(text, str)):
        return
    return text.replace('&', '&#38;').replace('<', '&#60;').replace('>', '&#62;')

def validateText(text):
    return text and len(text.strip()) != 0
@app.route('/', methods=['POST', 'GET'])
def hello_world():  # put application's code here for login page
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


if __name__ == '__main__':
    app.run(host="0.0.0.0")
