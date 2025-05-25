from flask import Flask, render_template, request, abort
import pandas as pd
import os

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
csv_path = os.path.join(basedir, "items.csv")

try:
    items_df = pd.read_csv(csv_path)
except FileNotFoundError:
    print(f"Error: Could not find items.csv at {csv_path}")
    items_df = pd.DataFrame(columns=["id", "name", "description", "price"])


@app.route("/")
def home():
    query = request.args.get("q", "")
    filtered_items = items_df[items_df["name"].str.contains(query, case=False, na=False)] if query else items_df
    return render_template("home.html", items=filtered_items.to_dict(orient="records"), query=query)


@app.route("/item/<int:item_id>")
def item_page(item_id):
    match = items_df[items_df["id"] == item_id]
    if match.empty:
        abort(404)
    item = match.iloc[0].to_dict()
    return render_template("item.html", item=item)


@app.route("/retrieval/<int:item_id>")
def retrieval_page(item_id):
    match = items_df[items_df["id"] == item_id]
    if match.empty:
        abort(404)
    item = match.iloc[0].to_dict()

    related_items = items_df[items_df["id"] != item_id].sample(min(5, len(items_df)-1)).to_dict(orient="records")
    return render_template("retrieval.html", item=item, related_items=related_items)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Placeholder: You would verify user credentials here
        username = request.form["username"]
        password = request.form["password"]
        return f"Login attempted by {username}"
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Placeholder: You would create a new user here
        username = request.form["username"]
        password = request.form["password"]
        confirm = request.form["confirm"]
        return f"Registered user: {username}"
    return render_template("register.html")


if __name__ == "__main__":
    app.run(debug=True)
