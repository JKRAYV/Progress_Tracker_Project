from flask import Flask, jsonify, request, render_template, redirect, session
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
import os
import re

app = Flask(__name__)

try:
    app = Flask(__name__)
    app.config["MONGO_URI"] = "mongodb://localhost:27017/progress_tracker"
    mongo = PyMongo(app)
except:
        print("ERROR- cannot connect to db")

@app.route('/', methods=["GET", "POST"])
def login():
    app.secret_key = os.urandom(24) # establishes session secret key
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = mongo.db.Users.find_one({"Username": username})

        if user and user["Password"] == password:
            session['username'] = username #stores session username
            # Successful login
            return redirect("/dashboard")

        # Invalid credentials
        error = "Invalid username or password"
        return render_template("login.html", error=error)

    return render_template("login.html")

@app.route('/register', methods=["GET", "POST"])
def register():
    app.secret_key = os.urandom(24)
    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        existing_user = mongo.db.Users.find_one({"Username": username})
        existing_email = mongo.db.Users.find_one({"Email": email})

        if existing_user:
            error = "Username already taken. Please choose a different username."
            return render_template("register.html", error=error)
        elif existing_email:
            error = "Email already in use. Please choose a different email."
            return render_template("register.html", error=error)
            

        # Insert the user into the database
        new_user = {
            "Fname": first_name,
            "Lname": last_name,
            "Username": username,
            "Password": password,
            "Profile image": "user_bright.png",
            "Email":email,
            "Role": "user",
            "Shows_Watched" : []
        }
        mongo.db.Users.insert_one(new_user)

        session['username'] = username
        return redirect("/dashboard")

    return render_template("register.html")

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

@app.route('/dashboard', methods=["GET","POST","PUT"])
def dashboard():
    if 'username' in session:
        logged_in_username = session['username'] #current user logged in

        user_data = mongo.db.Users.find_one({"Username": logged_in_username}) #finds instance of user
        
        tv_shows = list(mongo.db.TV.find())  # Retrieve all TV shows from the TV collection

        # Handle regex search for available shows
        regex_pattern = request.form.get("regex_pattern")
        if regex_pattern:
            try:
                tv_shows = [show for show in tv_shows if re.search(regex_pattern, show["Title"])]
            except re.error:
                error = "Invalid regex pattern"
                return render_template("dashboard.html", user_data=user_data, available_shows=tv_shows, error=error)

        if user_data:
            #-------------------------Updates Status of shows-------------------------
            for show in user_data["Shows_Watched"]:
                for tv_show in tv_shows:
                    if tv_show["Title"] == show["Name"]:
                        num_episodes = tv_show["Number_of_Episodes"]
                        if show["Episodes"] == 0:
                            show["Status"] = "plan to watch"
                        elif 0 < show["Episodes"] < num_episodes:
                            show["Status"] = "watching"
                        elif show["Episodes"] == num_episodes or show["Episodes"] > num_episodes:
                            show["Status"] = "completed"
                            show["Episodes"] = num_episodes
                        break  # No need to continue searching for matching TV shows

            # Update user data in MongoDB
            mongo.db.Users.update_one({"Username": logged_in_username}, {"$set": {"Shows_Watched": user_data["Shows_Watched"]}})
            #--------------------------------------------------------------------------

            #Finds all shows that user is currently not engaged with. Needed for selecting new shows to watch.
            available_shows = [show for show in tv_shows if show["Title"] not in [user_show["Name"] for user_show in user_data["Shows_Watched"]]]

            # Render the dashboard template with the updated data
            return render_template('dashboard.html', user_data=user_data, available_shows = available_shows)
        else:
            error = "User not found"
            return render_template('dashboard.html', error=error)
    else:
        error = "Please log in before accessing this data."
        return redirect("/")

@app.route('/edit_profile', methods=["GET", "POST"])
def edit_profile():
    if 'username' not in session:
        return redirect('/')
    
    # Fetch user data from the database
    user_data = mongo.db.Users.find_one({"Username": session['username']})

    # If POST request, update the user's profile
    if request.method == "POST":
        new_username = request.form.get("username")
        selected_avatar = request.form.get("avatar")
        
        # Check if the new username is already taken by another user
        existing_user = mongo.db.Users.find_one({"Username": new_username})
        if existing_user and existing_user["Username"] != session['username']:
            error = "Username already taken. Please choose a different username."
            avatars = os.listdir('static/profileimages')
            return render_template('edit_profile.html', user_data=user_data, avatars=avatars, error=error)
        
        # Update the database with the new username and avatar
        mongo.db.Users.update_one({"Username": session['username']}, {"$set": {"Username": new_username, "Profile image": selected_avatar}})
        
        # Update the session username
        session['username'] = new_username

        return redirect('/dashboard')

    # If GET request, display the edit profile page
    avatars = os.listdir('static/profileimages')  # List all avatars from the given directory
    return render_template('edit_profile.html', user_data=user_data, avatars=avatars)

