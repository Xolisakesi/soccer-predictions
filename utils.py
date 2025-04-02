import logging
import pytz
from datetime import datetime, timedelta
import re
import dateparser
from typing import Dict, List, Optional, Any

# Configure logging
logger = logging.getLogger(__name__)

# Global constants
DEFAULT_TIMEZONE = "Europe/London"

# League mappings
LEAGUE_MAPPINGS = {
    "premier league": 39,
    "epl": 39,
    "la liga": 140,
    "bundesliga": 78,
    "serie a": 135,
    "ligue 1": 61,
    "primeira liga": 94,
    "eredivisie": 88,
    "championship": 40,
    "mls": 253,
    "brazilian serie a": 71,
    "argentine primera": 128,
    "champions league": 2,
    "ucl": 2,
    "europa league": 3,
    "uel": 3,
    "conference league": 848,
    "world cup": 1,
    "euro": 4,
    "copa america": 13,
    "afcon": 12
}

# Country to league mappings
COUNTRY_MAPPINGS = {
    "england": 39,
    "english": 39,
    "spain": 140,
    "spanish": 140,
    "germany": 78,
    "german": 78,
    "italy": 135,
    "italian": 135,
    "france": 61,
    "french": 61,
    "portugal": 94,
    "portuguese": 94,
    "netherlands": 88,
    "dutch": 88,
    "brazil": 71,
    "brazilian": 71,
    "argentina": 128,
    "argentinian": 128,
    "usa": 253,
    "america": 253
}

# Team name variations
TEAM_VARIATIONS = {
    "manchester united": ["man utd", "man united", "man u", "united", "mufc"],
    "manchester city": ["man city", "city", "mcfc"],
    "liverpool": ["lfc", "the reds"],
    "arsenal": ["the gunners", "afc"],
    "chelsea": ["the blues", "cfc"],
    "tottenham": ["spurs", "thfc"],
    "barcelona": ["barca", "fcb"],
    "real madrid": ["madrid", "los blancos"],
    "bayern munich": ["bayern", "fcb"],
    "paris saint-germain": ["psg", "paris"],
    "juventus": ["juve", "the old lady"],
    "ac milan": ["milan"],
    "inter milan": ["inter"],
    "borussia dortmund": ["dortmund", "bvb"]
}

# Timezone configurations for different regions
TIMEZONE_MAPPINGS = {
    "europe": "Europe/London",
    "north_america": "America/New_York",
    "south_america": "America/Sao_Paulo",
    "asia": "Asia/Tokyo",
    "africa": "Africa/Cairo",
    "australia": "Australia/Sydney"
}

def format_date(date_str: str) -> str:
    """Format date in a readable format."""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%A, %B %d, %Y")
    except Exception:
        return date_str

def parse_match_date(query: str) -> str:
    """Parse date from query with timezone handling."""
    try:
        query_lower = query.lower()
        
        # Default timezone (can be made smarter based on mentioned leagues)
        tz = pytz.timezone(DEFAULT_TIMEZONE)
        current_date = datetime.now(tz)
        
        # Handle relative dates
        if 'tomorrow' in query_lower:
            target_date = current_date + timedelta(days=1)
        elif 'yesterday' in query_lower:
            target_date = current_date - timedelta(days=1)
        elif 'today' in query_lower or 'tonight' in query_lower:
            target_date = current_date
        elif 'weekend' in query_lower:
            # Find next Saturday
            days_until_saturday = (5 - current_date.weekday()) % 7
            target_date = current_date + timedelta(days=days_until_saturday)
        elif 'next week' in query_lower:
            target_date = current_date + timedelta(days=7)
        else:
            # Convert common date formats to standard format
            # First, try to find date patterns in the query
            date_pattern = r'(?i)(jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|aug|august|sep|september|oct|october|nov|november|dec|december)\s+\d{1,2}'
            match = re.search(date_pattern, query_lower)
            
            if match:
                date_str = match.group(0)
                # Try to parse the extracted date
                parsed_date = dateparser.parse(
                    date_str,
                    settings={
                        'TIMEZONE': tz.zone,
                        'RETURN_AS_TIMEZONE_AWARE': True,
                        'PREFER_DATES_FROM': 'future'
                    }
                )
                if parsed_date:
                    target_date = parsed_date
                else:
                    raise ValueError(f"Could not parse date from: {date_str}")
            else:
                # If no date pattern found, try parsing the entire query
                parsed_date = dateparser.parse(
                    query_lower,
                    settings={
                        'TIMEZONE': tz.zone,
                        'RETURN_AS_TIMEZONE_AWARE': True,
                        'PREFER_DATES_FROM': 'future'
                    }
                )
                if parsed_date:
                    target_date = parsed_date
                else:
                    # If no date found, assume today
                    target_date = current_date
        
        # Format the date in YYYY-MM-DD
        return target_date.strftime('%Y-%m-%d')
        
    except Exception as e:
        logger.error(f"Error parsing date from query: {str(e)}")
        # Default to today's date if parsing fails
        return datetime.now().strftime('%Y-%m-%d')

