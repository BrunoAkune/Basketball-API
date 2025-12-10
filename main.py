"""
Los Angeles Lakers Dashboard - Main Application
================================================
This is the main file that runs the Lakers statistics dashboard.
It connects to the BallDontLie NBA API to get game data and displays
it in a beautiful dashboard with charts and statistics.
"""

# --- IMPORTS ---
# These are the tools/libraries we need to make everything work

from fastapi import FastAPI                    # The web framework that handles web requests
from fastapi.responses import HTMLResponse, FileResponse  # Lets us send back HTML pages
from fastapi.staticfiles import StaticFiles    # Serves static files like HTML, CSS, JS
import requests                                # Used to make HTTP calls to the NBA API
import uvicorn                                 # The server that runs our web app
import dash                                    # Dashboard framework (used elsewhere)
from dash import dcc, html                     # Dash components for building dashboards
import plotly.graph_objects as go              # Creates the interactive charts
from datetime import datetime, timedelta       # Handles dates and time calculations
import os                                      # Access to environment variables

# --- CREATE THE WEB APP ---
app = FastAPI()

# --- CONFIGURATION ---
# These are the settings for connecting to the NBA API

# API key for BallDontLie API (tries to get from environment, falls back to default)
API_KEY = os.environ.get("BALLDONTLIE_API_KEY", "593a23ee-fa08-44fc-bced-3c622004e575")
BASE_URL = "https://api.balldontlie.io/v1"     # The NBA API's web address
FIXED_TEAM_ID = 14                             # The Lakers' team ID in the API


# =============================================================================
# CACHING SYSTEM
# =============================================================================
# The NBA API has rate limits (it blocks you if you make too many requests).
# To avoid this, we save (cache) the data we get from the API for 5 minutes.
# This way, when you refresh the page, we use the saved data instead of
# asking the API again.

_cache = {}                                    # Dictionary to store our cached data
CACHE_DURATION = timedelta(minutes=5)          # How long to keep data before refreshing


def get_cached(key, allow_stale=False):
    """
    Try to get data from our cache.
    
    Parameters:
        key: The name/identifier of what we're looking for
        allow_stale: If True, return old data even if it's expired (useful when API fails)
    
    Returns:
        (data, is_fresh): The cached data and whether it's still fresh
    """
    if key in _cache:
        data, timestamp = _cache[key]
        # Check if the cached data is less than 5 minutes old
        is_fresh = datetime.now() - timestamp < CACHE_DURATION
        if is_fresh:
            print(f"Cache hit for {key}")
            return data, True
        elif allow_stale:
            # If API is down, we can still use old data
            print(f"Cache stale hit for {key} (fallback)")
            return data, False
    return None, False


def set_cache(key, data):
    """
    Save data to our cache with a timestamp.
    
    Parameters:
        key: The name to save the data under
        data: The actual data to save
    """
    _cache[key] = (data, datetime.now())


# =============================================================================
# API FUNCTIONS
# =============================================================================
# These functions talk to the BallDontLie API to get Lakers data


def get_fixed_team():
    """
    Get information about the Lakers team (name, city, abbreviation).
    
    This function:
    1. First checks if we have fresh cached data
    2. If not, asks the API for the data
    3. If the API fails, tries to use old cached data
    4. Saves successful responses to cache for next time
    
    Returns:
        A tuple of (team_name, team_city, team_abbreviation) or None if failed
    """
    cache_key = f"team_{FIXED_TEAM_ID}"
    cached, is_fresh = get_cached(cache_key)
    if cached is not None and is_fresh:
        return cached
    
    # Build the URL and headers for the API request
    url = f"{BASE_URL}/teams/{FIXED_TEAM_ID}"
    headers = {"Authorization": API_KEY}

    try:
        # Make the request to the API (with 10 second timeout)
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            # Something went wrong - try to use old cached data
            print("Error from balldontlie:", response.status_code, response.text)
            stale_data, _ = get_cached(cache_key, allow_stale=True)
            if stale_data:
                return stale_data
            return None

        # Extract the team info from the response
        data = response.json()["data"]
        team_name = data["name"]
        team_city = data["city"]
        team_abbreviation = data["abbreviation"]
        result = (team_name, team_city, team_abbreviation)
        
        # Save to cache for next time
        set_cache(cache_key, result)
        return result
        
    except Exception as e:
        # Network error or timeout - try to use old cached data
        print(f"Request failed: {e}")
        stale_data, _ = get_cached(cache_key, allow_stale=True)
        if stale_data:
            return stale_data
        return None


