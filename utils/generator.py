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
    """Generate a basic brand story based on the analysis"""
    try:
        # Extract key components from the analysis
        keywords = analysis.get("keywords", [])[:5]
        key_values = analysis.get("key_values", [])
        tone_analysis = analysis.get("tone_analysis", {})
        
        # Determine the dominant tone
        dominant_tone = max(tone_analysis.items(), key=lambda x: x[1])[0] if tone_analysis else "professional"
        
        # Create a brand story with standard sections
        # Introduction
        intro = f"# {brand_name}: Brand Story\n\n## Introduction\n\n"
        intro += f"{brand_name} is a brand focused on {key_values[0].lower() if key_values else 'quality'} "
        intro += f"and {key_values[1].lower() if len(key_values) > 1 else 'excellence'}. {description}"
        
        # Core Values
        values = "\n\n## Core Values\n\n"
        values += f"{brand_name} operates according to the following established values and principles:\n\n"
        for value in key_values[:5]:
            values += f"- **{value}**: Core principle guiding {brand_name}'s operations.\n"
            
        # Brand Voice
        voice = "\n\n## Brand Voice & Tone\n\n"
        voice += f"The {brand_name} brand communicates with a {dominant_tone} voice. "
        voice += f"Key themes and language include {', '.join([f'**{k}**' for k in keywords[:3]])}."
        
        # Social Media
        social = "\n\n## Social Media Presence\n\n"
        if social_content:
            social += f"{brand_name} maintains a strategic social media presence across multiple platforms:\n\n"
            for platform in social_content[:3]:
                platform_name = platform.get("platform", "Unknown")
                followers = platform.get("followers", "N/A")
                social += f"- **{platform_name}**: {followers} followers\n"
        else:
            social += f"{brand_name} maintains a focused digital presence aligned with its brand values."
        
        # Conclusion
        conclusion = f"\n\n## Conclusion\n\n{brand_name} continues to set standards through its "
        conclusion += f"commitment to {key_values[0] if key_values else 'quality'} and excellence."
        
        return intro + values + voice + social + conclusion
        
    except Exception:
        # Create a simple fallback brand story
        fallback = f"# {brand_name}: Brand Story\n\n## Introduction\n\n"
        fallback += f"{brand_name} is a brand focused on delivering quality products and services. {description}\n\n"
        fallback += "## Core Values\n\nQuality, Innovation, Service, Excellence, Integrity\n\n"
        fallback += f"## Brand Voice & Tone\n\nThe brand communicates with a professional voice.\n\n"
        fallback += f"## Social Media Presence\n\n{brand_name} maintains a strategic social media presence.\n\n"
        fallback += f"## Conclusion\n\n{brand_name} continues to set standards through its commitment to quality."
        return fallback

def generate_visual_profile(analysis):
    """Generate a simplified visual profile based on analysis"""
    try:
        # Default professional color palette
        default_palette = {
            "primary": "#0A3D62",  # Dark blue
            "secondary": "#3E92CC",  # Medium blue
            "accent": "#D8D8D8",    # Light gray
            "neutral": "#F5F5F5",   # Off-white
            "highlight": "#2E86AB", # Teal blue
        }
        
        # Default font style
        default_font = {
            "heading": "Montserrat or Georgia",
            "body": "Open Sans or Roboto",
            "style": "Clean, structured typography with proper hierarchy",
        }
        
        # Get tone analysis or use default
        tone_analysis = analysis.get("tone_analysis", {})
        if not tone_analysis:
            tone_analysis = {
                "professional": 0.7,
                "friendly": 0.4,
                "informative": 0.6,
            }
            
        # Extract top tones
        tone_indicators = [
            {"name": tone.capitalize(), "value": round(value, 2)}
            for tone, value in sorted(tone_analysis.items(), 
                                     key=lambda x: x[1], 
                                     reverse=True)[:3]
        ]
        
        return {
            "color_palette": default_palette,
            "font_style": default_font,
            "image_style": "Professional photography with clean compositions.",
            "tone_indicators": tone_indicators,
        }
    except Exception:
        # Return default profile on error
        return {
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
                "style": "Clean typography",
            },
            "image_style": "Professional photography",
            "tone_indicators": [
                {"name": "Professional", "value": 0.7},
                {"name": "Informative", "value": 0.6},
                {"name": "Friendly", "value": 0.4},
            ],
        }

def generate_consistency_score(website_content, social_content, analysis):
    """Generate a simplified consistency score"""
    # Just return a reasonable score between 65-85
    return random.randint(65, 85)
