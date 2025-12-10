"""
Lakers Dashboard - Dash Application
====================================
This file creates an alternative dashboard using the Dash framework.
Dash is great for building interactive web dashboards with Python.

This dashboard shows:
- Win/Loss statistics
- Score comparisons over time
- Home vs Away performance
- Point differential charts

Visit: http://localhost:5000/dash/
"""

# --- IMPORTS ---
from dash import Dash, html, dcc              # Dash framework for building dashboards
import plotly.graph_objects as go              # Creates interactive charts
import plotly.express as px                    # Simpler chart creation (not used but available)
from services.nba import get_lakers_games      # Our function to get Lakers game data


def create_dash_app():
    """
    Creates and configures the Dash application.
    
    This function:
    1. Creates a new Dash app
    2. Fetches Lakers game data from the NBA API
    3. Processes the data for visualization
    4. Creates multiple charts (scores, point diff, home/away)
    5. Assembles everything into a complete dashboard layout
    
    Returns:
        A configured Dash application ready to be served
    """
    # Create the Dash app
    # requests_pathname_prefix tells Dash it will be served at /dash/
    dash_app = Dash(__name__, requests_pathname_prefix="/dash/")
    
    # --- FETCH DATA ---
    # Get 50 games from the 2023 season
    games = get_lakers_games(season=2023, per_page=50)
    
    # If we couldn't get any games, show an error message
    if not games:
        dash_app.layout = html.Div([
            html.H1("Lakers Dashboard"),
            html.P("No game data available. Please check API connection.")
        ])
        return dash_app
    
    # --- EXTRACT DATA FROM GAMES ---
    # Pull out the specific fields we need for our charts
    dates = [g["date"] for g in games]                    # Game dates
    lakers_scores = [g["lakers_score"] for g in games]    # Lakers' scores
    opponent_scores = [g["opponent_score"] for g in games] # Opponents' scores
    opponents = [g["opponent"] for g in games]            # Opponent team names
    point_diffs = [g["point_diff"] for g in games]        # Point differences
    locations = [g["location"] for g in games]            # Home or Away
    wins = [g["won"] for g in games]                      # True/False for each game
    
    # =========================================================================
    # CHART 1: Scores Over Time
    # =========================================================================
    # This line chart compares Lakers and opponent scores across all games
    
    scores_fig = go.Figure()
    
    # Add Lakers score line (purple)
    scores_fig.add_trace(go.Scatter(
        x=dates, y=lakers_scores,
        mode='lines+markers',                  # Show both line and dots
        name='Lakers Score',
        line=dict(color='#552583', width=2),   # Lakers purple color
        marker=dict(size=8)                    # Size of the dots
    ))
    
    # Add opponent score line (gold)
    scores_fig.add_trace(go.Scatter(
        x=dates, y=opponent_scores,
        mode='lines+markers',
        name='Opponent Score',
        line=dict(color='#FDB927', width=2),   # Lakers gold color
        marker=dict(size=8)
    ))
    
    # Configure the chart layout
    scores_fig.update_layout(
        title='Lakers vs Opponents - Game Scores Over Time',
        xaxis_title='Date',
        yaxis_title='Score',
        template='plotly_white',               # Clean white background
        hovermode='x unified'                  # Show all values when hovering on a date
    )
    
    # =========================================================================
    # CHART 2: Point Differential (Win/Loss Bars)
    # =========================================================================
    # Bar chart showing how much Lakers won or lost by in each game
    # Purple bars = wins, Red bars = losses
    
    # Choose color based on whether they won (positive diff) or lost (negative)
    colors = ['#552583' if diff > 0 else '#DC143C' for diff in point_diffs]
    
    diff_fig = go.Figure()
    diff_fig.add_trace(go.Bar(
        x=dates,
        y=point_diffs,
        marker_color=colors,
        text=[f"vs {opp}" for opp in opponents],  # Show opponent name on hover
        hovertemplate="<b>%{text}</b><br>Point Diff: %{y}<extra></extra>"
    ))
    
    diff_fig.update_layout(
        title='Win/Loss Point Differential (Purple = Win, Red = Loss)',
        xaxis_title='Date',
        yaxis_title='Point Differential',
        template='plotly_white'
    )
    
    # Add a horizontal line at 0 to clearly separate wins from losses
    diff_fig.add_hline(y=0, line_dash="dash", line_color="gray")
    
    # =========================================================================
    # CHART 3: Home vs Away Performance
    # =========================================================================
    # Grouped bar chart comparing wins and losses at home vs on the road
    
    # Separate games by location
    home_games = [g for g in games if g["location"] == "Home"]
    away_games = [g for g in games if g["location"] == "Away"]
    
    # Count wins and losses for each location
    home_wins = sum(1 for g in home_games if g["won"])
    home_losses = len(home_games) - home_wins
    away_wins = sum(1 for g in away_games if g["won"])
    away_losses = len(away_games) - away_wins
    
    location_fig = go.Figure()
    
    # Add wins bars (purple)
    location_fig.add_trace(go.Bar(
        name='Wins',
        x=['Home', 'Away'],
        y=[home_wins, away_wins],
        marker_color='#552583'                 # Lakers purple
    ))
    
    # Add losses bars (gold)
    location_fig.add_trace(go.Bar(
        name='Losses',
        x=['Home', 'Away'],
        y=[home_losses, away_losses],
        marker_color='#FDB927'                 # Lakers gold
    ))
    
    location_fig.update_layout(
        title='Home vs Away Performance',
        xaxis_title='Location',
        yaxis_title='Games',
        barmode='group',                       # Put bars side by side
        template='plotly_white'
    )
    
    # =========================================================================
    # CALCULATE SUMMARY STATISTICS
    # =========================================================================
    
    total_wins = sum(1 for g in games if g["won"])
    total_losses = len(games) - total_wins
    avg_lakers_score = sum(lakers_scores) / len(lakers_scores) if lakers_scores else 0
    avg_opponent_score = sum(opponent_scores) / len(opponent_scores) if opponent_scores else 0
    
    # =========================================================================
    # BUILD THE PAGE LAYOUT
    # =========================================================================
    # This defines what appears on the page and in what order
    
    dash_app.layout = html.Div([
        # --- HEADER SECTION ---
        # Gold background with purple title
        html.Div([
            html.H1("Los Angeles Lakers Dashboard", 
                    style={'textAlign': 'center', 'color': '#552583', 'marginBottom': '10px'}),
            html.P("2023 Season Statistics",
                   style={'textAlign': 'center', 'color': '#666', 'fontSize': '18px'})
        ], style={'padding': '20px', 'backgroundColor': '#FDB927'}),
        
        # --- STATS CARDS ROW ---
        # Four boxes showing key statistics
        html.Div([
            # Wins card
            html.Div([
                html.H3(f"{total_wins}", style={'color': '#552583', 'fontSize': '36px', 'margin': '0'}),
                html.P("Wins", style={'margin': '0'})
            ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': '#f8f9fa', 'borderRadius': '10px', 'flex': '1', 'margin': '10px'}),
            
            # Losses card
            html.Div([
                html.H3(f"{total_losses}", style={'color': '#DC143C', 'fontSize': '36px', 'margin': '0'}),
                html.P("Losses", style={'margin': '0'})
            ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': '#f8f9fa', 'borderRadius': '10px', 'flex': '1', 'margin': '10px'}),
            
            # Average Lakers points card
            html.Div([
                html.H3(f"{avg_lakers_score:.1f}", style={'color': '#552583', 'fontSize': '36px', 'margin': '0'}),
                html.P("Avg Points", style={'margin': '0'})
            ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': '#f8f9fa', 'borderRadius': '10px', 'flex': '1', 'margin': '10px'}),
            
            # Average opponent points card
            html.Div([
                html.H3(f"{avg_opponent_score:.1f}", style={'color': '#FDB927', 'fontSize': '36px', 'margin': '0'}),
                html.P("Opp Avg Points", style={'margin': '0'})
            ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': '#f8f9fa', 'borderRadius': '10px', 'flex': '1', 'margin': '10px'}),
        ], style={'display': 'flex', 'justifyContent': 'center', 'padding': '20px'}),
        
        # --- CHART 1: Scores Over Time ---
        html.Div([
            dcc.Graph(figure=scores_fig, style={'height': '400px'})
        ], style={'padding': '20px'}),
        
        # --- CHART 2: Point Differential ---
        html.Div([
            dcc.Graph(figure=diff_fig, style={'height': '400px'})
        ], style={'padding': '20px'}),
        
        # --- CHART 3: Home vs Away ---
        html.Div([
            dcc.Graph(figure=location_fig, style={'height': '400px'})
        ], style={'padding': '20px'}),
        
        # --- FOOTER ---
        html.Div([
            html.P("Data provided by Ball Don't Lie API",
                   style={'textAlign': 'center', 'color': '#666', 'padding': '20px'})
        ])
        
    ], style={'fontFamily': 'Arial, sans-serif', 'backgroundColor': '#fff'})
    
    return dash_app