def get_team_games(team_id: int, season: int = 2024, per_page: int = 5):
    """
    Get a list of games for a team in a specific season.
    
    Parameters:
        team_id: The team's ID number (14 for Lakers)
        season: Which NBA season to get games for (e.g., 2024)
        per_page: How many games to fetch (max is usually 100)
    
    Returns:
        A list of game data dictionaries, or empty list if failed
    """
    cache_key = f"games_{team_id}_{season}_{per_page}"
    cached, is_fresh = get_cached(cache_key)
    if cached is not None and is_fresh:
        return cached
    
    url = f"{BASE_URL}/games"
    headers = {"Authorization": API_KEY}
    params = {
        "team_ids[]": team_id,      # Filter to just this team
        "seasons[]": season,         # Filter to this season
        "per_page": per_page         # How many results to return
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)

        # Print debug info to help with troubleshooting
        print("Games status:", response.status_code)
        print("Games URL:", response.url)

        if response.status_code != 200:
            # API error (often 429 = too many requests) - use old cached data
            print("Error from balldontlie (games):", response.status_code,
                  response.text)
            stale_data, _ = get_cached(cache_key, allow_stale=True)
            if stale_data:
                return stale_data
            return []

        # Get the games list from the response
        data = response.json().get("data", [])
        set_cache(cache_key, data)
        return data
        
    except Exception as e:
        print(f"Request failed: {e}")
        stale_data, _ = get_cached(cache_key, allow_stale=True)
        if stale_data:
            return stale_data
        return []


# =============================================================================
# WEB PAGES (ROUTES)
# =============================================================================
# These functions define what appears when you visit different URLs


@app.get("/")
def read_root():
    """
    The home page - serves the static index.html file.
    Visit: http://localhost:5000/
    """
    return FileResponse("static/index.html")


