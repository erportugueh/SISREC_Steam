from flask import Flask, render_template, request, abort
import pandas as pd
import os
from flask import session
from flask import redirect, url_for
from Backend import load_users, save_users, load_data, search_items, get_top_overall, get_top_genre_blocks

app = Flask(__name__)


app.secret_key = 'your-secret-key'  # Set a secure secret key for session encryption

basedir = os.path.abspath(os.path.dirname(__file__))
csv_path = os.path.join(basedir, "items.csv")
items_df = pd.read_csv(csv_path)


@app.route('/')
def home():
    query = request.args.get('q', '').strip()
    df = load_data()

    if query:
        search_results = search_items(df, query)
        return render_template(
            'home.html',
            query=query,
            search_results=search_results,
            top_overall=[],
            genre_blocks={}
        )

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



"""

@app.route("/retrieval/<int:item_id>")
def retrieval_page(item_id):
    match = items_df[items_df["id"] == item_id]
    if match.empty:
        abort(404)
    item = match.iloc[0].to_dict()

    related_items = items_df[items_df["id"] != item_id].sample(min(5, len(items_df)-1)).to_dict(orient="records")
    return render_template("retrieval.html", item=item, related_items=related_items)

"""
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

@app.route("/setup", methods=["GET", "POST"])
def setup():
    if 'username' not in session:
        return redirect(url_for('login'))  # protect this page

    items = ["Option 1", "Option 2", "Option 3", "Option 4", "Option 5",
             "Option 6", "Option 7", "Option 8"]  # example options

    if request.method == "POST":
        chosen = request.form.getlist('choices')  # get multiple selected values
        # Here you could save the choices to user data if you want
        # For now, just redirect home after submission
        return redirect(url_for('home'))

    return render_template("setup.html", items=items)


if __name__ == "__main__":
    app.run(debug=True)



