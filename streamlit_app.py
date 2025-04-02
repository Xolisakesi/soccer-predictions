import streamlit as st
import os
import asyncio
from datetime import datetime, timedelta
import pandas as pd
import json
import logging
from dotenv import load_dotenv

# Import our predictor modules
from soccer_predictor import SoccerPredictor
from utils import parse_match_date, identify_league, format_date

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Check required environment variables
required_vars = [
    "FOOTBALL_API_KEY",
    "OPENAI_API_KEY"
]

missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    st.error(f"Missing required environment variables: {', '.join(missing_vars)}")
    st.stop()

# Initialize session state
if "history" not in st.session_state:
    st.session_state.history = []

if "predictor" not in st.session_state:
    st.session_state.predictor = SoccerPredictor()

# Run async functions in Streamlit
def run_async(func):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(func)
    loop.close()
    return result

# Page configuration
st.set_page_config(
    page_title="⚽ Global Soccer Predictions",
    page_icon="⚽",
    layout="wide"
)

# Sidebar
st.sidebar.title("⚽ Global Soccer Predictions")
st.sidebar.markdown("Get predictions for soccer matches from leagues worldwide")

# League selector
leagues = {
    "Premier League": 39,
    "La Liga": 140,
    "Bundesliga": 78,
    "Serie A": 135,
    "Ligue 1": 61,
    "Champions League": 2,
    "Europa League": 3,
    "MLS": 253,
    "Brazilian Serie A": 71
}

selected_league = st.sidebar.selectbox(
    "Choose a league (optional)",
    ["All Leagues"] + list(leagues.keys())
)

league_id = leagues.get(selected_league) if selected_league != "All Leagues" else None

# Date selector
date_options = {
    "Today": datetime.now(),
    "Tomorrow": datetime.now() + timedelta(days=1),
    "This Weekend": datetime.now() + timedelta(days=(5 - datetime.now().weekday()) % 7),
    "Custom Date": None
}

selected_date_option = st.sidebar.selectbox(
    "Choose a date",
    list(date_options.keys())
)

if selected_date_option == "Custom Date":
    custom_date = st.sidebar.date_input(
        "Select custom date",
        datetime.now()
    )
    selected_date = custom_date
else:
    selected_date = date_options[selected_date_option]

formatted_date = selected_date.strftime('%Y-%m-%d')

# Options
show_parlay = st.sidebar.checkbox("Show parlay recommendation", value=False)
show_detailed_stats = st.sidebar.checkbox("Show detailed statistics", value=False)

# Main content area
st.title("Soccer Match Predictions")
st.write(f"Showing predictions for: **{selected_date_option}** ({format_date(formatted_date)})")

if selected_league != "All Leagues":
    st.write(f"League: **{selected_league}**")

# Load fixtures
with st.spinner("Loading fixtures..."):
    fixtures = run_async(
        st.session_state.predictor.get_fixtures(formatted_date, league_id)
    )

if not fixtures:
    st.warning(f"No fixtures found for {format_date(formatted_date)}" + 
              (f" in {selected_league}" if selected_league != "All Leagues" else ""))
    st.stop()

# Group fixtures by league
leagues_fixtures = {}
for fixture in fixtures:
    league_name = fixture['league']['name']
    if league_name not in leagues_fixtures:
        leagues_fixtures[league_name] = []
    leagues_fixtures[league_name].append(fixture)