@app.get("/team", response_class=HTMLResponse)
def get_team_info():
    """
    The main Lakers dashboard page - shows team stats and charts.
    Visit: http://localhost:5000/team
    
    This page displays:
    - Team name and info
    - Win/Loss record
    - Average points scored
    - Line chart of scores over time
    - Bar chart of point differentials (wins/losses)
    """
    # Get team info from the API
    result = get_fixed_team()

    if result is None:
        return "<html><body><h1>Error: Could not find Lakers team data.</h1></body></html>"

    team_name, team_city, team_abbreviation = result
    
    # Get the last 25 games
    games = get_team_games(FIXED_TEAM_ID, season=2024, per_page=25)
    
    # If no games available, show a message
    if not games:
        chart_html = "<p>No game data available at this time.</p>"
        stats_html = ""
    else:
        # --- PROCESS THE GAME DATA ---
        # Create lists to hold all our data for the charts
        dates = []              # When each game was played
        lakers_scores = []      # Lakers' score in each game
        opponent_scores = []    # Opponent's score in each game
        opponents = []          # Who they played against
        point_diffs = []        # How much they won/lost by
        locations = []          # Home or Away
        
        # Loop through each game and extract the relevant info
        for g in games:
            # Convert the date string to a proper date object
            # (Replace "Z" timezone with proper format for Python)
            date_str = g["date"].replace("Z", "+00:00")
            date = datetime.fromisoformat(date_str)
            
            # Figure out if Lakers were home or away team
            if g["home_team"]["id"] == FIXED_TEAM_ID:
                # Lakers were the HOME team
                lakers_score = g["home_team_score"]
                opponent_score = g["visitor_team_score"]
                opponent_name = g["visitor_team"]["abbreviation"]
                location = "Home"
            else:
                # Lakers were the AWAY team
                lakers_score = g["visitor_team_score"]
                opponent_score = g["home_team_score"]
                opponent_name = g["home_team"]["abbreviation"]
                location = "Away"
            
            # Add this game's data to our lists
            dates.append(date)
            lakers_scores.append(lakers_score)
            opponent_scores.append(opponent_score)
            opponents.append(opponent_name)
            point_diffs.append(lakers_score - opponent_score)  # Positive = win
            locations.append(location)
        
        # --- CALCULATE STATISTICS ---
        total_wins = sum(1 for diff in point_diffs if diff > 0)    # Count positive diffs
        total_losses = len(point_diffs) - total_wins               # The rest are losses
        avg_lakers = sum(lakers_scores) / len(lakers_scores) if lakers_scores else 0
        avg_opponent = sum(opponent_scores) / len(opponent_scores) if opponent_scores else 0
        
        # --- CREATE CHART 1: Scores Over Time ---
        # This line chart shows how Lakers and opponents scored in each game
        scores_fig = go.Figure()
        
        # Purple line for Lakers scores
        scores_fig.add_trace(go.Scatter(
            x=dates, y=lakers_scores,
            mode='lines+markers',              # Show both lines and dots
            name='Lakers Score',
            line=dict(color='#552583', width=2),  # Lakers purple
            marker=dict(size=8)
        ))
        
        # Gold line for opponent scores
        scores_fig.add_trace(go.Scatter(
            x=dates, y=opponent_scores,
            mode='lines+markers',
            name='Opponent Score',
            line=dict(color='#FDB927', width=2),  # Lakers gold
            marker=dict(size=8)
        ))
        
        # Style the chart
        scores_fig.update_layout(
            title='Lakers vs Opponents - Game Scores Over Time',
            xaxis_title='Date',
            yaxis_title='Score',
            template='plotly_white',           # Clean white background
            hovermode='x unified'              # Show both values when hovering
        )
        
        # --- CREATE CHART 2: Win/Loss Point Differential ---
        # This bar chart shows how much they won or lost each game by
        # Purple bars = wins, Red bars = losses
        colors = ['#552583' if diff > 0 else '#DC143C' for diff in point_diffs]
        
        diff_fig = go.Figure()
        diff_fig.add_trace(go.Bar(
            x=dates,
            y=point_diffs,
            marker_color=colors,
            text=[f"vs {opp}" for opp in opponents],  # Show opponent on hover
            hovertemplate="<b>%{text}</b><br>Point Diff: %{y}<extra></extra>"
        ))
        
        diff_fig.update_layout(
            title='Win/Loss Point Differential (Purple = Win, Red = Loss)',
            xaxis_title='Date',
            yaxis_title='Point Differential',
            template='plotly_white'
        )
        
        # Add a horizontal line at 0 to clearly show wins vs losses
        diff_fig.add_hline(y=0, line_dash="dash", line_color="gray")
        
        # Convert charts to HTML that can be embedded in the page
        chart_html = scores_fig.to_html(full_html=False) + diff_fig.to_html(full_html=False)
        
        # --- CREATE STATS CARDS ---
        # These are the four boxes showing key statistics
        stats_html = f"""
        <div style="display: flex; justify-content: center; gap: 20px; margin: 20px 0;">
            <div style="text-align: center; padding: 20px; background: #f8f9fa; border-radius: 10px; min-width: 120px;">
                <h3 style="color: #552583; font-size: 36px; margin: 0;">{total_wins}</h3>
                <p style="margin: 0;">Wins</p>
            </div>
            <div style="text-align: center; padding: 20px; background: #f8f9fa; border-radius: 10px; min-width: 120px;">
                <h3 style="color: #DC143C; font-size: 36px; margin: 0;">{total_losses}</h3>
                <p style="margin: 0;">Losses</p>
            </div>
            <div style="text-align: center; padding: 20px; background: #f8f9fa; border-radius: 10px; min-width: 120px;">
                <h3 style="color: #552583; font-size: 36px; margin: 0;">{avg_lakers:.1f}</h3>
                <p style="margin: 0;">Avg Points</p>
            </div>
            <div style="text-align: center; padding: 20px; background: #f8f9fa; border-radius: 10px; min-width: 120px;">
                <h3 style="color: #FDB927; font-size: 36px; margin: 0;">{avg_opponent:.1f}</h3>
                <p style="margin: 0;">Opp Avg Points</p>
            </div>
        </div>
        """
    
    # --- BUILD THE FULL HTML PAGE ---
    # Combines the header, stats, charts, and footer into one page
    return f"""
    <html>
    <head>
        <title>Los Angeles Lakers Dashboard</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background: #fff; }}
            .header {{ background: #FDB927; padding: 20px; text-align: center; }}
            .header h1 {{ color: #552583; margin: 0 0 10px 0; }}
            .header p {{ color: #666; margin: 0; font-size: 18px; }}
            .content {{ padding: 20px; }}
            .team-info {{ text-align: center; margin: 20px 0; color: #333; }}
            .footer {{ text-align: center; color: #666; padding: 20px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Los Angeles Lakers Dashboard</h1>
            <p>2024 Season Statistics</p>
        </div>
        <div class="team-info">
            <p><strong>{team_city} {team_name}</strong> ({team_abbreviation})</p>
        </div>
        {stats_html}
        <div class="content">
            {chart_html}
        </div>
        <div class="footer">
            <p>Data provided by Ball Don't Lie API</p>
            <a href="/">Back to Home</a>
        </div>
    </body>
    </html>
    """


