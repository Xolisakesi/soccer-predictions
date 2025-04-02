import os
import logging
from typing import Dict, List, Optional, Any
import httpx
import asyncio

# Configure logging
logger = logging.getLogger(__name__)

class FootballAPIClient:
    """Client for interacting with the Football API."""
    
    def __init__(self):
        self.base_url = "https://api-football-v1.p.rapidapi.com/v3"
        self.api_key = os.getenv("FOOTBALL_API_KEY")
        self.api_host = "api-football-v1.p.rapidapi.com"
        
        # Check if API key is available
        if not self.api_key:
            logger.warning("FOOTBALL_API_KEY environment variable not set")
            
        self.headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.api_host
        }
        
        # Current season - update this as needed
        self.current_season = 2024

    async def get_fixtures(self, date: str, league_id: Optional[int] = None) -> List[Dict]:
        """Fetch fixtures for a specific date and optionally a specific league."""
        logger.info(f"Fetching fixtures for date: {date}, league_id: {league_id}")
        url = f"{self.base_url}/fixtures"
        
        # Set up parameters
        params = {"date": date}
        if league_id:
            params["league"] = league_id
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                fixtures = data.get('response', [])
                logger.info(f"Found {len(fixtures)} fixtures for {date}" + (f" in league {league_id}" if league_id else ""))
                return fixtures
        except Exception as e:
            logger.error(f"Error fetching fixtures: {str(e)}")
            return []

    async def get_league_fixtures(self, league_id: int, season: Optional[int] = None) -> List[Dict]:
        """Fetch fixtures for a specific league and season."""
        logger.info(f"Fetching fixtures for league: {league_id}, season: {season or self.current_season}")
        url = f"{self.base_url}/fixtures"
        
        # Use current season if none provided
        if not season:
            season = self.current_season
            
        params = {
            "league": league_id,
            "season": season
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                return data.get('response', [])
        except Exception as e:
            logger.error(f"Error fetching league fixtures: {str(e)}")
            return []

    async def get_standings(self, league_id: int, season: Optional[int] = None) -> Dict:
        """Get current standings for a league."""
        logger.info(f"Fetching standings for league: {league_id}")
        url = f"{self.base_url}/standings"
        
        # Use current season if none provided
        if not season:
            season = self.current_season
            
        params = {
            "league": league_id,
            "season": season
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                standings_data = data.get('response', [])
                
                # Process and format standings
                standings = {}
                if standings_data and len(standings_data) > 0:
                    for league_standing in standings_data:
                        for standing_item in league_standing.get('league', {}).get('standings', []):
                            for team in standing_item:
                                team_id = team.get('team', {}).get('id')
                                if team_id:
                                    standings[team_id] = {
                                        'rank': team.get('rank'),
                                        'points': team.get('points'),
                                        'goalsDiff': team.get('goalsDiff'),
                                        'form': team.get('form'),
                                        'all': team.get('all', {}),
                                        'home': team.get('home', {}),
                                        'away': team.get('away', {})
                                    }
                return standings
        except Exception as e:
            logger.error(f"Error fetching standings: {str(e)}")
            return {}

    async def get_team_info(self, team_id: int) -> Dict:
        """Get detailed information about a team."""
        logger.info(f"Fetching team info for team_id: {team_id}")
        url = f"{self.base_url}/teams"
        
        params = {"id": team_id}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                teams = data.get('response', [])
                return teams[0] if teams else {}
        except Exception as e:
            logger.error(f"Error fetching team info: {str(e)}")
            return {}

    async def get_team_statistics(self, team_id: int, league_id: int, season: Optional[int] = None) -> Dict:
        """Get team statistics for a particular league and season."""
        logger.info(f"Fetching team statistics for team: {team_id}, league: {league_id}")
        url = f"{self.base_url}/teams/statistics"
        
        # Use current season if none provided
        if not season:
            season = self.current_season
            
        params = {
            "team": team_id,
            "league": league_id,
            "season": season
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                return data.get('response', {})
        except Exception as e:
            logger.error(f"Error fetching team statistics: {str(e)}")
            return {}

    async def get_head_to_head(self, team1_id: int, team2_id: int, limit: int = 10) -> List[Dict]:
        """Get head-to-head fixtures between two teams."""
        logger.info(f"Fetching head-to-head for teams: {team1_id} vs {team2_id}")
        url = f"{self.base_url}/fixtures/headtohead"
        
        params = {
            "h2h": f"{team1_id}-{team2_id}",
            "last": limit  # Number of past meetings to retrieve
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                return data.get('response', [])
        except Exception as e:
            logger.error(f"Error fetching head-to-head: {str(e)}")
            return []

    async def get_team_injuries(self, team_id: int, league_id: Optional[int] = None, season: Optional[int] = None) -> List[Dict]:
        """Fetch current injuries for a team, optionally filtered by league."""
        logger.info(f"Fetching injuries for team: {team_id}")
        url = f"{self.base_url}/injuries"
        
        # Use current season if none provided
        if not season:
            season = self.current_season
            
        params = {
            "team": team_id,
            "season": season
        }
        
        if league_id:
            params["league"] = league_id
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                return data.get('response', [])
        except Exception as e:
            logger.error(f"Error fetching team injuries: {str(e)}")
            return []

    async def get_fixture_odds(self, fixture_id: int, bookmaker_id: int = 1) -> Dict:
        """Fetch betting odds for a specific fixture."""
        logger.info(f"Fetching odds for fixture: {fixture_id}")
        url = f"{self.base_url}/odds"
        
        params = {
            "fixture": fixture_id,
            "bookmaker": bookmaker_id  # Using default bookmaker (could be made configurable)
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                odds_data = data.get('response', [])
                
                # Process and format odds
                odds = {}
                if odds_data:
                    for odds_item in odds_data:
                        bookmakers = odds_item.get('bookmakers', [])
                        if bookmakers:
                            for bookmaker in bookmakers:
                                bets = bookmaker.get('bets', [])
                                for bet in bets:
                                    bet_name = bet.get('name')
                                    if bet_name not in odds:
                                        odds[bet_name] = []
                                    values = [
                                        {"value": value.get('value'), "odd": value.get('odd')} 
                                        for value in bet.get('values', [])
                                    ]
                                    odds[bet_name].extend(values)
                return odds
        except Exception as e:
            logger.error(f"Error fetching fixture odds: {str(e)}")
            return {}

    async def get_players(self, team_id: int, season: Optional[int] = None) -> List[Dict]:
        """Get players for a specific team and season."""
        logger.info(f"Fetching players for team: {team_id}")
        url = f"{self.base_url}/players"
        
        # Use current season if none provided
        if not season:
            season = self.current_season
            
        params = {
            "team": team_id,
            "season": season
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                return data.get('response', [])
        except Exception as e:
            logger.error(f"Error fetching players: {str(e)}")
            return []

    async def get_live_fixtures(self) -> List[Dict]:
        """Fetch currently live fixtures."""
        logger.info("Fetching live fixtures")
        url = f"{self.base_url}/fixtures"
        
        params = {"live": "all"}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                return data.get('response', [])
        except Exception as e:
            logger.error(f"Error fetching live fixtures: {str(e)}")
            return []

    async def get_league_info(self, league_id: int) -> Dict:
        """Get information about a specific league."""
        logger.info(f"Fetching league info for league_id: {league_id}")
        url = f"{self.base_url}/leagues"
        
        params = {"id": league_id}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                leagues = data.get('response', [])
                return leagues[0] if leagues else {}
        except Exception as e:
            logger.error(f"Error fetching league info: {str(e)}")
            return {}

    async def search_teams(self, name: str) -> List[Dict]:
        """Search for teams by name."""
        logger.info(f"Searching for team: {name}")
        url = f"{self.base_url}/teams"
        
        params = {"search": name}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                return data.get('response', [])
        except Exception as e:
            logger.error(f"Error searching teams: {str(e)}")
            return []

    async def batch_fetch(self, fixture: Dict) -> Dict[str, Any]:
        """Fetch all relevant data for a fixture in a batch."""
        home_team = fixture['teams']['home']
        away_team = fixture['teams']['away']
        league_id = fixture['league']['id']
        fixture_id = fixture['fixture']['id']
        
        # Create all tasks
        tasks = [
            self.get_team_statistics(home_team['id'], league_id),
            self.get_team_statistics(away_team['id'], league_id),
            self.get_standings(league_id),
            self.get_head_to_head(home_team['id'], away_team['id']),
            self.get_team_injuries(home_team['id'], league_id),
            self.get_team_injuries(away_team['id'], league_id),
            self.get_fixture_odds(fixture_id)
        ]
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks)
        
        # Return structured results
        return {
            "home_stats": results[0],
            "away_stats": results[1],
            "standings": results[2],
            "head_to_head": results[3],
            "home_injuries": results[4],
            "away_injuries": results[5],
            "odds": results[6]
        }