"""
NBA API Service - Lakers Game Data
===================================
This file contains helper functions for fetching and processing
Lakers game data from the BallDontLie NBA API.

The main function is get_lakers_games() which:
1. Fetches raw game data from the API
2. Processes it to make it easier to use
3. Figures out if Lakers won or lost each game
4. Returns a clean list of game dictionaries
"""

import requests  # Library for making HTTP requests to APIs
import os        # Access to environment variables

# --- API CONFIGURATION ---
# Get the API key from environment variable, with a fallback default
API_KEY = os.environ.get("BALLDONTLIE_API_KEY", "593a23ee-fa08-44fc-bced-3c622004e575")
BASE_URL = "https://api.balldontlie.io/v1"        # Base URL for the API
LAKERS_TEAM_ID = 14                                # Lakers' team ID in the API


def get_lakers_games(season: int = 2023, per_page: int = 25):
    """
    Fetches and processes Lakers games for a specific season.
    
    Parameters:
        season: Which NBA season to get games for (e.g., 2023, 2024)
        per_page: How many games to fetch (max is usually 100)
    
    Returns:
        A list of processed game dictionaries, each containing:
        - date: When the game was played
        - lakers_score: How many points Lakers scored
        - opponent_score: How many points the opponent scored
        - opponent: Name of the opposing team
        - location: "Home" or "Away"
        - won: True if Lakers won, False if they lost
        - point_diff: Lakers score minus opponent score
        - status: Game status (e.g., "Final")
    
    Example:
        games = get_lakers_games(season=2024, per_page=10)
        for game in games:
            print(f"{game['date']}: Lakers {game['lakers_score']} - {game['opponent']} {game['opponent_score']}")
    """
    # Build the API request URL and parameters
    url = f"{BASE_URL}/games"
    headers = {"Authorization": API_KEY}
    params = {
        "team_ids[]": LAKERS_TEAM_ID,   # Filter to only Lakers games
        "seasons[]": season,             # Filter to specific season
        "per_page": per_page             # How many results to return
    }
    
    # Make the API request
    response = requests.get(url, headers=headers, params=params)
    
    # Check if the request was successful
    if response.status_code != 200:
        print("Error fetching games:", response.status_code, response.text)
        return []
    
    # Extract the games list from the response
    games = response.json().get("data", [])
    
    # --- PROCESS EACH GAME ---
    # The raw API data needs to be transformed because:
    # 1. Lakers could be either home or visitor team
    # 2. We want consistent field names regardless of location
    # 3. We want to calculate if they won and by how much
    
    processed_games = []
    
    for game in games:
        # Get the teams and scores from the raw data
        home_team = game.get("home_team", {})
        visitor_team = game.get("visitor_team", {})
        home_score = game.get("home_team_score", 0)
        visitor_score = game.get("visitor_team_score", 0)
        
        # Figure out if Lakers were the home or visitor team
        is_lakers_home = home_team.get("id") == LAKERS_TEAM_ID
        
        if is_lakers_home:
            # Lakers were playing at home
            lakers_score = home_score
            opponent_score = visitor_score
            opponent_name = visitor_team.get("full_name", "Unknown")
            location = "Home"
        else:
            # Lakers were playing away
            lakers_score = visitor_score
            opponent_score = home_score
            opponent_name = home_team.get("full_name", "Unknown")
            location = "Away"
        
        # Calculate win/loss and point difference
        won = lakers_score > opponent_score              # True if Lakers scored more
        point_diff = lakers_score - opponent_score       # Positive = win, Negative = loss
        
        # Add the processed game to our list
        processed_games.append({
            "date": game.get("date", ""),
            "lakers_score": lakers_score,
            "opponent_score": opponent_score,
            "opponent": opponent_name,
            "location": location,
            "won": won,
            "point_diff": point_diff,
            "status": game.get("status", "")
        })
    
    # Sort games by date (oldest to newest)
    processed_games.sort(key=lambda x: x["date"])
    
    return processed_games
