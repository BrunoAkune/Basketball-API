# Overview

This is a web application that displays Los Angeles Lakers NBA game statistics through an interactive dashboard. The application fetches game data from the BallDontLie NBA API and visualizes it using Plotly charts within a Dash dashboard, served through a FastAPI backend.

The system provides:
- Real-time Lakers game score tracking
- Visual comparisons between Lakers and opponent scores
- Game-by-game performance metrics
- Interactive data visualizations

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture

**Dash-based Visualization Layer**
- **Problem**: Need interactive, real-time data visualizations for NBA game statistics
- **Solution**: Dash framework with Plotly for chart generation
- **Rationale**: Dash provides Python-native dashboarding without requiring JavaScript, integrating seamlessly with the FastAPI backend
- **Components**:
  - Plotly graphs for score comparisons and trend analysis
  - Interactive time-series visualizations
  - Custom Lakers-branded color schemes (#552583 purple, #FDB927 gold)

## Backend Architecture

**FastAPI Web Framework**
- **Problem**: Need a lightweight, modern API server to handle HTTP requests and serve dashboard
- **Solution**: FastAPI with WSGI middleware integration
- **Rationale**: FastAPI offers high performance, automatic API documentation, and easy integration with WSGI applications like Dash
- **Design Pattern**: Microservices-style separation with dedicated service layer for NBA data

**Service Layer Pattern**
- **Problem**: Separate business logic from presentation and routing
- **Solution**: `services/nba.py` module encapsulates all NBA API interactions
- **Rationale**: Promotes code reusability, testability, and separation of concerns
- **Key Functions**:
  - `get_lakers_games()`: Fetches and processes game data with team-specific logic
  - Data transformation layer that normalizes home/away game differences

## Application Integration

**WSGI Middleware Bridge**
- **Problem**: Integrate Dash (WSGI) with FastAPI (ASGI)
- **Solution**: FastAPI's `WSGIMiddleware` to mount Dash app at `/dash` route
- **Implementation**: `run.py` orchestrates both applications
- **Pros**: Unified deployment, single port, shared infrastructure
- **Cons**: WSGI-ASGI bridge adds minimal overhead

## Data Processing

**Game Data Normalization**
- **Problem**: API returns games from both home and away perspectives
- **Solution**: Custom processing logic that identifies Lakers position and normalizes scores
- **Features**:
  - Automatic home/away detection based on team ID
  - Win/loss determination
  - Point differential calculations
  - Location tracking

**API Response Caching**
- **Problem**: BallDontLie API has rate limits that cause 429 errors on frequent requests
- **Solution**: In-memory caching with 5-minute TTL and stale-fallback mechanism
- **Features**:
  - Fresh cache served immediately without API calls
  - Stale cache served when API returns errors (429/5xx) or times out
  - Prevents dashboard from breaking during rate limiting
  - Cache keys based on team ID, season, and page size

# External Dependencies

## Third-Party APIs

**BallDontLie NBA API**
- **Purpose**: Primary data source for NBA game statistics
- **Endpoint**: `https://api.balldontlie.io/v1`
- **Authentication**: API key-based (hardcoded: `593a23ee-fa08-44fc-bced-3c622004e575`)
- **Key Endpoints**:
  - `/teams/{id}`: Team information lookup
  - `/games`: Game data with filtering by team, season, pagination
- **Rate Limits**: Unknown from code (should be documented)
- **Data Structure**: JSON responses with nested team and score objects

## Python Frameworks & Libraries

**Web Framework Stack**
- **FastAPI**: ASGI web framework for API routes
- **Uvicorn**: ASGI server for running FastAPI
- **Dash**: Reactive web framework for dashboards
- **Plotly**: Visualization library (graph_objects and express modules)

**HTTP Client**
- **requests**: HTTP library for external API calls

## Configuration

**Hardcoded Constants**
- Lakers Team ID: `14`
- Default season: `2023` (dashboard), `2024` (main.py endpoints)
- API key stored directly in source code (security concern)
- Server configuration: Host `0.0.0.0`, Port `5000` (run.py), Port `8080` (main-2.py)

**Architectural Notes**
- Multiple entry points (`main.py`, `main-2.py`, `run.py`) suggest development evolution
- `run.py` appears to be the production entry point
- No environment variable management detected
- No database layer currently implemented