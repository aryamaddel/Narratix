import re
import logging
from typing import Dict, Any, List

# Import Gemini configuration
from utils.core.gemini_setup import GEMINI_AVAILABLE, DEFAULT_MODEL

logger = logging.getLogger(__name__)

def generate_consistency_score(website_content, social_content, analysis):
    """
    Calculate a brand consistency score based on website and social media content.
    
    Args:
        website_content (dict): Extracted website content
        social_content (list): Social media profiles and content
        analysis (dict): Content analysis results
        
    Returns:
        int: Consistency score from 0-100
    """
    try:
        # Base score starts at 50
        score = 50
        
        # Factor 1: If social media profiles exist and match the brand name
        if social_content and len(social_content) > 0:
            score += min(len(social_content) * 5, 20)  # Up to 20 points for social presence
            
            # Check if social profiles are active (have followers or engagement metrics)
            active_profiles = 0
            for profile in social_content:
                if profile.get("followers") not in [None, "N/A", 0] or profile.get("engagement") not in [None, "Unknown"]:
                    active_profiles += 1
            
            if active_profiles > 0:
                score += min(active_profiles * 3, 15)  # Up to 15 points for active profiles
        
        # Factor 2: Website content quality
        if website_content:
            # Check if website has key brand elements
            if website_content.get("brand_name"):
                score += 5
            if website_content.get("description") and len(website_content.get("description", "")) > 50:
                score += 5
        
        # Factor 3: Sentiment consistency
        if analysis.get("sentiment"):
            sentiment = analysis.get("sentiment", {})
            # If sentiment is fairly consistent (not too extreme in either direction)
            if -0.3 <= sentiment.get("polarity", 0) <= 0.7:
                score += 5
        
        # Ensure score stays within 0-100 range
        score = max(0, min(score, 100))
        
        return score
    
    except Exception as e:
        # Return a default middle score if calculation fails
        return 70
