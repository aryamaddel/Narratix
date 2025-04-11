def generate_visual_profile(analysis):
    """Generate a simple visual profile with a dark theme"""
    return {
        "color_palette": {
            "primary": "#8A78EE",  # Purple
            "secondary": "#6c63a3",  # Darker purple
            "accent": "#f87171",  # Red
        },
        "font_style": {
            "heading": "Poppins",
            "body": "Poppins",
            "style": "Clean with medium contrast for dark backgrounds",
        },
        "tone_indicators": [
            {"name": tone.capitalize(), "value": round(value, 2)}
            for tone, value in sorted(
                analysis.get("tone_analysis", {}).items(),
                key=lambda x: x[1],
                reverse=True,
            )[:3]
        ],
        "image_style": "High contrast imagery with bold colors that stand out against dark backgrounds",
    }


def generate_consistency_score(website_content, social_content, analysis):
    """Generate a simple consistency score between 65-85"""
    return 75  # Fixed value for simplicity
