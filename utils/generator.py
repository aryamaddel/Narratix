import random
import os
import json
from typing import Dict, List, Any, Optional
import google.generativeai as genai


# Configure Gemini API if environment variable is set
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        GEMINI_AVAILABLE = True
    except Exception as e:
        GEMINI_AVAILABLE = False
else:
    GEMINI_AVAILABLE = False


def generate_with_gemini(
    brand_name: str,
    description: str,
    analysis: Dict[str, Any],
    social_content: List[Dict[str, Any]],
) -> Optional[str]:
    """Generate a brand story using Google's Gemini AI model"""
    if not GEMINI_AVAILABLE:
        return None

    try:
        # Extract key components from the analysis
        keywords = analysis.get("keywords", [])
        key_values = analysis.get("key_values", [])
        tone_analysis = analysis.get("tone_analysis", {})
        sentiment = analysis.get("sentiment", {})

        # Determine the dominant tone
        dominant_tone = (
            max(tone_analysis.items(), key=lambda x: x[1])[0]
            if tone_analysis
            else "professional"
        )

        # Prepare social media information
        social_platforms = []
        for platform in social_content:
            platform_info = {
                "platform": platform.get("platform", "Unknown"),
                "followers": platform.get("followers", "N/A"),
                "engagement": platform.get("engagement", "Medium"),
                "frequency": platform.get("frequency", "Regular"),
            }
            social_platforms.append(platform_info)

        # Create the prompt for Gemini
        prompt = f"""
        Generate a comprehensive brand story for "{brand_name}".

        Brand Description: {description}

        Key Information:
        - Keywords: {', '.join(keywords) if keywords else "professional, quality, service, innovation"}
        - Key Values: {', '.join(key_values) if key_values else "Quality, Innovation, Customer Focus, Excellence, Integrity"}
        - Dominant Brand Tone: {dominant_tone.capitalize()}
        - Brand Sentiment: Polarity: {sentiment.get('polarity', 0.1)}, Subjectivity: {sentiment.get('subjectivity', 0.3)}

        Social Media Presence: {json.dumps(social_platforms) if social_platforms else "Limited or private channels."}

        Format the brand story with these sections using markdown:
        1. Introduction - Begin with "# {brand_name}: Brand Story" and introduce the brand
        2. Core Values - Describe the key values that define the brand
        3. Brand Voice & Tone - Explain the communication style and key themes/language
        4. Social Media Presence - Detail how the brand engages on different platforms
        5. Conclusion - Summarize the brand's positioning and future vision

        The story should be professional, insightful, and accurately reflect the brand's identity based on the provided information.
        """

        # Generate content with Gemini
        try:
            # Use the specified model name
            model = genai.GenerativeModel("gemini-2.5-pro-exp-03-25")
            response = model.generate_content(prompt)
        except Exception as model_error:
            try:
                # Try with another possible format
                model = genai.GenerativeModel("models/gemini-2.5-pro-exp-03-25")
                response = model.generate_content(prompt)
            except Exception as fallback_error:
                # Try with original format as last resort
                try:
                    model = genai.GenerativeModel("gemini-pro")
                    response = model.generate_content(prompt)
                except Exception as final_error:
                    raise final_error

        # Return the generated story
        if response and hasattr(response, "text"):
            return response.text
        else:
            return None

    except Exception as e:
        return None


def generate_brand_story(brand_name, description, analysis, social_content):
    """Generate a simplified brand story"""
    # Extract keywords and values
    keywords = analysis.get("keywords", [])[:5]
    key_values = analysis.get("key_values", [])[:3]
    
    # Create sections
    intro = f"# {brand_name}: Brand Story\n\n"
    intro += f"## Introduction\n\n{brand_name} is focused on {key_values[0].lower() if key_values else 'quality'}. {description}\n\n"
    
    values = "## Core Values\n\n"
    for i, value in enumerate(key_values[:3]):
        values += f"- **{value}**: A guiding principle for {brand_name}\n"
    values += "\n"
    
    tone = analysis.get("tone_analysis", {})
    dominant_tone = max(tone.items(), key=lambda x: x[1])[0] if tone else "professional" 
    
    voice = f"## Brand Voice\n\n{brand_name} communicates with a {dominant_tone} tone, "
    voice += f"using themes like {', '.join(keywords[:3])}.\n\n"
    
    social = "## Social Media\n\n"
    if social_content:
        for platform in social_content[:3]:
            platform_name = platform.get("platform", "")
            followers = platform.get("followers", "N/A")
            social += f"- **{platform_name}**: {followers} followers\n"
    else:
        social += "Limited social media presence detected.\n"
    
    return intro + values + voice + social

def generate_visual_profile(analysis):
    """Generate a simple visual profile"""
    return {
        "color_palette": {
            "primary": "#0A3D62",  # Dark blue
            "secondary": "#3E92CC", # Medium blue
            "accent": "#D8D8D8",    # Light gray
        },
        "font_style": {
            "heading": "Montserrat",
            "body": "Open Sans",
        },
        "tone_indicators": [
            {"name": tone.capitalize(), "value": round(value, 2)}
            for tone, value in sorted(
                analysis.get("tone_analysis", {}).items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
        ]
    }

def generate_consistency_score(website_content, social_content, analysis):
    """Generate a simple consistency score between 65-85"""
    return 75  # Fixed value for simplicity
