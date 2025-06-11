import json
import os
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd




SELECTIONS_JSON = "Website/user_selections.json"

RATINGS_FILE = "Website/user_ratings.json"


def load_user_ratings_for(username):
    all_ratings = load_user_ratings()  
    return [r for r in all_ratings if r['username'] == username]

def load_user_ratings():
    if not os.path.exists(RATINGS_FILE):
        return []
    with open(RATINGS_FILE, "r") as f:
        return json.load(f)

def save_user_ratings(ratings):
    with open(RATINGS_FILE, "w") as f:
        json.dump(ratings, f, indent=2)

def add_or_update_user_rating(username, appid, rating):
    ratings = load_user_ratings()

    # Check if user already rated this app
    for r in ratings:
        if r['username'] == username and r['appid'] == appid:
            r['rating'] = rating  # update rating
            break
    else:
        # If not found, append new rating
        ratings.append({
            "username": username,
            "appid": appid,
            "rating": rating
        })

    save_user_ratings(ratings)



def load_data(csv_path='Website/items.csv'):
    df = pd.read_csv(csv_path)
    df['Genres'] = df['Genres'].fillna('NAN')
    return df

def search_items(df, query):
    query = query.lower()
    return df[
        df['Name'].str.lower().str.contains(query) | 
        df['AppID'].astype(str).str.contains(query)
    ].to_dict(orient='records')


def save_user_selection_json(username, appids):
    if len(appids) != 5:
        return False

    data = {}
    if os.path.isfile(SELECTIONS_JSON):
        with open(SELECTIONS_JSON, "r") as f:
            data = json.load(f)

    data[username] = appids

    with open(SELECTIONS_JSON, "w") as f:
        json.dump(data, f, indent=4)

    return True

def load_user_selection_json(username):
    if os.path.isfile(SELECTIONS_JSON):
        with open(SELECTIONS_JSON, "r") as f:
            data = json.load(f)
        return data.get(username, [])
    return []

def calculate_rating_percent(row):
    try:
        positive = int(row.get('Positive', 0))
        negative = int(row.get('Negative', 0))
        total = positive + negative
        if total == 0:
            return 0.0
        return round((positive / total) * 100, 2)
    except:
        return 0.0
    

def get_top_by_rating(df, n=20):
    df = df.copy()
    df['RatingPercent'] = df.apply(lambda row: (
        round(100 * row['Positive'] / (row['Positive'] + row['Negative']))
        if row['Positive'] + row['Negative'] > 0 else 0
    ), axis=1)
    return df.sort_values(by='RatingPercent', ascending=False).head(n).to_dict(orient='records')

def get_top_overall(df, sort_by='owners', n=20):
    df = df.copy()
    if sort_by == 'rating':
        df['RatingPercent'] = df.apply(calculate_rating_percent, axis=1)
        return df.sort_values(by='RatingPercent', ascending=False).head(n).to_dict(orient='records')
    else:
        return df.sort_values(by='Estimated owners', ascending=False).head(n).to_dict(orient='records')




def get_top_genre_blocks(df, top_n_genres=10, top_n_games=20, sort_by='owners'):
    genre_df = df.copy()
    genre_df['Genres'] = genre_df['Genres'].str.split(',')
    genre_df = genre_df.explode('Genres')
    genre_df['Genres'] = genre_df['Genres'].str.strip()

    top_genres = (
        genre_df.groupby('Genres')['Estimated owners']
        .sum()
        .sort_values(ascending=False)
        .head(top_n_genres)
        .index.tolist()
    )

    genre_blocks = {}
    for genre in top_genres:
        filtered = genre_df[genre_df['Genres'] == genre].copy()

        if sort_by == 'rating':
            filtered['RatingPercent'] = filtered.apply(lambda row: (
                round(100 * row['Positive'] / (row['Positive'] + row['Negative']))
                if row['Positive'] + row['Negative'] > 0 else 0
            ), axis=1)
            top_games = filtered.sort_values(by='RatingPercent', ascending=False).head(top_n_games)
        else:
            top_games = filtered.sort_values(by='Estimated owners', ascending=False).head(top_n_games)

        genre_blocks[genre] = top_games.to_dict(orient='records')

    return genre_blocks

