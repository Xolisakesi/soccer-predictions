import logging
import os
from typing import Dict, List, Optional, Any
import asyncio

from api_client import FootballAPIClient
from prediction_helper import MatchPredictor
from utils import parse_match_date, identify_league, identify_team

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SoccerPredictor:
    """Main class for soccer predictions and API interactions."""
    
    def __init__(self):
        """Initialize the soccer predictor with API configuration"""
        self.api_client = FootballAPIClient()
        self.predictor = MatchPredictor()
        
        # Default season
        self.current_season = 2024

    async def parse_match_date(self, query: str) -> str:
        """Parse date from query with timezone handling."""
        return parse_match_date(query)

    async def analyze_league(self, query: str) -> Optional[int]:
        """Identify league from query."""
        return identify_league(query)
        
    async def analyze_team(self, query: str) -> Optional[str]:
        """Identify team from query."""
        return identify_team(query)

    async def get_fixtures(self, date: str, league_id: Optional[int] = None) -> List[Dict]:
        """Fetch fixtures for a specific date and optionally a specific league."""
        return await self.api_client.get_fixtures(date, league_id)

    async def get_league_fixtures(self, league_id: int, season: Optional[int] = None) -> List[Dict]:
        """Fetch fixtures for a specific league and season."""
        return await self.api_client.get_league_fixtures(league_id, season or self.current_season)

    async def get_standings(self, league_id: int, season: Optional[int] = None) -> Dict:
        """Get current standings for a league."""
        return await self.api_client.get_standings(league_id, season or self.current_season)

    async def get_team_info(self, team_id: int) -> Dict:
        """Get detailed information about a team."""
        return await self.api_client.get_team_info(team_id)

    async def get_team_statistics(self, team_id: int, league_id: int, season: Optional[int] = None) -> Dict:
        """Get team statistics for a particular league and season."""
        return await self.api_client.get_team_statistics(team_id, league_id, season or self.current_season)

    async def get_head_to_head(self, team1_id: int, team2_id: int) -> List[Dict]:
        """Get head-to-head fixtures between two teams."""
        return await self.api_client.get_head_to_head(team1_id, team2_id)

    async def get_team_injuries(self, team_id: int, league_id: Optional[int] = None) -> List[Dict]:
        """Fetch current injuries for a team, optionally filtered by league."""
        return await self.api_client.get_team_injuries(team_id, league_id)

    async def get_fixture_odds(self, fixture_id: int) -> Dict:
        """Fetch betting odds for a specific fixture."""
        return await self.api_client.get_fixture_odds(fixture_id)

    async def get_players(self, team_id: int, season: Optional[int] = None) -> List[Dict]:
        """Get players for a specific team and season."""
        return await self.api_client.get_players(team_id, season or self.current_season)

    async def get_live_fixtures(self) -> List[Dict]:
        """Fetch currently live fixtures."""
        return await self.api_client.get_live_fixtures()

    async def analyze_matchup(self, fixture: Dict) -> Dict:
        """Analyze a matchup and generate prediction."""
        try:
            # Fetch all necessary data for the fixture
            fixture_data = await self.api_client.batch_fetch(fixture)
            
            # Generate prediction
            prediction = await self.predictor.generate_prediction(fixture, fixture_data)
            
            # Return formatted result
            return {
                "matchup": f"{fixture['teams']['away']['name']} @ {fixture['teams']['home']['name']}",
                "prediction": prediction,
                "data": {
                    "fixture": fixture,
                    "home_team": fixture['teams']['home'],
                    "away_team": fixture['teams']['away'],
                    "league": fixture['league'],
                    "statistics": {
                        "home": fixture_data["home_stats"],
                        "away": fixture_data["away_stats"]
                    },
                    "standings": fixture_data["standings"],
                    "head_to_head": fixture_data["head_to_head"],
                    "injuries": {
                        "home": fixture_data["home_injuries"],
                        "away": fixture_data["away_injuries"]
                    },
                    "odds": fixture_data["odds"]
                }
            }
        except Exception as e:
            logger.error(f"Error in analyze_matchup: {str(e)}")
            raise

    def generate_parlay_prediction(self, predictions: List[Dict]) -> str:
        """Generate a parlay prediction based on highest confidence picks."""
        return self.predictor.generate_parlay_prediction(predictions)