@app.route('/add_show/<show_title>')
def add_show(show_title):
    if 'username' in session:
        logged_in_username = session['username']

        user_data = mongo.db.Users.find_one({"Username": logged_in_username})
        if user_data:
            # Retrieve the selected TV show based on the show_title
            selected_show = mongo.db.TV.find_one({"Title": show_title})

            if selected_show:
                # Add the show to the user's Shows_Watched array
                new_show = {
                    "Name": selected_show["Title"],
                    "Status": "plan to watch",
                    "Episodes": 0
                }
                user_data["Shows_Watched"].append(new_show)
                mongo.db.Users.update_one({"Username": logged_in_username}, {"$set": user_data})

                # Redirect back to the dashboard after adding the show
                return redirect("/dashboard")

    # If something goes wrong, return to the dashboard with an error
    error = "Failed to add show"
    return redirect("/dashboard?error=" + error)

@app.route('/advance_episode/<show_title>', methods=["POST"])
def advance_episode(show_title):
    if 'username' in session:
        logged_in_username = session['username']

        user_data = mongo.db.Users.find_one({"Username": logged_in_username})
        if user_data:
            # Find the user's show by its title
            user_show = next((show for show in user_data["Shows_Watched"] if show["Name"] == show_title), None)

            if user_show and user_show["Status"] == "watching" or user_show and user_show["Status"] == "plan to watch":
                # Fetch total episodes from the TV table
                tv_show = mongo.db.TV.find_one({"Title": show_title})
                total_episodes = tv_show["Number_of_Episodes"]
                user_show["Status"] = "watching"

                # Check if advancing the episode will complete the show
                if user_show["Episodes"] + 1 == total_episodes or user_show["Episodes"] + 1 > total_episodes:
                    user_show["Episodes"] = total_episodes
                    user_show["Status"] = "completed"

                else:
                    user_show["Episodes"] += 1

                # Update the user's data in the database
                mongo.db.Users.update_one({"Username": logged_in_username}, {"$set": user_data})

                # Calculate the completion percentage
                completion_percentage = (user_show["Episodes"] / total_episodes) * 100 if total_episodes else 0



                return jsonify({
                                    "completion_percentage": completion_percentage,
                                    "current_episode": user_show["Episodes"],
                                    "status": user_show["Status"]
                                })

    error = "Error advancing episode"
    return redirect("/dashboard?error=" + error)

@app.route('/show_details/<show_title>')
def show_details(show_title):
    if 'username' in session:
        logged_in_username = session['username']

        user_data = mongo.db.Users.find_one({"Username": logged_in_username})
        if user_data:
            user_show = next((show for show in user_data["Shows_Watched"] if show["Name"] == show_title), None)
            if user_show:
                show = mongo.db.TV.find_one({"Title": show_title})

                # Calculates the percentage watched
                total_episodes = show["Number_of_Episodes"]
                completion_percentage = (user_show["Episodes"] / total_episodes) * 100


                return render_template('show_details.html', show=show, user_show=user_show, completion_percentage=completion_percentage)

    error = "Show details not found"
    return redirect("/dashboard?error=" + error)

@app.route('/restart_show/<show_title>', methods=["POST"])
def restart_show(show_title):
    if 'username' in session:
        logged_in_username = session['username']

        user_data = mongo.db.Users.find_one({"Username": logged_in_username})
        if user_data:
            user_show = next((show for show in user_data["Shows_Watched"] if show["Name"] == show_title), None)

            if user_show and user_show["Status"] == "completed":
                # Set status to "watching" and reset episodes to 0
                user_show["Status"] = "watching"
                user_show["Episodes"] = 0

                # Update the user's data in the database
                mongo.db.Users.update_one({"Username": logged_in_username}, {"$set": user_data})

                return redirect("/show_details/" + show_title)

    error = "Error restarting show"
    return redirect("/dashboard?error=" + error)

@app.route('/remove_show/<show_title>', methods=["GET","POST"])
def remove_show(show_title):
    if 'username' in session:
        logged_in_username = session['username']

        user_data = mongo.db.Users.find_one({"Username": logged_in_username})
        if user_data:
            user_show = next((show for show in user_data["Shows_Watched"] if show["Name"] == show_title), None)

            if user_show and user_show["Status"] == "completed":
                # Remove the show from the user's watched shows
                user_data["Shows_Watched"] = [show for show in user_data["Shows_Watched"] if show["Name"] != show_title]

                # Update the user's data in the database
                mongo.db.Users.update_one({"Username": logged_in_username}, {"$set": user_data})

                return redirect("/dashboard")

    error = "Error removing show"
    return redirect("/dashboard?error=" + error)

if __name__ == "__main__":
    app.run(debug=True)
