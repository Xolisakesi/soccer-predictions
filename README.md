# Global Soccer Predictions Bot

An AI-powered soccer predictions and betting insights application that provides game predictions, betting odds, and analysis for leagues worldwide. Designed to help users make data-driven decisions, it evaluates upcoming matchups, potential outcomes, and relevant statistics, offering valuable insights for sports betting enthusiasts.

## Features
- Real-time soccer game predictions for worldwide leagues
- Betting odds and analysis
- Team-specific insights
- Historical matchup data analysis
- League standing information
- Injuries and player availability tracking
- Parlay/Accumulator suggestions
- Interactive Streamlit UI

## Supported Leagues
- Premier League (England)
- La Liga (Spain)
- Bundesliga (Germany)
- Serie A (Italy)
- Ligue 1 (France)
- Primeira Liga (Portugal)
- Eredivisie (Netherlands)
- Championship (England)
- MLS (USA)
- Brazilian Serie A
- Argentine Primera Division
- Champions League
- Europa League
- Conference League
- World Cup
- European Championship
- Copa America
- Africa Cup of Nations
- And many more via the API-Football database

## Tech Stack
- Backend: Python
- Frontend: Streamlit
- Database: Supabase (optional)
- APIs: API-Football (via RapidAPI), OpenAI API

## Setup
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables in `.env`:
   - FOOTBALL_API_KEY (via RapidAPI)
   - OPENAI_API_KEY
   - SUPABASE_URL (optional)
   - SUPABASE_SERVICE_KEY (optional)

4. Run the Streamlit application:
```python
streamlit run streamlit_app.py
```

## Project Structure
- `streamlit_app.py`: Main Streamlit application 
- `soccer_predictor.py`: Core prediction logic and API interactions
- `api_client.py`: API client for Football API
- `prediction_helper.py`: Prediction generation
- `utils.py`: Utility functions and data mappings
- `requirements.txt`: Python dependencies
- `Dockerfile`: Container definition

## Deployment
The application can be deployed on any platform supporting Streamlit:

### Local Deployment
```bash
streamlit run streamlit_app.py
```

### Docker Deployment
```bash
docker build -t soccer-predictions-bot .
docker run -p 8501:8501 soccer-predictions-bot
```

### Streamlit Cloud
The application can be easily deployed on Streamlit Cloud by connecting your GitHub repository.

## License
MIT