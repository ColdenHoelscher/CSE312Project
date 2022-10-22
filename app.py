from flask import Flask, render_template
from flask_pymongo import PyMongo
import pymongo
import flask

app = Flask(__name__)

mongo_client = pymongo.MongoClient("mongo")
database1 = mongo_client["312Project"]  # username database
username_table = database1["usernames"]  # username collection

@app.route('/', methods=['POST', 'GET'])
def hello_world():  # put application's code here for login page
    if flask.request.method == 'POST':
        formUsername = flask.request.form['uname']
        formPassword = flask.request.form['psw']
        formUsername = formUsername.replace('&', '&#38;')
        formUsername = formUsername.replace('<', '&#60;')
        formUsername = formUsername.replace('>', '&#62;')
        desiredEntry = list(username_table.find({"username": formUsername}))
        if len(desiredEntry) == 0:  # username is not in the database
            # userInfo = {"username": formUsername, "password": formPassword}
            # username_table.insert_one(userInfo)
            # return render_template("profile.html", User=formUsername)
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


if __name__ == '__main__':
    app.run(host="0.0.0.0")
