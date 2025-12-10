"""
Lakers Dashboard - Application Entry Point
==========================================
This is the file that starts the entire application.

It combines two different apps:
1. The FastAPI app (main.py) - handles the main pages and API
2. The Dash app (dashboard.py) - provides the interactive /dash/ dashboard

The FastAPI app runs on port 5000 and the Dash app is "mounted" at /dash/
so you can access both from the same server.

URLs:
- http://localhost:5000/       - Home page
- http://localhost:5000/team   - Main Lakers dashboard
- http://localhost:5000/dash/  - Alternative Dash dashboard
"""

# --- IMPORTS ---
from fastapi.middleware.wsgi import WSGIMiddleware  # Lets FastAPI serve Dash apps
from main import app                                 # The FastAPI application
from dashboard import create_dash_app               # Function to create the Dash app
import uvicorn                                       # The web server

# --- CREATE AND MOUNT THE DASH APP ---
# Create the Dash dashboard app
dash_app = create_dash_app()

# Mount it at /dash so it's accessible at http://localhost:5000/dash/
# WSGIMiddleware is needed because Dash uses WSGI while FastAPI uses ASGI
app.mount("/dash", WSGIMiddleware(dash_app.server))

# --- START THE SERVER ---
# This runs when you execute: python run.py
if __name__ == "__main__":
    # Start the server on all network interfaces (0.0.0.0) on port 5000
    uvicorn.run(app, host="0.0.0.0", port=5000)
