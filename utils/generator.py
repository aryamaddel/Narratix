import logging
import random
import re
import os
import json
from typing import Dict, List, Any, Optional
import google.generativeai as genai

logger = logging.getLogger(__name__)

# Configure Gemini API if environment variable is set
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        GEMINI_AVAILABLE = True
        logger.info("Gemini API configured successfully")
    except Exception as e:
        logger.error(f"Failed to configure Gemini API: {str(e)}")
        GEMINI_AVAILABLE = False
else:
    GEMINI_AVAILABLE = False
    logger.warning("Gemini API key not found in environment variables")


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
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)

        # Return the generated story
        if response and hasattr(response, "text"):
            return response.text
        else:
            logger.warning("Gemini returned an invalid response")
            return None

    except Exception as e:
        logger.error(f"Error generating brand story with Gemini: {str(e)}")
        return None


def generate_brand_story(brand_name, description, analysis, social_content):
    """Generate a compelling brand story based on the analysis"""
    try:
        # Try to generate with Gemini first if available
        if GEMINI_AVAILABLE:
            gemini_story = generate_with_gemini(
                brand_name, description, analysis, social_content
            )
            if gemini_story:
                logger.info("Successfully generated brand story using Gemini AI")
                return gemini_story
            else:
                logger.warning(
                    "Gemini AI generation failed, falling back to rule-based generation"
                )

        # Extract key components from the analysis
        keywords = analysis.get("keywords", [])
        key_values = analysis.get("key_values", [])
        tone_analysis = analysis.get("tone_analysis", {})
        sentiment = analysis.get("sentiment", {})

        # Apply default values if any component is missing
        if not keywords:
            keywords = [
                "professional",
                "quality",
                "service",
                "experience",
                "innovation",
            ]

        if not key_values:
            key_values = [
                "Quality",
                "Innovation",
                "Customer Focus",
                "Excellence",
                "Integrity",
            ]

        if not tone_analysis:
            tone_analysis = {
                "professional": 0.7,
                "friendly": 0.4,
                "informative": 0.6,
                "enthusiastic": 0.3,
                "formal": 0.5,
            }

        # Determine the dominant tone
        dominant_tone = max(tone_analysis.items(), key=lambda x: x[1])[0]

        # Validate and clean brand name
        if not brand_name:
            brand_name = "Brand"

        # Clean and validate description
        if not description:
            description = f"{brand_name} is a professional organization providing quality products and services."

        # Create sections for the brand story
        brand_intro = generate_brand_intro(
            brand_name, description, key_values, dominant_tone
        )
        brand_values = generate_brand_values(brand_name, key_values, dominant_tone)
        brand_voice = generate_brand_voice(dominant_tone, tone_analysis, keywords)
        social_presence = generate_social_presence(brand_name, social_content)
        brand_conclusion = generate_brand_conclusion(
            brand_name, key_values, dominant_tone
        )

        # Combine all sections into the final brand story
        brand_story = f"{brand_intro}\n\n{brand_values}\n\n{brand_voice}\n\n{social_presence}\n\n{brand_conclusion}"

        return brand_story

    except Exception as e:
        logger.error(f"Error generating brand story: {str(e)}")

        # Create a simple fallback brand story
        fallback_brand_story = f"""# {brand_name}: Brand Story

## Introduction

{brand_name} is a brand focused on delivering quality products and services. {description}

## Core Values

{brand_name} operates according to the following established values and principles:

- **Quality**: Delivering exceptional products/services that exceed expectations.
- **Innovation**: Pioneering new approaches and solutions.
- **Excellence**: Striving for outstanding performance in all operations.
- **Integrity**: Maintaining honesty and ethical standards in all business practices.
- **Customer Focus**: Putting the needs and satisfaction of customers at the center of every decision.

## Brand Voice & Tone

The brand communicates with a professional voice that inspires confidence. Key themes and language include **quality**, **innovation**, **service**, **excellence** and **solutions**.

## Social Media Presence

{brand_name} maintains a strategic social media presence to engage with its audience across multiple platforms.

## Conclusion

{brand_name} continues to set industry standards through its unwavering commitment to quality and strategic vision, positioning itself as a trusted authority in its field.
"""
        return fallback_brand_story


