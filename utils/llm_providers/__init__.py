import json
from typing import Dict, List, Any, Optional

# Import the LLM providers
from .gemini import generate_with_gemini, is_available as gemini_available
from .groq import generate_with_groq, is_available as groq_available

def create_brand_story_prompt(
    brand_name: str,
    description: str,
    analysis: Dict[str, Any],
    social_content: List[Dict[str, Any]],
) -> str:
    """Create a prompt for brand story generation that can be used with any LLM"""
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

    # Create the prompt for any LLM
    return f"""
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

def generate_with_llm(
    brand_name: str,
    description: str,
    analysis: Dict[str, Any],
    social_content: List[Dict[str, Any]],
) -> Optional[str]:
    """Generate content using available LLM providers with fallbacks"""
    
    # Create the prompt that works for any model
    prompt = create_brand_story_prompt(brand_name, description, analysis, social_content)
    
    # Try Gemini first if available
    if gemini_available():
        content = generate_with_gemini(prompt)
        if content:
            return content
    
    # Try Groq if available
    if groq_available():
        content = generate_with_groq(prompt)
        if content:
            return content
    
    # If all LLMs fail, return None to indicate failure
    return None

def generate_brand_story(brand_name, description, analysis, social_content):
    """Generate a brand story using available LLMs or fall back to the simplified version"""
    # Try to generate with LLM
    llm_content = generate_with_llm(brand_name, description, analysis, social_content)
    
    # If LLM generation succeeded, return that
    if llm_content:
        return llm_content
        
    # Otherwise, use the simplified generator
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
