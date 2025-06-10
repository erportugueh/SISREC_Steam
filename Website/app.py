from flask import Flask, render_template, request, abort
import pandas as pd
import os
from flask import session, flash
from flask import redirect, url_for
from Backend import load_users, save_users, load_data, get_top_by_rating,  get_personalized_blocks_with_ratings, load_user_ratings_for, get_top_overall, add_or_update_user_rating, get_top_genre_blocks,  get_items, save_user_selection_json, load_user_selection_json, get_personalized_blocks, load_user_selections

app = Flask(__name__)


app.secret_key = 'your-secret-key'  # Set a secure secret key for session encryption

basedir = os.path.abspath(os.path.dirname(__file__))
csv_path = os.path.join(basedir, "items.csv")
items_df = pd.read_csv(csv_path)

@app.route('/')
def home():
    username = session.get('username')
    query = request.args.get('q', '').strip()
    filter_option = request.args.get('filter', 'owners')
    df = load_data()

    df['RatingPercent'] = df.apply(lambda row: (
        round(100 * row['Positive'] / (row['Positive'] + row['Negative']))
        if row['Positive'] + row['Negative'] > 0 else 0
    ), axis=1)

    user_selected_appids = []
    user_ratings = []

    search_results = []
    if query:
        search_results = df[df['AppID'].str.contains(query, case=False, na=False)].to_dict(orient='records')
        sort_key = 'RatingPercent' if filter_option == 'rating' else 'Estimated owners'
        search_results.sort(key=lambda x: x.get(sort_key, 0), reverse=True)

        top_overall = []
        genre_blocks = {}
    else:
        if username:
            user_selected_appids = load_user_selections(username)
            user_ratings = load_user_ratings_for(username)

        if username and user_ratings:
            _, genre_blocks = get_personalized_blocks_with_ratings(df, user_ratings, sort_by=filter_option)
            top_overall = []
        elif user_selected_appids:
            _, genre_blocks = get_personalized_blocks(df, user_selected_appids, sort_by=filter_option)
            top_overall = []
        else:
            top_overall = get_top_overall(df) if filter_option == 'owners' else get_top_by_rating(df)
            genre_blocks = get_top_genre_blocks(df, sort_by=filter_option)

    user_appids_to_exclude = set(user_selected_appids) | set(str(r['appid']) for r in user_ratings)

    top_overall = [item for item in top_overall if str(item['AppID']) not in user_appids_to_exclude]
    for genre, games in genre_blocks.items():
        genre_blocks[genre] = [game for game in games if str(game['AppID']) not in user_appids_to_exclude]

    return render_template(
        'home.html',
        query=query,
        filter=filter_option,
        search_results=search_results,
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



