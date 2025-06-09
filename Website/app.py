from flask import Flask, render_template, request, abort
import pandas as pd
import os
from flask import session, flash
from flask import redirect, url_for
from Backend import load_users, save_users, load_data, get_personalized_blocks_with_ratings, load_user_ratings_for, get_top_overall, add_or_update_user_rating, get_top_genre_blocks,  get_items, save_user_selection_json, load_user_selection_json, get_personalized_blocks, load_user_selections

app = Flask(__name__)


app.secret_key = 'your-secret-key'  # Set a secure secret key for session encryption

basedir = os.path.abspath(os.path.dirname(__file__))
csv_path = os.path.join(basedir, "items.csv")
items_df = pd.read_csv(csv_path)

@app.route('/')
def home():
    username = session.get('username')
    df = load_data()

    if username:
        # Load user selections and ratings
        user_selected_appids = load_user_selections(username)  # List of appids user selected/liked
        user_ratings = load_user_ratings_for(username)  # List of dicts {'appid':..., 'rating':...}
    else:
        user_selected_appids = []
        user_ratings = []

    if username and user_ratings:
        # Use the personalized blocks that consider ratings
        top_overall, genre_blocks = get_personalized_blocks_with_ratings(df, user_ratings)
    elif user_selected_appids:
        # Use personalized blocks based on selections (old behavior)
        top_overall, genre_blocks = get_personalized_blocks(df, user_selected_appids)
    else:
        top_overall = get_top_overall(df)
        genre_blocks = get_top_genre_blocks(df)

    return render_template(
        'home.html',
        query='',
        search_results=[],
        top_overall=top_overall,
        genre_blocks=genre_blocks
    )


@app.route("/item/<appid>")
def item_page(appid):
    # appid is now a string
    match = items_df[items_df["AppID"].astype(str) == appid]
    if match.empty:
        abort(404)
    item = match.iloc[0].to_dict()
    return render_template("item.html", item=item)



@app.route("/submit_review/<appid>", methods=["POST"])
def submit_review(appid):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    rating = request.form.get('rating')
    if not rating or not rating.isdigit() or int(rating) not in range(1, 6):
        flash("Please provide a valid rating between 1 and 5.")
        return redirect(url_for('item_page', appid=appid))

    add_or_update_user_rating(session['username'], appid, int(rating))
    flash("Your rating has been saved!")
    return redirect(url_for('item_page', appid=appid))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        users = load_users()

        if username in users and users[username] == password:
            session['username'] = username
            return redirect(url_for("home"))
        else:
            return "Invalid username or password.", 401

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("home"))

from flask import session, redirect, url_for

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm = request.form["confirm"]

        users = load_users()

        if username in users:
            message = "Username already exists. Please choose a different username."
            return render_template("register.html", message=message)
        elif password != confirm:
            message = "Passwords do not match."
            return render_template("register.html", message=message)
        else:
            users[username] = password
            save_users(users)
            session['username'] = username  # log them in or store for setup
            return redirect(url_for('setup'))

    return render_template("register.html")

from Backend import save_user_selection_json
from flask import flash

@app.route("/setup", methods=["GET", "POST"])
def setup():
    if 'username' not in session:
        return redirect(url_for('login'))

    items = get_items()

    if request.method == "POST":
        selected = request.form.getlist('choices')
        if len(selected) != 5:
            flash("Please select exactly 5 games.")
            return render_template("setup.html", items=items, selected=selected)
        else:
            save_user_selection_json(session['username'], selected)
            return redirect(url_for('home'))

    # For GET requests, try to load previous selections to keep them checked on reload
    user_selections = load_user_selection_json(session['username'])
    return render_template("setup.html", items=items, selected=user_selections)




if __name__ == "__main__":
    app.run(debug=True)