def generate_brand_intro(brand_name, description, key_values, tone):
    """Generate the introduction section of the brand story"""
    try:
        # Ensure we have at least 2 values for formatting
        if len(key_values) < 2:
            key_values = key_values + ["Excellence", "Quality"]

        # Create a compelling opening based on the dominant tone
        openings = {
            "professional": [
                f"{brand_name} is a distinguished player in the industry, known for its commitment to {key_values[0]} and {key_values[1]}.",
                f"As a leader in its field, {brand_name} has established a reputation built on {key_values[0]} and {key_values[1]}.",
                f"{brand_name} represents the pinnacle of excellence in its sector, emphasizing {key_values[0]} in all aspects of operation.",
            ],
            "friendly": [
                f"Meet {brand_name}, a brand that feels like a friend – approachable, reliable, and all about {key_values[0]}.",
                f"{brand_name} is where community meets {key_values[0]}, creating a space where customers feel valued and understood.",
                f"The story of {brand_name} is one of connection and {key_values[0]}, built on genuine relationships with its community.",
            ],
            "informative": [
                f"{brand_name} provides comprehensive solutions centered around {key_values[0]} and {key_values[1]}, addressing key market needs.",
                f"Founded on principles of {key_values[0]}, {brand_name} offers data-driven approaches to solve complex challenges.",
                f"{brand_name} delivers insights and expertise in its field, with a strong foundation in {key_values[0]}.",
            ],
            "enthusiastic": [
                f"{brand_name} is passionate about {key_values[0]}! Every aspect of the brand radiates enthusiasm and energy.",
                f"With boundless energy and commitment to {key_values[0]}, {brand_name} stands out as a vibrant force in its industry.",
                f"{brand_name} brings excitement to {key_values[0]}, transforming everyday experiences into something extraordinary!",
            ],
            "formal": [
                f"{brand_name} operates with the utmost adherence to {key_values[0]} and {key_values[1]}, maintaining rigorous standards.",
                f"In accordance with its principles of {key_values[0]}, {brand_name} delivers consistent, reliable services to its clientele.",
                f"{brand_name} maintains a distinguished presence in its sector, characterized by unwavering commitment to {key_values[0]}.",
            ],
        }

        # Select an opening based on the dominant tone (with fallback)
        opening = random.choice(openings.get(tone, openings["informative"]))

        # Clean and use the provided description
        clean_description = description.strip()
        if not clean_description.endswith((".", "!", "?")):
            clean_description += "."

        # Create the introduction paragraph
        intro = f"# {brand_name}: Brand Story\n\n## Introduction\n\n{opening} {clean_description}"

        return intro
    except Exception as e:
        logger.warning(f"Error generating introduction: {str(e)}")
        return f"# {brand_name}: Brand Story\n\n## Introduction\n\n{brand_name} is a professional organization known for quality products and services. {description}"


