import logging
import asyncio
from typing import Dict, List, Any
import re
from openai import OpenAI
import os

from utils import format_team_standing, format_team_stats, format_h2h_results, format_betting_odds

# Configure logging
logger = logging.getLogger(__name__)

class MatchPredictor:
    """Helper class for generating soccer match predictions."""
    
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
    async def generate_prediction(self, fixture: Dict, fixture_data: Dict) -> str:
        """Generate prediction with LLM."""
        try:
            home_team = fixture['teams']['home']
            away_team = fixture['teams']['away']
            league = fixture['league']
            
            # Extract all the required data
            home_stats = fixture_data['home_stats']
            away_stats = fixture_data['away_stats']
            standings = fixture_data['standings']
            h2h = fixture_data['head_to_head']
            home_injuries = fixture_data['home_injuries']
            away_injuries = fixture_data['away_injuries']
            odds = fixture_data['odds']
            
            # Get team standings if available
            home_standing = standings.get(home_team['id'], {})
            away_standing = standings.get(away_team['id'], {})
            
            # Format head-to-head results
            h2h_summary = format_h2h_results(h2h, home_team['id'], away_team['id'])
            
            # Format injuries
            home_injuries_formatted = ", ".join([
                f"{inj['player']['name']} ({inj['player']['type']})"
                for inj in home_injuries
            ]) if home_injuries else "None reported"
            
            away_injuries_formatted = ", ".join([
                f"{inj['player']['name']} ({inj['player']['type']})"
                for inj in away_injuries
            ]) if away_injuries else "None reported"
            
            # Create detailed prompt for analysis
            analysis_prompt = f"""
            Analyze this {league['name']} matchup between {away_team['name']} (Away) and {home_team['name']} (Home).
            
            Match details:
            - Date: {fixture['fixture']['date']}
            - Venue: {fixture['fixture']['venue']['name'] if fixture['fixture'].get('venue') else 'Unknown'}
            
            HOME TEAM ({home_team['name']}):
            {format_team_standing(home_standing)}
            {format_team_stats(home_stats)}
            Injuries: {home_injuries_formatted}
            
            AWAY TEAM ({away_team['name']}):
            {format_team_standing(away_standing)}
            {format_team_stats(away_stats)}
            Injuries: {away_injuries_formatted}
            
            HEAD-TO-HEAD HISTORY:
            {h2h_summary}
            
            BETTING ODDS:
            {format_betting_odds(odds) if odds else 'Not available'}
            
            Provide your response in exactly this format:
            Winner: [Team Name] ([Win Probability]%)
            Score Prediction: [Score]
            Analysis: 3-4 sentences analyzing key factors including form, home/away advantage, key player availability, and historical matchups
            Confidence: High/Medium/Low
            """
            
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an expert football/soccer analyst with deep knowledge of leagues worldwide. Provide predictions in the exact format requested."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            ai_analysis = response.choices[0].message.content.strip()
            
            # Format the prediction
            prediction = f"⚽ {away_team['name']} (Away) @ {home_team['name']} (Home)\n"
            prediction += f"League: {league['name']} ({league['country']})\n\n"
            
            # Add the AI analysis
            lines = ai_analysis.split('\n')
            for line in lines:
                if line.strip():
                    prediction += f"{line}\n"
            
            # Format betting lines if available
            if odds and 'Match Winner' in odds:
                prediction += "\nBetting Odds:\n"
                for odd in odds.get('Match Winner', []):
                    if odd['value'] == 'Home':
                        prediction += f"{home_team['name']} win: {odd['odd']}\n"
                    elif odd['value'] == 'Away':
                        prediction += f"{away_team['name']} win: {odd['odd']}\n"
                    elif odd['value'] == 'Draw':
                        prediction += f"Draw: {odd['odd']}\n"
                        
            return prediction

        except Exception as e:
            logger.error(f"Error generating prediction: {str(e)}")
            return f"⚽ {away_team['name']} (Away) @ {home_team['name']} (Home)\n\nUnable to generate prediction: {str(e)}"
            
    def generate_parlay_prediction(self, predictions: List[Dict]) -> str:
        """Generate a parlay prediction based on highest confidence picks."""
        try:
            # Filter predictions with high confidence
            high_confidence_picks = []
            
            for pred in predictions:
                prediction_text = pred['prediction']
                
                # Extract win probability and confidence level
                winner_line = [line for line in prediction_text.split('\n') if 'Winner:' in line]
                confidence_line = [line for line in prediction_text.split('\n') if 'Confidence:' in line]
                
                if winner_line and confidence_line:
                    winner_text = winner_line[0]
                    confidence = confidence_line[0].split(': ')[1].split()[0] if confidence_line else "Unknown"
                    
                    # Extract probability if available
                    prob_match = re.search(r'\((\d+)%\)', winner_text)
                    probability = float(prob_match.group(1)) if prob_match else 50.0
                    
                    # Extract team name
                    team_name = winner_text.split(':')[1].split('(')[0].strip() if ':' in winner_text else "Unknown"
                    
                    # Get betting odds
                    betting_lines = ""
                    if "Betting Odds:" in prediction_text:
                        odds_section = prediction_text.split("Betting Odds:")[1]
                        betting_lines = odds_section.strip()
                    
                    if confidence == "High" and probability > 60:
                        high_confidence_picks.append({
                            'matchup': pred['matchup'],
                            'winner': team_name,
                            'probability': probability,
                            'betting_lines': betting_lines
                        })

            if not high_confidence_picks:
                return "I don't have enough high-confidence picks to recommend a parlay today."

            # Sort by probability
            high_confidence_picks.sort(key=lambda x: x['probability'], reverse=True)
            
            # Take top 2-3 picks
            parlay_picks = high_confidence_picks[:min(3, len(high_confidence_picks))]
            
            # Calculate combined probability
            combined_prob = 100
            for pick in parlay_picks:
                combined_prob *= (pick['probability'] / 100)
            
            # Generate parlay prediction
            parlay = "🎲 Recommended Parlay:\n\n"
            for i, pick in enumerate(parlay_picks, 1):
                parlay += f"{i}. {pick['winner']} ({pick['probability']:.0f}% probability)\n"
                if pick['betting_lines']:
                    odds_line = [line for line in pick['betting_lines'].split('\n') if pick['winner'] in line]
                    if odds_line:
                        parlay += f"   Odds: {odds_line[0].split(':')[1].strip()}\n"
            
            parlay += f"\nCombined Probability: {combined_prob:.1f}%\n"
            parlay += "Note: This parlay combines the highest confidence picks based on team form, injuries, and historical matchups."
            
            return parlay
            
        except Exception as e:
            logger.error(f"Error generating parlay: {str(e)}")
            return "Sorry, I couldn't generate a parlay prediction at this time."