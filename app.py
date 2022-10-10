from flask import Flask, render_template
from flask_pymongo import PyMongo
import pymongo
import flask

app = Flask(__name__)

mongo_client = pymongo.MongoClient("mongo")
database1 = mongo_client["312Project"]  # username database
username_table = database1["usernames"]  # username collection

@app.route('/', methods=['POST', 'GET'])
def hello_world():  # put application's code here
    if flask.request.method == 'POST':
        formUsername = flask.request.form['uname']
        formPassword = flask.request.form['psw']
        # print(formUsername)
        # print(formPassword)
        desiredEntry = list(username_table.find({"username": formUsername}))
        if len(desiredEntry) == 0:
            userInfo = {"username": formUsername, "password": formPassword}
            username_table.insert_one(userInfo)
            return render_template("profile.html")
        else:
            desiredDict = username_table.find_one({"username": formUsername})
            if desiredDict["password"] == formPassword:
                return render_template("profile.html")
            else:
                return render_template("index.html")
        #userEntry(formUsername, formPassword)
    else:
        return render_template("index.html")


def userEntry(username, password):
    desiredEntry = list(username_table.find({"username": username}))
    if len(desiredEntry) == 0:
        userInfo = {"username": username, "password": password}
        username_table.insert_one(userInfo)
        return render_template("profile.html")
    else:
        desiredDict = username_table.find_one({"username": username})
        if desiredDict["password"] == password:
            return render_template("profile.html")
        else:
            return render_template("index.html")

if __name__ == '__main__':
    app.run(host="0.0.0.0")
