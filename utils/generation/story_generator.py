def generate_brand_story(brand_name, brand_description, analysis, social_content):
    """
    Generate a brand story based on the provided information.
    
    Args:
        brand_name (str): Name of the brand
        brand_description (str): Brief description of the brand
        analysis (dict): Analysis data containing keywords, tone, values
        social_content (list): Social media content and metrics
        
    Returns:
        str: Markdown formatted brand story
    """
    try:
        # Basic structure for the brand story
        story = f"# {brand_name}: Brand Story\n\n"
        story += "## Overview\n\n"
        story += f"{brand_description}\n\n"
        
        # Add key values section
        story += "## Brand Values\n\n"
        key_values = analysis.get("key_values", [])
        if key_values:
            story += "This brand emphasizes the following core values:\n\n"
            for value in key_values[:5]:  # Limit to top 5 values
                story += f"- **{value}**\n"
            story += "\n"
        
        # Add tone and voice section
        story += "## Brand Tone and Voice\n\n"
        tone_analysis = analysis.get("tone_analysis", {})
        if tone_analysis:
            # Get the top 3 tones by value
            top_tones = sorted(tone_analysis.items(), key=lambda x: x[1], reverse=True)[:3]
            story += "The brand's communication style is characterized by:\n\n"
            for tone, score in top_tones:
                story += f"- **{tone.capitalize()}** tone ({int(score * 100)}%)\n"
            story += "\n"
        
        # Add social media presence if available
        if social_content:
            story += "## Social Media Presence\n\n"
            story += f"{brand_name} maintains an active presence across the following platforms:\n\n"
            for platform in social_content:
                platform_name = platform.get("platform", "").capitalize()
                if platform_name:
                    story += f"- **{platform_name}**\n"
            story += "\n"
        
        # Conclusion
        story += "## Conclusion\n\n"
        story += f"{brand_name} is positioned as a {' and '.join(analysis.get('keywords', ['professional'])[:2])} brand "
        story += "that aims to connect with its audience through consistent messaging and values.\n"
        
        return story
        
    except Exception as e:
        # Provide a simple fallback story in case of errors
        return f"# {brand_name}: Brand Story\n\n## Overview\n\n{brand_description}\n\nThis brand is developing its unique narrative."