def get_personalized_blocks(df, user_selected_appids, top_n=10, top_n_games=20, sort_by='owners'):
    # Filter user's selected games from df
    user_games_df = df[df['AppID'].astype(str).isin(user_selected_appids)]

    if user_games_df.empty:
        return [], {}

    # Extract unique genres from user's games
    user_genres_list = []
    for genres_str in user_games_df['Genres'].fillna(''):
        user_genres_list.extend([g.strip() for g in genres_str.split(',') if g.strip()])
    user_genres_list = list(set(user_genres_list))

    all_genres = df['Genres'].fillna('').unique()

    vectorizer = TfidfVectorizer()
    all_genre_vectors = vectorizer.fit_transform(all_genres)

    user_genre_vectors = vectorizer.transform([' '.join(user_genres_list)])

    sim_scores = cosine_similarity(user_genre_vectors, all_genre_vectors).flatten()

    top_indices = sim_scores.argsort()[::-1][:top_n]

    top_similar_genres = [all_genres[i] for i in top_indices if all_genres[i].strip() != '']

    genre_blocks = {}
    for genre_str in top_similar_genres:
        filtered = df[df['Genres'].str.contains(genre_str, case=False, na=False)].copy()

        if sort_by == 'rating':
            filtered['RatingPercent'] = filtered.apply(lambda row: (
                round(100 * row['Positive'] / (row['Positive'] + row['Negative']))
                if row['Positive'] + row['Negative'] > 0 else 0), axis=1)
            top_games = filtered.sort_values(by='RatingPercent', ascending=False).head(top_n_games)
        else:
            top_games = filtered.sort_values(by='Estimated owners', ascending=False).head(top_n_games)

        genre_blocks[genre_str] = top_games.to_dict(orient='records')

    return [], genre_blocks



def get_personalized_blocks_with_ratings(df, user_ratings, top_n=10, top_n_games=20, sort_by='owners'):
    # user_ratings: list of dicts, e.g. [{'username': 'bob', 'appid': '123', 'rating': 5}, ...]

    rating_map = {str(r['appid']): r['rating'] for r in user_ratings}

    # Filter games that user rated
    rated_games_df = df[df['AppID'].astype(str).isin(rating_map.keys())]

    if rated_games_df.empty:
        return [], {}

    # Weighted genre scores accumulator
    genre_scores = defaultdict(float)

    # For each rated game, parse genres and add weighted score by rating
    for _, row in rated_games_df.iterrows():
        appid = str(row['AppID'])
        rating = rating_map.get(appid, 0)

        # Include all ratings, assign small weights to low ratings
        rating_weight_map = {1: 0.1, 2: 0.3, 3: 0.5, 4: 0.8, 5: 1.0}
        weight = rating_weight_map.get(int(round(rating)), 0.0)

        genres_str = row['Genres'] if pd.notnull(row['Genres']) else ''
        genres = [g.strip() for g in genres_str.split(',') if g.strip()]

        for genre in genres:
            genre_scores[genre] += weight

    if not genre_scores:
        return [], {}

    # Create weighted genre list (repeat genres by weighted score)
    weighted_genres = []
    for genre, score in genre_scores.items():
        repeat_count = max(1, int(score * 15))  # Adjust scale factor as needed
        weighted_genres.extend([genre] * repeat_count)

    all_genres = df['Genres'].fillna('').unique()
    vectorizer = TfidfVectorizer()
    all_genre_vectors = vectorizer.fit_transform(all_genres)

    user_genre_vector = vectorizer.transform([' '.join(weighted_genres)])
    sim_scores = cosine_similarity(user_genre_vector, all_genre_vectors).flatten()

    top_indices = sim_scores.argsort()[::-1][:top_n]
    top_similar_genres = [all_genres[i] for i in top_indices if all_genres[i].strip() != '']

    genre_blocks = {}
    for genre_str in top_similar_genres:
        filtered = df[df['Genres'].str.contains(genre_str, case=False, na=False)].copy()

        if sort_by == 'rating':
            filtered['RatingPercent'] = filtered.apply(
                lambda row: (
                    round(100 * row['Positive'] / (row['Positive'] + row['Negative']))
                    if row['Positive'] + row['Negative'] > 0 else 0
                ),
                axis=1
            )
            top_games = filtered.sort_values(by='RatingPercent', ascending=False).head(top_n_games)
        else:
            top_games = filtered.sort_values(by='Estimated owners', ascending=False).head(top_n_games)

        genre_blocks[genre_str] = top_games.to_dict(orient='records')

    return [], genre_blocks


def load_user_selections(username, path=SELECTIONS_JSON):
    if not os.path.isfile(path):
        return []
    with open(path, "r") as f:
        data = json.load(f)
    return data.get(username, [])



def get_items(path="Website/items.csv"):
    df = pd.read_csv(path)
    return df.to_dict(orient='records')  # returns list of dicts


# Function to load users from a file
def load_users(filename='users.json'):
    try:
        with open(filename, 'r') as file:
            users = json.load(file)
    except FileNotFoundError:
        users = {}
    return users

# Function to save users to a file
def save_users(users, filename='users.json'):
    with open(filename, 'w') as file:
        json.dump(users, file)













