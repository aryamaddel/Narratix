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