# Display fixtures and predictions
for league_name, league_fixtures in leagues_fixtures.items():
    with st.expander(f"{league_name} - {len(league_fixtures)} matches", expanded=True):
        cols = st.columns(len(league_fixtures)) if len(league_fixtures) <= 3 else st.columns(3)
        
        # Display fixtures
        fixture_buttons = {}
        for i, fixture in enumerate(league_fixtures):
            col_idx = i % 3
            with cols[col_idx]:
                home_team = fixture['teams']['home']['name']
                away_team = fixture['teams']['away']['name']
                match_time = datetime.strptime(fixture['fixture']['date'], '%Y-%m-%dT%H:%M:%S%z').strftime('%H:%M')
                
                fixture_key = f"{home_team}_vs_{away_team}"
                fixture_buttons[fixture_key] = st.button(
                    f"{home_team} vs {away_team}\n{match_time}",
                    key=f"btn_{fixture_key}",
                    use_container_width=True
                )

        # Get predictions for clicked fixtures
        for i, fixture in enumerate(league_fixtures):
            home_team = fixture['teams']['home']['name']
            away_team = fixture['teams']['away']['name']
            fixture_key = f"{home_team}_vs_{away_team}"
            
            if fixture_buttons[fixture_key]:
                with st.spinner(f"Analyzing {home_team} vs {away_team}..."):
                    prediction_data = run_async(
                        st.session_state.predictor.analyze_matchup(fixture)
                    )
                
                # Display prediction
                st.markdown("### Match Prediction")
                
                # Extract prediction details
                prediction_text = prediction_data['prediction']
                lines = prediction_text.split('\n')
                
                # Extract key information
                winner_line = next((line for line in lines if line.startswith("Winner:")), "")
                score_line = next((line for line in lines if line.startswith("Score Prediction:")), "")
                analysis_line = next((line for line in lines if line.startswith("Analysis:")), "")
                confidence_line = next((line for line in lines if line.startswith("Confidence:")), "")
                
                # Create columns for the prediction
                pred_cols = st.columns([2, 1])
                
                with pred_cols[0]:
                    st.markdown(f"**{home_team}** vs **{away_team}**")
                    if winner_line:
                        st.markdown(f"**{winner_line}**")
                    if score_line:
                        st.markdown(f"**{score_line}**")
                    if analysis_line:
                        st.markdown(f"{analysis_line}")
                    if confidence_line:
                        st.markdown(f"**{confidence_line}**")
                
                with pred_cols[1]:
                    # Display betting odds if available
                    odds = prediction_data['data']['odds']
                    if odds and 'Match Winner' in odds:
                        st.markdown("#### Betting Odds")
                        odds_df = pd.DataFrame([
                            {"Outcome": "Home Win", "Odds": next((odd['odd'] for odd in odds['Match Winner'] if odd['value'] == 'Home'), '-')},
                            {"Outcome": "Draw", "Odds": next((odd['odd'] for odd in odds['Match Winner'] if odd['value'] == 'Draw'), '-')},
                            {"Outcome": "Away Win", "Odds": next((odd['odd'] for odd in odds['Match Winner'] if odd['value'] == 'Away'), '-')}
                        ])
                        st.table(odds_df)
                
                # Show detailed stats if option is enabled
                if show_detailed_stats:
                    st.markdown("### Detailed Statistics")
                    
                    # Create tabs for different stat categories
                    stats_tabs = st.tabs(["Team Form", "Head-to-Head", "Injuries"])
                    
                    with stats_tabs[0]:
                        # Show team form and standings
                        form_cols = st.columns(2)
                        
                        with form_cols[0]:
                            st.markdown(f"#### {home_team} (Home)")
                            home_stats = prediction_data['data']['statistics']['home']
                            standings = prediction_data['data']['standings']
                            
                            if home_stats:
                                # Display basic team stats
                                if 'fixtures' in home_stats:
                                    fixtures_stats = home_stats['fixtures']
                                    st.markdown(f"**Form:** W{fixtures_stats.get('wins', {}).get('total', 0)} "
                                               f"D{fixtures_stats.get('draws', {}).get('total', 0)} "
                                               f"L{fixtures_stats.get('loses', {}).get('total', 0)}")
                                
                                # Display goals stats
                                if 'goals' in home_stats:
                                    goals_stats = home_stats['goals']
                                    st.markdown(f"**Avg Goals Scored:** {goals_stats.get('for', {}).get('average', {}).get('total', 'N/A')}")
                                    st.markdown(f"**Avg Goals Conceded:** {goals_stats.get('against', {}).get('average', {}).get('total', 'N/A')}")
                        
                        with form_cols[1]:
                            st.markdown(f"#### {away_team} (Away)")
                            away_stats = prediction_data['data']['statistics']['away']
                            
                            if away_stats:
                                # Display basic team stats
                                if 'fixtures' in away_stats:
                                    fixtures_stats = away_stats['fixtures']
                                    st.markdown(f"**Form:** W{fixtures_stats.get('wins', {}).get('total', 0)} "
                                               f"D{fixtures_stats.get('draws', {}).get('total', 0)} "
                                               f"L{fixtures_stats.get('loses', {}).get('total', 0)}")
                                
                                # Display goals stats
                                if 'goals' in away_stats:
                                    goals_stats = away_stats['goals']
                                    st.markdown(f"**Avg Goals Scored:** {goals_stats.get('for', {}).get('average', {}).get('total', 'N/A')}")
                                    st.markdown(f"**Avg Goals Conceded:** {goals_stats.get('against', {}).get('average', {}).get('total', 'N/A')}")
                    
                    with stats_tabs[1]:
                        # Show head-to-head statistics
                        h2h = prediction_data['data']['head_to_head']
                        if h2h:
                            st.markdown("#### Previous Meetings")
                            
                            # Count results
                            home_wins = 0
                            away_wins = 0
                            draws = 0
                            
                            h2h_data = []
                            
                            for match in h2h[:5]:  # Show last 5 matches
                                teams = match.get('teams', {})
                                goals = match.get('goals', {})
                                
                                if teams and goals:
                                    home_team_h2h = teams.get('home', {}).get('name', '')
                                    away_team_h2h = teams.get('away', {}).get('name', '')
                                    home_goals = goals.get('home', 0)
                                    away_goals = goals.get('away', 0)
                                    match_date = match.get('fixture', {}).get('date', '')[:10]
                                    
                                    result = "Draw"
                                    if home_goals > away_goals:
                                        result = f"{home_team_h2h} Win"
                                        if home_team_h2h == home_team:
                                            home_wins += 1
                                        else:
                                            away_wins += 1
                                    elif away_goals > home_goals:
                                        result = f"{away_team_h2h} Win"
                                        if away_team_h2h == home_team:
                                            home_wins += 1
                                        else:
                                            away_wins += 1
                                    else:
                                        draws += 1
                                    
                                    h2h_data.append({
                                        "Date": match_date,
                                        "Match": f"{home_team_h2h} vs {away_team_h2h}",
                                        "Score": f"{home_goals} - {away_goals}",
                                        "Result": result
                                    })
                            
                            # Display summary
                            st.markdown(f"**Last {len(h2h)} meetings:** {home_wins} wins for {home_team}, "
                                       f"{away_wins} wins for {away_team}, {draws} draws")
                            
                            # Display as table
                            if h2h_data:
                                st.table(pd.DataFrame(h2h_data))
                        else:
                            st.info(f"No previous meetings found between {home_team} and {away_team}")
                    
                    with stats_tabs[2]:
                        # Show injuries
                        injuries_cols = st.columns(2)
                        
                        with injuries_cols[0]:
                            st.markdown(f"#### {home_team} Injuries")
                            home_injuries = prediction_data['data']['injuries']['home']
                            
                            if home_injuries:
                                injuries_data = []
                                for injury in home_injuries:
                                    player_name = injury.get('player', {}).get('name', 'Unknown')
                                    injury_type = injury.get('player', {}).get('type', 'Unknown')
                                    injury_reason = injury.get('player', {}).get('reason', 'Unknown')
                                    
                                    injuries_data.append({
                                        "Player": player_name,
                                        "Type": injury_type,
                                        "Reason": injury_reason
                                    })
                                
                                if injuries_data:
                                    st.table(pd.DataFrame(injuries_data))
                            else:
                                st.info(f"No reported injuries for {home_team}")
                        
                        with injuries_cols[1]:
                            st.markdown(f"#### {away_team} Injuries")
                            away_injuries = prediction_data['data']['injuries']['away']
                            
                            if away_injuries:
                                injuries_data = []
                                for injury in away_injuries:
                                    player_name = injury.get('player', {}).get('name', 'Unknown')
                                    injury_type = injury.get('player', {}).get('type', 'Unknown')
                                    injury_reason = injury.get('player', {}).get('reason', 'Unknown')
                                    
                                    injuries_data.append({
                                        "Player": player_name,
                                        "Type": injury_type,
                                        "Reason": injury_reason
                                    })
                                
                                if injuries_data:
                                    st.table(pd.DataFrame(injuries_data))
                            else:
                                st.info(f"No reported injuries for {away_team}")