def generate_brand_values(brand_name, key_values, tone):
    """Generate the values section of the brand story"""
    try:
        # Create a section on brand values
        section_intros = {
            "professional": f"The core philosophy of {brand_name} is built upon several key principles that guide all business decisions and interactions:",
            "friendly": f"Here's what {brand_name} truly cares about – the values that make this brand special:",
            "informative": f"{brand_name} operates according to the following established values and principles:",
            "enthusiastic": f"{brand_name} is driven by these exciting and powerful values:",
            "formal": f"The operational ethos of {brand_name} is predicated upon the following foundational principles:",
        }

        # Select a section intro based on the dominant tone
        section_intro = section_intros.get(tone, section_intros["informative"])

        # Value descriptions based on common key values
        value_descriptions = {
            "Quality": f"Delivering exceptional {brand_name} products/services that exceed expectations.",
            "Innovation": f"Pioneering new approaches and solutions that keep {brand_name} at the cutting edge.",
            "Customer Focus": f"Putting the needs and satisfaction of {brand_name} customers at the center of every decision.",
            "Excellence": f"Striving for outstanding performance in all aspects of {brand_name}'s operations.",
            "Integrity": f"Maintaining honesty and ethical standards in all {brand_name} business practices.",
            "Sustainability": f"Ensuring {brand_name}'s operations contribute positively to environmental and social wellbeing.",
            "Creativity": f"Fostering original thinking and artistic approaches throughout {brand_name}'s work.",
            "Reliability": f"Being consistently dependable in {brand_name}'s services and communications.",
            "Trust": f"Building strong, credible relationships with all {brand_name} stakeholders.",
            "Community": f"Creating and nurturing a sense of belonging among {brand_name}'s customers and team members.",
            "Service": f"Delivering exceptional support and assistance to {brand_name}'s customers.",
            "Accountability": f"Taking responsibility for actions and outcomes across all {brand_name} operations.",
            "Teamwork": f"Collaborating effectively to achieve {brand_name}'s goals through shared effort.",
            "Leadership": f"Guiding the industry forward through {brand_name}'s vision and example.",
            "Expertise": f"Maintaining deep knowledge and skill in {brand_name}'s area of specialization.",
        }

        # Create bullet points for each value
        value_points = []
        for value in key_values:
            # Get a description if available, otherwise create a generic one
            if value in value_descriptions:
                description = value_descriptions[value]
            else:
                description = f"Emphasis on {value.lower()} as a guiding principle in {brand_name}'s approach."

            value_points.append(f"- **{value}**: {description}")

        # Ensure we have at least 3 value points
        if len(value_points) < 3:
            default_values = [
                "Quality",
                "Innovation",
                "Customer Focus",
                "Excellence",
                "Integrity",
            ]
            for value in default_values:
                if value not in key_values:
                    description = value_descriptions[value]
                    value_points.append(f"- **{value}**: {description}")
                if len(value_points) >= 5:
                    break

        # Combine into values section
        values_section = f"## Core Values\n\n{section_intro}\n\n" + "\n".join(
            value_points
        )

        return values_section
    except Exception as e:
        logger.warning(f"Error generating values section: {str(e)}")
        return f"## Core Values\n\n{brand_name} is guided by the following principles:\n\n- **Quality**: Delivering exceptional products and services.\n- **Innovation**: Pioneering new approaches and solutions.\n- **Customer Focus**: Putting customers at the center of every decision."


def generate_brand_voice(tone, tone_analysis, keywords):
    """Generate the brand voice section of the brand story"""
    try:
        # Create a section on brand voice and tone
        voice_intros = {
            "professional": "The brand communicates with a polished, authoritative voice that inspires confidence.",
            "friendly": "The brand speaks in a warm, approachable manner that makes connections with its audience.",
            "informative": "The brand presents information clearly and helpfully, focusing on educational content.",
            "enthusiastic": "The brand expresses itself with energy and passion, creating excitement around its message.",
            "formal": "The brand maintains a sophisticated, structured communication style that conveys expertise.",
        }

        # Select a voice intro based on the dominant tone
        voice_intro = voice_intros.get(tone, voice_intros["informative"])

        # Add details about secondary tones
        secondary_tones = []
        for t, value in tone_analysis.items():
            if t != tone and value > 0.3:  # Only include significant secondary tones
                if t == "professional":
                    secondary_tones.append("professional confidence")
                elif t == "friendly":
                    secondary_tones.append("approachable warmth")
                elif t == "informative":
                    secondary_tones.append("helpful clarity")
                elif t == "enthusiastic":
                    secondary_tones.append("energetic passion")
                elif t == "formal":
                    secondary_tones.append("structured sophistication")

        secondary_tone_text = ""
        if secondary_tones:
            if len(secondary_tones) == 1:
                secondary_tone_text = (
                    f"This is balanced with notes of {secondary_tones[0]}."
                )
            else:
                secondary_tone_text = (
                    f"This is balanced with notes of {' and '.join(secondary_tones)}."
                )

        # Key themes and language
        themes_text = "Key themes and language that define the brand include:"

        # Select some keywords as themes (use 5-7 keywords)
        selected_keywords = []
        if keywords:
            selected_count = min(6, len(keywords))
            selected_keywords = random.sample(keywords, selected_count)
        else:
            selected_keywords = [
                "quality",
                "professional",
                "service",
                "excellence",
                "innovation",
            ]

        keywords_text = ", ".join([f"**{k}**" for k in selected_keywords])

        # Combine into voice section
        voice_section = f"## Brand Voice & Tone\n\n{voice_intro} {secondary_tone_text}\n\n{themes_text}\n\n{keywords_text}"

        return voice_section
    except Exception as e:
        logger.warning(f"Error generating voice section: {str(e)}")
        return "## Brand Voice & Tone\n\nThe brand communicates with a professional voice that inspires confidence while remaining approachable. Key themes include **quality**, **service**, and **expertise**."


