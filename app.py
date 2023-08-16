from flask import Flask, jsonify, request
import pymongo

app = Flask(__name__)

"""try: 
    mongo = pymongo.MongoClient(
        host = "localhost",
        port = 27017,
        severlSelectionTimeout = 1000
    )
    mongo.server_info() # trigger exception if cannot connect to database 
except: 
    print("ERROR- cannot connect to db")"""

#mongodata = {"Hello":"World"}
@app.route('')
def login(): 
    return '<h1>TV Tracker<h1>'

@app.route("/users", methods=["GET","POST"])
def get_users():
    if request.method == "GET":
        # Handle Mongo queries here
        data = query.all()
        # return data to jsonify method
        return jsonify(mongodata)

    elif request.method == "POST":
        post_data = request.json["key"]
        print(post_data)
        # Handle Mongo interactions here

    return "request handled"

@app.route("/tvshows", methods=["GET","POST"])
def get_tvshows():
    if request.method == "GET":
        # Handle Mongo queries here
        # return data to jsonify method
        return jsonify(mongodata)

    elif request.method == "POST":
        post_data = request.json["key"]
        print(post_data)
        # Handle Mongo interactions here

    return "request handled"

if __name__ == "main":
    app.run(debug=True)