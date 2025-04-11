import re
import logging
from typing import Dict, Any, List

# Import Gemini configuration
from utils.core.gemini_setup import GEMINI_AVAILABLE, DEFAULT_MODEL

logger = logging.getLogger(__name__)

def generate_consistency_score(website_content: Dict[str, Any], 
                              social_content: List[Dict[str, Any]],
                              analysis: Dict[str, Any]) -> int:
    """
    Calculate a brand consistency score based on website and social media content
    
    Args:
        website_content: Website content data
        social_content: Social media profiles data
        analysis: Content analysis data
        
    Returns:
        Consistency score (0-100)
    """
    logger.info("Generating brand consistency score")
    # Start with a base score
    score = 70
    
    if GEMINI_AVAILABLE and DEFAULT_MODEL:
        try:
            # Extract social platforms for context with null checks
            platforms = []
            if social_content:
                for social in social_content:
                    if social.get("platform"):
                        platforms.append(social.get("platform"))
            platforms_str = ", ".join(platforms) if platforms else "No social platforms detected"
            
            # Handle null analysis
            keywords = analysis.get("keywords", ["Unknown"]) if analysis else ["Unknown"]
            
            # Use Gemini to calculate a consistency score with the available model
            prompt = f"""
            Calculate a brand consistency score (0-100) based on this information:
            
            Website content detected: {"Yes" if website_content else "Limited or None"}
            Social platforms detected: {platforms_str}
            Keywords identified: {", ".join(keywords)}
            
            Factors to consider:
            1. Presence across multiple platforms
            2. Consistent messaging across platforms
            3. Brand voice clarity
            
            Return only the numeric score (0-100) with no additional text.
            """
            
            # Generate content with Gemini
            import google.generativeai as genai
            model = genai.GenerativeModel(DEFAULT_MODEL)
            logger.debug(f"Sending consistency score prompt to Gemini using model {DEFAULT_MODEL}")
            response = model.generate_content(prompt)
            
            if response and hasattr(response, "text"):
                # Parse the score
                try:
                    score_text = response.text.strip()
                    # Extract just the number
                    score_match = re.search(r'\b(\d{1,3})\b', score_text)
                    if score_match:
                        numeric_score = int(score_match.group(1))
                        # Validate the score is in range
                        if 0 <= numeric_score <= 100:
                            logger.info(f"Generated consistency score with Gemini: {numeric_score}")
                            return numeric_score
                        else:
                            logger.warning(f"Gemini score out of range: {numeric_score}, falling back to manual calculation")
                except Exception as e:
                    logger.error(f"Error parsing Gemini score: {str(e)}")
                    # Continue with calculating score manually
                    pass
        except Exception as e:
            logger.warning(f"Error generating consistency score with Gemini: {str(e)}")
            # Fall back to calculating score manually
            pass
    
    # Manual calculation if Gemini fails or isn't available
    logger.info("Using manual consistency score calculation")
    
    # Adjust score based on social media presence
    if social_content:
        score += min(len(social_content) * 5, 15)  # Up to +15 for social presence
        logger.debug(f"Adjusted score for social presence: +{min(len(social_content) * 5, 15)}")
    else:
        score -= 10  # Penalty for no social presence
        logger.debug("Adjusted score for missing social presence: -10")
    
    # Adjust for content analysis
    if analysis:
        # If we have keywords, that's a good sign
        if analysis.get("keywords") and len(analysis.get("keywords", [])) >= 3:
            score += 5
            logger.debug("Adjusted score for keywords: +5")
            
        # If we have tone analysis, that's also good
        if analysis.get("tone_analysis") and len(analysis.get("tone_analysis", {})) >= 3:
            score += 5
            logger.debug("Adjusted score for tone analysis: +5")
            
        # If we have key values identified
        if analysis.get("key_values") and len(analysis.get("key_values", [])) >= 2:
            score += 5
            logger.debug("Adjusted score for key values: +5")
    else:
        score -= 10  # Penalty for limited analysis
        logger.debug("Adjusted score for limited analysis: -10")
    
    # Ensure score stays within 0-100 range
    final_score = max(0, min(score, 100))
    logger.info(f"Calculated manual consistency score: {final_score}")
    return final_score