def generate_social_presence(brand_name, social_content):
    """Generate the social media presence section of the brand story"""
    try:
        if not social_content:
            return f"## Social Media Presence\n\n{brand_name} maintains a limited social media presence or uses private channels for client communication."

        # Create a section on social media presence
        social_intro = f"## Social Media Presence\n\n{brand_name} engages with its audience across multiple social platforms, each with a distinct approach:"

        # Generate details for each platform
        platform_details = []

        for platform in social_content:
            platform_name = platform.get("platform", "Unknown")
            followers = platform.get("followers", "N/A")
            engagement = platform.get("engagement", "Medium")
            frequency = platform.get("frequency", "Regular")

            # Create platform-specific descriptions
            if platform_name.lower() == "facebook":
                detail = f"- **{platform_name}**: Maintains a {engagement.lower()} engagement community of {followers} followers with {frequency.lower()} updates focusing on community building and detailed content."
            elif platform_name.lower() == "twitter":
                detail = f"- **{platform_name}**: Engages {followers} followers with {frequency.lower()} posts, achieving {engagement.lower()} engagement through timely industry insights and conversations."
            elif platform_name.lower() == "instagram":
                detail = f"- **{platform_name}**: Showcases visual content to {followers} followers with {engagement.lower()} engagement, posting {frequency.lower()} to highlight brand aesthetics."
            elif platform_name.lower() == "linkedin":
                detail = f"- **{platform_name}**: Connects with {followers} professional followers, sharing industry expertise and company updates {frequency.lower()} with {engagement.lower()} industry engagement."
            elif platform_name.lower() == "youtube":
                detail = f"- **{platform_name}**: Offers video content to {followers} subscribers with {frequency.lower()} uploads, generating {engagement.lower()} viewer engagement through informative and demonstrative content."
            elif platform_name.lower() == "tiktok":
                detail = f"- **{platform_name}**: Creates trend-focused content for {followers} followers with {engagement.lower()} engagement rates, posting {frequency.lower()} to reach younger demographics."
            else:
                detail = f"- **{platform_name}**: Maintains a presence with approximately {followers} followers, posting {frequency.lower()} with {engagement.lower()} audience engagement."

            platform_details.append(detail)

        # Add strategic insights based on the platform mix
        strategy_insights = "\n\nThe social media strategy reflects the brand's priorities and audience targeting:"

        # Determine dominant platforms
        has_visual = any(
            p.get("platform", "").lower() in ["instagram", "tiktok", "pinterest"]
            for p in social_content
        )
        has_professional = any(
            p.get("platform", "").lower() in ["linkedin"] for p in social_content
        )
        has_content = any(
            p.get("platform", "").lower() in ["youtube", "medium"]
            for p in social_content
        )

        strategy_points = []

        if has_visual:
            strategy_points.append(
                "- Strong visual identity and aesthetic appeal to engage visually-oriented audiences"
            )
        if has_professional:
            strategy_points.append(
                "- Focus on industry expertise and professional networking"
            )
        if has_content:
            strategy_points.append(
                "- Investment in longer-form educational and informative content"
            )
        if len(social_content) >= 3:
            strategy_points.append(
                "- Multi-platform approach to reach diverse audience segments"
            )
        else:
            strategy_points.append(
                "- Targeted platform selection to focus resources on key audience channels"
            )

        # If no specific insights, add a general one
        if not strategy_points:
            strategy_points.append(
                "- Strategic platform selection aligned with the brand's communication goals and target audience"
            )

        # Combine into social media section
        social_presence = (
            f"{social_intro}\n\n"
            + "\n".join(platform_details)
            + f"{strategy_insights}\n\n"
            + "\n".join(strategy_points)
        )

        return social_presence
    except Exception as e:
        logger.warning(f"Error generating social presence section: {str(e)}")
        return f"## Social Media Presence\n\n{brand_name} maintains a strategic social media presence across key platforms, engaging with audiences in a way that reflects the brand's values and communication style."