# =============================================================================
# LEGACY CHART ENDPOINT
# =============================================================================
# This is an older, simpler chart endpoint. The /team page above is the main one.

# Get some games for the basic chart
games_sample = get_team_games(FIXED_TEAM_ID, season=2024)
LAL_TEAM_ID = 14

# Transform the games into lists for the chart
dates = []
lakers_scores = []
opponent_scores = []
opponents = []

for g in games_sample:
    date = datetime.fromisoformat(g["date"])
    if g["home_team"]["id"] == LAL_TEAM_ID:
        lakers_scores.append(g["home_team_score"])
        opponent_scores.append(g["visitor_team_score"])
        opponents.append(g["visitor_team"]["abbreviation"])
    else:
        lakers_scores.append(g["visitor_team_score"])
        opponent_scores.append(g["home_team_score"])
        opponents.append(g["home_team"]["abbreviation"])
        dates.append(date)

# Build a simple Plotly figure
fig = go.Figure()
fig.add_trace(
    go.Scatter(x=dates,
               y=lakers_scores,
               mode="lines+markers",
               name="Lakers points"))
fig.add_trace(
    go.Scatter(x=dates,
               y=opponent_scores,
               mode="lines+markers",
               name="Opponent points"))

fig.update_layout(title="Lakers vs. Opponents",
                  xaxis_title="Date",
                  yaxis_title="Points",
                  legend_title="Legend")


@app.get("/chart", response_class=HTMLResponse)
def show_chart():
    """
    Simple chart page - shows just a basic score comparison chart.
    Visit: http://localhost:5000/chart
    """
    html_fig = fig.to_html(full_html=False)
    return f"""
    <html>
    <head>
    <title>Lakers Chart</title>
    </head>
    <body>
    <h1>Lakers Game Scores</h1>
    {html_fig}
    </body>
    </html>
    """


# =============================================================================
# RUN THE APP
# =============================================================================
# This only runs if you execute main.py directly (not when imported)
    
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