# Show parlay recommendation if enabled
if show_parlay:
    st.markdown("## Parlay Recommendation")
    
    with st.spinner("Generating parlay recommendation..."):
        # Analyze a subset of fixtures to generate parlay
        analysis_fixtures = fixtures[:min(8, len(fixtures))]
        
        all_predictions = []
        for fixture in analysis_fixtures:
            # Check if we already analyzed this fixture
            home_team = fixture['teams']['home']['name']
            away_team = fixture['teams']['away']['name']
            fixture_key = f"{home_team}_vs_{away_team}"
            
            prediction_data = run_async(
                st.session_state.predictor.analyze_matchup(fixture)
            )
            all_predictions.append(prediction_data)
        
        # Generate parlay
        parlay_prediction = st.session_state.predictor.generate_parlay_prediction(all_predictions)
        
        # Parse parlay prediction
        if "I don't have enough high-confidence picks" in parlay_prediction:
            st.warning(parlay_prediction)
        else:
            # Extract parlay picks
            lines = parlay_prediction.split('\n')
            parlay_picks = []
            
            for line in lines:
                if line.strip() and line[0].isdigit() and '. ' in line:
                    pick_info = line.split('. ')[1]
                    team = pick_info.split(' (')[0]
                    probability = pick_info.split('(')[1].split('%')[0]
                    parlay_picks.append({
                        "Team": team,
                        "Probability": f"{probability}%"
                    })
            
            # Extract combined probability
            combined_prob = ""
            for line in lines:
                if "Combined Probability" in line:
                    combined_prob = line.split(": ")[1]
            
            # Display parlay recommendations
            if parlay_picks:
                st.markdown("### Recommended Picks")
                st.table(pd.DataFrame(parlay_picks))
                st.markdown(f"**Combined Probability:** {combined_prob}")
                st.info("This parlay combines the highest confidence picks based on team form, injuries, and historical matchups.")
            else:
                st.warning("Couldn't generate parlay picks with high confidence for these fixtures.")

# Footer
st.divider()
st.markdown("**Global Soccer Predictions** | Powered by AI & Advanced Statistics")