def generate_brand_conclusion(brand_name, key_values, tone):
    """Generate the conclusion section of the brand story"""
    try:
        # Ensure we have at least one value for formatting
        primary_value = key_values[0] if key_values else "Quality"

        # Create a conclusion based on the dominant tone
        conclusions = {
            "professional": f"{brand_name} continues to set industry standards through its unwavering commitment to {primary_value} and strategic vision, positioning itself as a trusted authority in its field.",
            "friendly": f"{brand_name} thrives on building genuine connections and creating a community united by shared values of {primary_value}, making every interaction meaningful and personal.",
            "informative": f"{brand_name} remains dedicated to providing valuable insights and solutions, consistently delivering on its promise of {primary_value} to meet the evolving needs of its market.",
            "enthusiastic": f"{brand_name} continues to bring energy and innovation to everything it does, inspiring its audience with a passionate commitment to {primary_value} and creating excitement at every touchpoint!",
            "formal": f"{brand_name} maintains its esteemed position through rigorous adherence to {primary_value} and methodical excellence, ensuring consistent delivery of superior outcomes.",
        }

        # Select a conclusion based on the dominant tone
        conclusion = conclusions.get(tone, conclusions["informative"])

        # Add a forward-looking statement
        future_statements = [
            f"As the brand evolves, its foundation in {' and '.join(key_values[:2]) if len(key_values) >= 2 else primary_value} will continue to guide its path forward.",
            f"Looking ahead, {brand_name} is well-positioned to build on these core strengths while adapting to new market opportunities.",
            f"The future trajectory of {brand_name} will be shaped by its established values while embracing innovation and growth.",
        ]

        future = random.choice(future_statements)

        # Combine into conclusion section
        conclusion_section = f"## Conclusion\n\n{conclusion} {future}"

        return conclusion_section
    except Exception as e:
        logger.warning(f"Error generating conclusion section: {str(e)}")
        return f"## Conclusion\n\n{brand_name} continues to set industry standards through its unwavering commitment to quality and strategic vision, positioning itself as a trusted authority in its field."


