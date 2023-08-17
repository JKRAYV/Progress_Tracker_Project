from flask import Flask, jsonify, request, render_template, redirect
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt

app = Flask(__name__)

bcrypt = Bcrypt(app)

try: 
    app = Flask(__name__)
    app.config["MONGO_URI"] = "mongodb://localhost:27017/progress_tracker"
    mongo = PyMongo(app) 
except: 
        print("ERROR- cannot connect to db")

@app.route('/', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = mongo.db.Users.find_one({"Username": username})

        if user and user["Password"] == password:
            # Successful login
            return redirect("/dashboard")

        # Invalid credentials
        error = "Invalid username or password"
        return render_template("login.html", error=error)

    return render_template("login.html")

@app.route("/users", methods=["GET","POST"])
def get_users():
    if request.method == "GET":
        users = list(mongo.db.Users.find())
        for user in users:
            user["_id"] = str(user["_id"])  # Convert ObjectId to string for JSON serialization    
        return render_template("./users.html", users=users)

    elif request.method == "POST":
        post_data = request.json
        # Assuming post_data is a dictionary containing user details
        new_user_id = mongo.db.users.insert_one(post_data).inserted_id
        return jsonify(str(new_user_id)), 201  # Return the new user's ID and HTTP status code 201 (Created)

    return "request handled"

@app.route("/tvshows", methods=["GET","POST"])
def get_tvshows():
    if request.method == "GET":
        tv = list(mongo.db.TV.find())
        for show in tv:
            show["_id"] = str(show["_id"])  # Convert ObjectId to string for JSON serialization    
        return render_template("./tv.html", tv=tv)

    elif request.method == "POST":
        post_data = request.json["key"]
        print(post_data)
        # Handle Mongo interactions here

    return "request handled"

if __name__ == "__main__":
    app.run(debug=True)