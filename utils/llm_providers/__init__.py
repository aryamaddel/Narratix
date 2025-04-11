import json
from typing import Dict, List, Any, Optional
from .gemini import generate_with_gemini
from .groq import generate_with_groq

def create_brand_story_prompt(brand_name, description, analysis, social_content):
    """Create a condensed prompt for brand story generation"""
    keywords = analysis.get("keywords", [])
    key_values = analysis.get("key_values", [])
    tone_analysis = analysis.get("tone_analysis", {})
    sentiment = analysis.get("sentiment", {})
    
    dominant_tone = max(tone_analysis.items(), key=lambda x: x[1])[0] if tone_analysis else "professional"
    
    # Simplified social platform formatting
    social_data = json.dumps([{
        "platform": p.get("platform", ""),
        "followers": p.get("followers", "N/A")
    } for p in social_content]) if social_content else "Limited channels"
    
    return f"""
    Generate a comprehensive brand story for "{brand_name}".

    Brand Description: {description}

    Key Information:
    - Keywords: {', '.join(keywords[:5]) if keywords else "professional, quality"}
    - Key Values: {', '.join(key_values[:3]) if key_values else "Quality, Innovation"}
    - Dominant Brand Tone: {dominant_tone.capitalize()}
    - Brand Sentiment: {sentiment.get('polarity', 0.0)}, {sentiment.get('subjectivity', 0.0)}

    Social Media: {social_data}

    Format with these markdown sections:
    1. Introduction - "# {brand_name}: Brand Story"
    2. Core Values
    3. Brand Voice & Tone
    4. Social Media Presence
    5. Conclusion
    """

def generate_with_llm(brand_name, description, analysis, social_content):
    """Try to generate content with available LLMs"""
    prompt = create_brand_story_prompt(brand_name, description, analysis, social_content)
    
    # Try providers in sequence
    for generator in [generate_with_gemini, generate_with_groq]:
        try:
            content = generator(prompt)
            if content:
                return content
        except Exception:
            continue
    
    return None

def generate_brand_story(brand_name, description, analysis, social_content):
    """Generate brand story or fall back to simplified version"""
    content = generate_with_llm(brand_name, description, analysis, social_content)
    if content:
        return content
    
    # Fallback to simplified generator
    keywords = analysis.get("keywords", [])[:3]
    key_values = analysis.get("key_values", [])[:3] or ["Quality"]
    tone = analysis.get("tone_analysis", {})
    dominant_tone = max(tone.items(), key=lambda x: x[1])[0] if tone else "professional"
    
    story = [
        f"# {brand_name}: Brand Story\n",
        f"## Introduction\n{brand_name} is focused on {key_values[0].lower()}. {description}\n",
        "## Core Values\n" + "\n".join([f"- **{v}**: A guiding principle" for v in key_values[:3]]) + "\n",
        f"## Brand Voice\n{brand_name} communicates with a {dominant_tone} tone using themes like {', '.join(keywords)}.\n",
        "## Social Media\n" + ("\n".join([f"- **{p['platform']}**: {p.get('followers', 'N/A')} followers" 
                              for p in social_content[:3]]) if social_content else "Limited social media presence.")
    ]
    
    return "\n".join(story)
