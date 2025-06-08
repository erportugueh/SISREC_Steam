import json
import random


# Backend.py
import pandas as pd

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

def get_top_overall(df, n=20):
    return df.sort_values(by='Estimated owners', ascending=False).head(n).to_dict(orient='records')

def get_top_genre_blocks(df, top_n_genres=10, top_n_games=20):
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
        top_games = genre_df[genre_df['Genres'] == genre]\
            .sort_values(by='Estimated owners', ascending=False)\
            .head(top_n_games)
        genre_blocks[genre] = top_games.to_dict(orient='records')

    return genre_blocks




# Function to display the menu
def display_menu(logged_in):
    print("Menu:")
    if logged_in:
        print("1. Logout")
    else:
        print("1. Login")
        print("2. Register")
    print("3. See All Items")
    if logged_in:
        print("4. Rate an Item")
    print("5. Exit")

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

# Function to register a new user
def register_user(users):
    username = input("Enter a username: ")
    if username in users:
        print("Username already exists. Please choose a different username.")
    else:
        password = input("Enter a password: ")
        users[username] = password
        save_users(users)
        print("User registered successfully.")

# Function to login a user
def login_user(users):
    username = input("Enter your username: ")
    password = input("Enter your password: ")
    if username in users and users[username] == password:
        print("Login successful.")
        return True
    else:
        print("Invalid username or password.")
        return False

# Function to create items
def create_items():
    genres = ['fps', 'tps', 'sps']
    items = []
   
    item_id = 1
    for genre in genres:
        for i in range(10):
            item = {
                'name': f'{genre.upper()} Item {i+1}',
                'id': item_id,
                'genre': genre,
                'price': random.randint(10, 40),
                'valuation': random.randint(1, 5),
                'ratings': [],
                'description': f"This is the description of {genre.upper()} Item {i+1}."
            }
            items.append(item)
            item_id += 1
   
    return items

# Function to save items to a file
def save_items(items, filename='items.json'):
    with open(filename, 'w') as file:
        json.dump(items, file)

# Function to load items from a file
def load_items(filename='items.json'):
    try:
        with open(filename, 'r') as file:
            items = json.load(file)
    except FileNotFoundError:
        items = create_items()
        save_items(items)
    return items

# Function to create sample users with ratings for each item
def create_sample_users(items):
    sample_users = {
        "user1": "password1",
        "user2": "password2",
        "user3": "password3",
        "user4": "password4",
        "user5": "password5"
    }
   
    for user in sample_users.keys():
        for item in items:
            rating = random.randint(1, 5)
            item['ratings'].append(rating)
            item['valuation'] = sum(item['ratings']) / len(item['ratings'])
   
    return sample_users

# Function to display all items in categories and let the user select one to see the review and description
def display_items(items, user_genre_preference=None):
    def sort_items_by_valuation(items):
        return sorted(items, key=lambda x: x['valuation'], reverse=True)
   
    def filter_items_by_genre(items, genre):
        return [item for item in items if item['genre'] == genre]
   
    # Sort items by valuation
    sorted_items = sort_items_by_valuation(items)
   
    # Display best 10 rated items
    print("\nBest 10 Rated Items:")
    for idx, item in enumerate(sorted_items[:10]):
        print(f"{item['id']}. Name: {item['name']}, Genre: {item['genre']}, Valuation: {item['valuation']}")
   
    # Display items by genre with best rated ones first
    genres = ['fps', 'tps', 'sps']
   
    if user_genre_preference and user_genre_preference in genres:
        genres.remove(user_genre_preference)
        genres.insert(0, user_genre_preference)
   
    for genre in genres:
        genre_items = filter_items_by_genre(sorted_items, genre)
        print(f"\nBest Rated {genre.upper()} Items:")
        for item in genre_items:
            print(f"{item['id']}. Name: {item['name']}, Genre: {item['genre']}, Valuation: {item['valuation']}")
   
    choice = int(input("\nSelect an item by ID to see the review and description: "))
   
    selected_item = next((item for item in sorted_items if item['id'] == choice), None)
   
    if selected_item:
        print(f"\nSelected Item:\nName: {selected_item['name']}\nID: {selected_item['id']}\nGenre: {selected_item['genre']}\nPrice: {selected_item['price']} euros\nValuation: {selected_item['valuation']}\nDescription: {selected_item['description']}\nRatings: {selected_item['ratings']}")
    else:
        print("Invalid selection.")

# Function to rate an item
def rate_item(items):
    choice = int(input("Enter the ID of the item you want to rate: "))
   
    selected_item = next((item for item in items if item['id'] == choice), None)
   
    if selected_item:
        rating = int(input(f"Enter your rating for {selected_item['name']} (1-5): "))
       
        if 1 <= rating <= 5:
            selected_item['ratings'].append(rating)
            selected_item['valuation'] = sum(selected_item['ratings']) / len(selected_item['ratings'])
            save_items(items)  # Save updated items
            print(f"Rating added successfully. New valuation for {selected_item['name']} is {selected_item['valuation']:.2f}.")
            return selected_item['genre']
        else:
            print("Invalid rating. Please enter a value between 1 and 5.")
            return None
    else:
        print("Invalid selection.")
        return None

def main():
    users = load_users()
    items = load_items()
   
    # Create sample users with ratings for each item
    sample_users = create_sample_users(items)
   
    # Merge sample users with existing users
    users.update(sample_users)
   
    save_users(users)  # Save updated users
   
    logged_in = False
    user_genre_preference = None
   
    while True:
        display_menu(logged_in)
        choice = input("Enter your choice (1-5): ")
       
        if choice == '1':
            if logged_in:
                logged_in = False
                user_genre_preference = None
                print("Logged out successfully.")
            else:
                logged_in = login_user(users)
        elif choice == '2' and not logged_in:
            register_user(users)
            users = load_users()  # Reload users after registration
        elif choice == '3':
            display_items(items, user_genre_preference)
        elif choice == '4' and logged_in:
            user_genre_preference = rate_item(items)
        elif choice == '5':
            print("Exiting the program.")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()