def generate_visual_profile(analysis):
    """Generate a visual profile based on the content analysis"""
    try:
        # Extract key components from the analysis
        tone_analysis = analysis.get("tone_analysis", {})
        sentiment = analysis.get("sentiment", {})
        key_values = analysis.get("key_values", [])

        # Default values if analysis components are missing
        if not tone_analysis:
            tone_analysis = {
                "professional": 0.7,
                "friendly": 0.4,
                "informative": 0.6,
                "enthusiastic": 0.3,
                "formal": 0.5,
            }

        # Generate color palette suggestion based on brand tone
        dominant_tone = max(tone_analysis.items(), key=lambda x: x[1])[0]

        color_palettes = {
            "professional": {
                "primary": "#0A3D62",  # Dark blue
                "secondary": "#3E92CC",  # Medium blue
                "accent": "#D8D8D8",  # Light gray
                "neutral": "#F5F5F5",  # Off-white
                "highlight": "#2E86AB",  # Teal blue
            },
            "friendly": {
                "primary": "#5E8C61",  # Forest green
                "secondary": "#98B06F",  # Soft green
                "accent": "#F9C846",  # Warm yellow
                "neutral": "#F8F4E3",  # Cream
                "highlight": "#FF9B42",  # Orange
            },
            "informative": {
                "primary": "#3A6EA5",  # Medium blue
                "secondary": "#004E98",  # Dark blue
                "accent": "#FF6700",  # Orange
                "neutral": "#F0F0F0",  # Light gray
                "highlight": "#C0C0C0",  # Silver
            },
            "enthusiastic": {
                "primary": "#E63946",  # Bright red
                "secondary": "#F85A3E",  # Coral
                "accent": "#FFD166",  # Yellow
                "neutral": "#F1FAEE",  # Off-white
                "highlight": "#06D6A0",  # Teal
            },
            "formal": {
                "primary": "#2D3142",  # Dark navy
                "secondary": "#4F5D75",  # Slate blue
                "accent": "#7A6C5D",  # Warm brown
                "neutral": "#EAE8DC",  # Soft beige
                "highlight": "#7A9E7E",  # Sage green
            },
        }

        # Select palette based on dominant tone
        selected_palette = color_palettes.get(
            dominant_tone, color_palettes["informative"]
        )

        # Font style suggestion based on tone
        font_styles = {
            "professional": {
                "heading": "Montserrat or Georgia",
                "body": "Open Sans or Roboto",
                "style": "Clean, structured typography with proper hierarchy",
            },
            "friendly": {
                "heading": "Quicksand or Nunito",
                "body": "Lato or Source Sans Pro",
                "style": "Rounded, approachable fonts with open spacing",
            },
            "informative": {
                "heading": "Roboto Slab or Merriweather",
                "body": "Roboto or Noto Sans",
                "style": "Clear, readable typography with strong contrast",
            },
            "enthusiastic": {
                "heading": "Poppins or Futura",
                "body": "Montserrat or Avenir",
                "style": "Bold, dynamic typography with playful accents",
            },
            "formal": {
                "heading": "Playfair Display or Garamond",
                "body": "EB Garamond or Libre Baskerville",
                "style": "Classic, refined typography with elegant details",
            },
        }

        # Select font style based on dominant tone
        selected_font = font_styles.get(dominant_tone, font_styles["informative"])

        # Image style suggestion based on values and tone
        image_styles = {
            "professional": "Polished, high-quality photography with clean compositions and professional settings.",
            "friendly": "Authentic, candid imagery featuring people, real situations, and warm lighting.",
            "informative": "Clear, explanatory visuals with data visualization and educational content.",
            "enthusiastic": "Vibrant, high-energy images with bold colors and dynamic compositions.",
            "formal": "Classic, elegant imagery with refined compositions and subdued color palettes.",
        }

        # Select image style based on dominant tone
        selected_image = image_styles.get(dominant_tone, image_styles["informative"])

        # Tone indicators for visual profile
        tone_indicators = []
        for tone, value in tone_analysis.items():
            if value > 0.3:  # Only include significant tones
                tone_indicators.append(
                    {"name": tone.capitalize(), "value": round(value, 2)}
                )

        # Sort tone indicators by value (descending)
        tone_indicators.sort(key=lambda x: x["value"], reverse=True)

        # Return the visual profile
        return {
            "color_palette": selected_palette,
            "font_style": selected_font,
            "image_style": selected_image,
            "tone_indicators": tone_indicators,
        }
    except Exception as e:
        logger.error(f"Error generating visual profile: {str(e)}")

        # Return default visual profile
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
                "style": "Clean, structured typography with proper hierarchy",
            },
            "image_style": "Polished, high-quality photography with clean compositions and professional settings.",
            "tone_indicators": [
                {"name": "Professional", "value": 0.7},
                {"name": "Informative", "value": 0.6},
                {"name": "Friendly", "value": 0.4},
            ],
        }


