import re
import json
import logging
from typing import Dict, Any

# Import Gemini configuration
from utils.core.gemini_setup import GEMINI_AVAILABLE, DEFAULT_MODEL

logger = logging.getLogger(__name__)

def generate_visual_profile(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate visual profile recommendations based on content analysis
    
    Args:
        analysis: Content analysis data
        
    Returns:
        Visual profile recommendations
    """
    logger.info("Generating visual profile recommendations")
    # Default visual profile
    default_profile = {
        "color_palette": {
            "primary": "#0A3D62",
            "secondary": "#3E92CC",
            "accent": "#D8D8D8",
            "neutral": "#F5F5F5",
            "highlight": "#2E86AB",
        },
        "font_style": {
            "heading": "Montserrat or Georgia",
            "body": "Open Sans or Roboto",
            "style": "Clean, structured typography with proper hierarchy",
        },
        "image_style": "Polished, high-quality photography with clean compositions.",
        "tone_indicators": [
            {"name": "Professional", "value": 0.7},
            {"name": "Informative", "value": 0.6},
            {"name": "Friendly", "value": 0.4},
        ],
    }
    
    if GEMINI_AVAILABLE and DEFAULT_MODEL:
        try:
            # Extract tone information with null check
            tone = analysis.get("tone_analysis", {}) if analysis else {}
            tone_str = ", ".join([f"{k}: {v:.1f}" for k, v in tone.items()]) if tone else "Professional: 0.7, Informative: 0.6"
            
            # Extract keywords and values with null checks
            keywords = ", ".join(analysis.get("keywords", ["professional", "quality"]) if analysis else ["professional", "quality"])
            values = ", ".join(analysis.get("key_values", ["Quality", "Service"]) if analysis else ["Quality", "Service"])
            
            # Use Gemini to generate visual profile recommendations with the available model
            prompt = f"""
            Create a visual brand profile based on these brand characteristics:
            - Tone profile: {tone_str}
            - Keywords: {keywords}
            - Key values: {values}
            
            Provide recommendations for:
            1. Color palette (primary, secondary, accent, neutral, and highlight colors as hex codes)
            2. Font style (heading font, body font, and overall typography style)
            3. Image style guidance
            4. Top 3 tone indicators with values from 0-1
            
            Format response as JSON with this structure:
            {{
                "color_palette": {{
                    "primary": "#hex",
                    "secondary": "#hex",
                    "accent": "#hex",
                    "neutral": "#hex",
                    "highlight": "#hex"
                }},
                "font_style": {{
                    "heading": "font names",
                    "body": "font names",
                    "style": "description"
                }},
                "image_style": "description",
                "tone_indicators": [
                    {{"name": "tone1", "value": 0.x}},
                    {{"name": "tone2", "value": 0.x}},
                    {{"name": "tone3", "value": 0.x}}
                ]
            }}
            """
            
            # Generate content with Gemini
            import google.generativeai as genai
            model = genai.GenerativeModel(DEFAULT_MODEL)
            logger.debug(f"Sending visual profile prompt to Gemini using model {DEFAULT_MODEL}")
            response = model.generate_content(prompt)
            
            if response and hasattr(response, "text"):
                logger.debug("Received response from Gemini API")
                # Parse the JSON response
                try:
                    # Extract JSON from the response text
                    json_str = response.text.strip()
                    # Handle case where response might have markdown code block
                    if "```json" in json_str:
                        json_str = json_str.split("```json")[1].split("```")[0].strip()
                    elif "```" in json_str:
                        json_str = json_str.split("```")[1].split("```")[0].strip()
                        
                    visual_profile = json.loads(json_str)
                    logger.info("Successfully generated visual profile with Gemini")
                    return visual_profile
                except Exception as e:
                    logger.error(f"Error parsing Gemini response: {str(e)}")
                    # Return default if JSON parsing fails
                    return default_profile
            else:
                logger.error("Empty or invalid response from Gemini API")
                return default_profile
                
        except Exception as e:
            logger.warning(f"Error generating visual profile: {str(e)}, using default")
            # Fall back to the default profile
            return default_profile
    
    # Return the default profile if Gemini isn't available
    logger.info("Using default visual profile (Gemini unavailable or failed)")
    return default_profile