def identify_league(query: str) -> Optional[int]:
    """Identify league ID from the query."""
    query_lower = query.lower()
    
    # Check direct league name matches
    for league_name, league_id in LEAGUE_MAPPINGS.items():
        if league_name in query_lower:
            return league_id
    
    # Check country matches
    for country, league_id in COUNTRY_MAPPINGS.items():
        if country in query_lower:
            return league_id
    
    return None

def identify_team(query: str) -> Optional[str]:
    """Identify team name from the query."""
    query_lower = query.lower()
    
    # Check direct team name and variations
    for team_name, variations in TEAM_VARIATIONS.items():
        if team_name in query_lower:
            return team_name
        
        for variation in variations:
            if variation in query_lower:
                return team_name
    
    return None

def format_team_standing(standing: Dict) -> str:
    """Format team standing information."""
    if not standing:
        return "Standing: Information not available"
        
    all_stats = standing.get('all', {})
    home_stats = standing.get('home', {})
    away_stats = standing.get('away', {})
    
    result = f"Position: {standing.get('rank', 'N/A')}, Points: {standing.get('points', 'N/A')}, Goal Difference: {standing.get('goalsDiff', 'N/A')}\n"
    result += f"Form: {standing.get('form', 'N/A')}\n"
    
    if all_stats:
        result += f"Overall: {all_stats.get('played', 0)}G {all_stats.get('win', 0)}W {all_stats.get('draw', 0)}D {all_stats.get('lose', 0)}L, Goals: {all_stats.get('goals', {}).get('for', 0)}-{all_stats.get('goals', {}).get('against', 0)}\n"
    
    if home_stats:
        result += f"Home: {home_stats.get('played', 0)}G {home_stats.get('win', 0)}W {home_stats.get('draw', 0)}D {home_stats.get('lose', 0)}L, Goals: {home_stats.get('goals', {}).get('for', 0)}-{home_stats.get('goals', {}).get('against', 0)}\n"
        
    if away_stats:
        result += f"Away: {away_stats.get('played', 0)}G {away_stats.get('win', 0)}W {away_stats.get('draw', 0)}D {away_stats.get('lose', 0)}L, Goals: {away_stats.get('goals', {}).get('for', 0)}-{away_stats.get('goals', {}).get('against', 0)}\n"
        
    return result

def format_team_stats(stats: Dict) -> str:
    """Format team statistics."""
    if not stats:
        return "Statistics: Not available"
        
    result = "Key Stats:\n"
    
    # Add offensive stats
    goals = stats.get('goals', {})
    if goals:
        result += f"Avg Goals Scored: {goals.get('for', {}).get('average', {}).get('total', 'N/A')} per game\n"
        result += f"Avg Goals Conceded: {goals.get('against', {}).get('average', {}).get('total', 'N/A')} per game\n"
    
    # Add clean sheets
    clean_sheets = stats.get('clean_sheet', {})
    if clean_sheets:
        total_cs = clean_sheets.get('total', 0)
        result += f"Clean Sheets: {total_cs}\n"
    
    # Add form
    fixtures = stats.get('fixtures', {})
    if fixtures:
        result += f"Form: W{fixtures.get('wins', {}).get('total', 0)} D{fixtures.get('draws', {}).get('total', 0)} L{fixtures.get('loses', {}).get('total', 0)}\n"
    
    return result

def format_h2h_results(h2h: List, home_id: int, away_id: int) -> str:
    """Format head-to-head results between two teams."""
    if not h2h:
        return "No recent head-to-head matches found"
        
    home_wins = 0
    away_wins = 0
    draws = 0
    
    recent_matches = []
    
    for match in h2h[:5]:  # Show last 5 matches
        teams = match.get('teams', {})
        goals = match.get('goals', {})
        
        if teams and goals:
            home_team = teams.get('home', {})
            away_team = teams.get('away', {})
            
            home_goals = goals.get('home', 0)
            away_goals = goals.get('away', 0)
            
            if home_goals > away_goals:
                if home_team.get('id') == home_id:
                    home_wins += 1
                else:
                    away_wins += 1
            elif away_goals > home_goals:
                if away_team.get('id') == home_id:
                    home_wins += 1
                else:
                    away_wins += 1
            else:
                draws += 1
            
            match_str = f"{home_team.get('name')} {home_goals}-{away_goals} {away_team.get('name')} ({match.get('fixture', {}).get('date', '')[:10]})"
            recent_matches.append(match_str)
    
    result = f"Last {len(h2h)} meetings: {home_wins} wins for current home team, {away_wins} wins for current away team, {draws} draws\n"
    result += "Recent results:\n"
    result += "\n".join(recent_matches)
        
    return result

def format_betting_odds(odds: Dict) -> str:
    """Format betting odds data."""
    if not odds:
        return "Betting odds not available"
        
    result = ""
    
    if 'Match Winner' in odds:
        result += "Match Result:\n"
        for odd in odds['Match Winner']:
            result += f"- {odd['value']}: {odd['odd']}\n"
    
    if 'Goals Over/Under' in odds:
        result += "\nGoals Over/Under:\n"
        for odd in odds['Goals Over/Under']:
            result += f"- {odd['value']}: {odd['odd']}\n"
            
    if 'Both Teams Score' in odds:
        result += "\nBoth Teams to Score:\n"
        for odd in odds['Both Teams Score']:
            result += f"- {odd['value']}: {odd['odd']}\n"
    
    return result