def generate_consistency_score(website_content, social_content, analysis):
    """Generate a consistency score for the brand across platforms"""
    try:
        # Base score
        score = 70  # Start with a decent base score

        # Check if brand has social media presence
        if social_content:
            score += 5
        else:
            score -= 10

        # Check for consistent brand name
        brand_name = website_content.get("brand_name", "")
        name_consistency = True

        if brand_name:
            for social in social_content:
                content = social.get("content", "").lower()
                # Check if brand name appears in social content (allowing for some variation)
                if brand_name.lower() not in content and brand_name.lower().replace(
                    " ", ""
                ) not in content.replace(" ", ""):
                    name_consistency = False
                    break

            if name_consistency:
                score += 10
            else:
                score -= 5

        # Check for content volume and description
        if len(website_content.get("content", "")) > 1000:
            score += 5
        else:
            score -= 5

        if website_content.get("description", ""):
            score += 5
        else:
            score -= 5

        # Check for tone consistency
        tone_analysis = analysis.get("tone_analysis", {})
        if tone_analysis:
            # If one tone is clearly dominant (50% higher than others)
            dominant_tone = max(tone_analysis.items(), key=lambda x: x[1])
            if dominant_tone[1] > 0.6:
                score += 5

            # If tones are more balanced (less clear brand voice)
            if len([t for t, v in tone_analysis.items() if v > 0.5]) > 2:
                score -= 5

        # Adjust based on sentiment consistency
        sentiment = analysis.get("sentiment", {})
        sentiment_values = []

        if "polarity" in sentiment:
            sentiment_values.append(sentiment["polarity"])

        # Check sentiment in social content
        for social in social_content:
            content = social.get("content", "")
            if content:
                # Simple sentiment check (can be enhanced with actual NLP)
                positive_words = [
                    "good",
                    "great",
                    "excellent",
                    "amazing",
                    "best",
                    "love",
                ]
                negative_words = ["bad", "poor", "terrible", "awful", "worst", "hate"]

                content_lower = content.lower()
                positive_count = sum(
                    1 for word in positive_words if word in content_lower
                )
                negative_count = sum(
                    1 for word in negative_words if word in content_lower
                )

                # Calculate simple polarity
                if positive_count > 0 or negative_count > 0:
                    polarity = (positive_count - negative_count) / (
                        positive_count + negative_count
                    )
                    sentiment_values.append(polarity)

        # Calculate sentiment variance
        if len(sentiment_values) > 1:
            min_sentiment = min(sentiment_values)
            max_sentiment = max(sentiment_values)
            sentiment_range = max_sentiment - min_sentiment

            if sentiment_range < 0.3:  # Consistent sentiment
                score += 10
            elif sentiment_range < 0.6:  # Moderate consistency
                score += 0
            else:  # Inconsistent sentiment
                score -= 10

        # Check for key values consistency
        key_values = analysis.get("key_values", [])
        if key_values:
            value_words = [value.lower() for value in key_values]
            value_mentions = 0

            # Count mentions of key values in social content
            for social in social_content:
                content = social.get("content", "").lower()
                for value in value_words:
                    if value in content:
                        value_mentions += 1

            # Adjust score based on value mentions
            if value_mentions > len(social_content):
                score += 10  # Values consistently mentioned
            elif value_mentions > 0:
                score += 5  # Some value mentions

        # Consistency in posting frequency
        if social_content:
            frequencies = [social.get("frequency", "") for social in social_content]
            unique_frequencies = set(frequencies)

            if len(unique_frequencies) == 1:
                score += 5  # Consistent posting schedule
            elif len(unique_frequencies) < len(frequencies) // 2:
                score += 3  # Somewhat consistent

        # Ensure score is within bounds
        score = max(0, min(100, score))

        return int(score)
    except Exception as e:
        logger.error(f"Error calculating consistency score: {str(e)}")
        return 70  # Return default score
