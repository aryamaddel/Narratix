from urllib.parse import urlparse
from flask import Flask, render_template, request, jsonify

# Import utility modules
# Remove this import
# from utils.analyzer import analyze_content
# Import Gemini search utilities (now includes all social functionality)
from utils.brand_analyzer import search_website_content, search_social_media, GEMINI_AVAILABLE
from utils.brand_analyzer import generate_brand_story, generate_visual_profile, generate_consistency_score
from utils.brand_analyzer import get_social_profiles, analyze_content  # Added analyze_content here

# Initialize Flask app
app = Flask(__name__)


@app.route("/")
def index():
    """Render the main page"""
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze_website():
    """API endpoint to analyze a website and generate a brand story"""
    data = request.get_json()
    url = data.get("url", "").strip()

    if not url:
        return jsonify({"error": "URL is required"}), 400

    # Validate and normalize URL format
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    # Initialize with defaults in case of failure
    domain = urlparse(url).netloc
    default_brand_name = domain.replace("www.", "")
    default_brand_name = default_brand_name.split(".")[0].capitalize()

    # Initialize empty result structure with default values
    result = {
        "brand_name": default_brand_name,
        "brand_description": f"Website for {default_brand_name}",
        "social_links": [],
        "social_analytics": [],
        "key_values": ["Quality", "Innovation", "Service", "Excellence", "Integrity"],
        "tone_analysis": {
            "professional": 0.7,
            "friendly": 0.4,
            "informative": 0.6,
            "enthusiastic": 0.3,
            "formal": 0.5,
        },
        "keywords": ["professional", "service", "quality", "experience", "solution"],
        "brand_story": f"# {default_brand_name}: Brand Story\n\n## Overview\n\n{default_brand_name} is a brand focused on delivering quality products and services.",
        "visual_profile": {
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
        },
        "consistency_score": 70,
        "api_method": "default",
        "error": None  # Add an error field to track any specific issues
    }

    try:
        # Step 1: Use Gemini API to search and extract website content if available
        if GEMINI_AVAILABLE:
            try:
                website_content = search_website_content(url)
                # Update result with website content
                if website_content.get("brand_name"):
                    result["brand_name"] = website_content.get("brand_name")
                if website_content.get("description"):
                    result["brand_description"] = website_content.get("description")
                # Mark that we're using the Gemini API
                result["api_method"] = "gemini"
            except Exception as e:
                # Continue with default website content
                from utils.crawler import extract_website_content
                website_content = extract_website_content(url)
                result["error"] = f"Gemini search failed: {str(e)}"
        else:
            # If Gemini is not available, use traditional crawler
            from utils.crawler import extract_website_content
            website_content = extract_website_content(url)

        # Step 2: Use our unified approach to search social media profiles
        try:
            # Use the unified function that tries search first, then scraping
            social_content = get_social_profiles(brand_name=result["brand_name"], website_url=url)
            
            # Extract social links for compatibility with existing code
            social_links = []
            social_analytics = []
            
            for social in social_content:
                # Add to social links
                social_links.append({
                    "platform": social["platform"],
                    "url": social["url"]
                })
                
                # Add to social analytics
                social_analytics.append({
                    "platform": social["platform"],
                    "followers": social.get("followers", "N/A"),
                    "engagement": social.get("engagement", "Medium"),
                    "frequency": social.get("frequency", "Unknown"),
                })
            
            result["social_links"] = social_links
            result["social_analytics"] = social_analytics
        except Exception as e:
            # Continue with empty social_content
            social_content = []

        # Step 3: Analyze the content with error handling
        try:
            analysis = analyze_content(website_content, social_content)
            # Update result with analysis
            result["key_values"] = analysis.get("key_values", result["key_values"])
            result["tone_analysis"] = analysis.get("tone_analysis", result["tone_analysis"])
            result["keywords"] = analysis.get("keywords", result["keywords"])
        except Exception as e:
            # Continue with default analysis from result
            analysis = {
                "keywords": result["keywords"],
                "tone_analysis": result["tone_analysis"],
                "key_values": result["key_values"],
                "sentiment": {"polarity": 0.1, "subjectivity": 0.3},
            }

        # Step 4: Generate the brand story with error handling
        try:
            brand_story = generate_brand_story(
                result["brand_name"],
                result["brand_description"],
                analysis,
                social_content,
            )
            
            # Ensure brand_story is a string and properly formatted
            if brand_story:
                # Make sure brand story is a string
                if not isinstance(brand_story, str):
                    brand_story = str(brand_story)
                
                # Ensure it has proper Markdown formatting with headers
                if not brand_story.startswith("#"):
                    brand_story = f"# {result['brand_name']}: Brand Story\n\n{brand_story}"
                    
                # Remove any problematic characters that might affect display
                brand_story = brand_story.replace("\r", "")
                
                result["brand_story"] = brand_story
        except Exception as e:
            # Create a simple brand story as fallback
            result["brand_story"] = f"# {result['brand_name']}: Brand Story\n\n## Overview\n\n{result['brand_description']}"
            result["error"] = f"Brand story generation failed: {str(e)}"

        # Step 5: Generate visual profile data with error handling
        try:
            visual_profile = generate_visual_profile(analysis)
            result["visual_profile"] = visual_profile
        except Exception as e:
            # Continue with default visual profile
            pass

        # Step 6: Calculate consistency score with error handling
        try:
            consistency_score = generate_consistency_score(
                website_content, social_content, analysis
            )
            result["consistency_score"] = consistency_score
        except Exception as e:
            # Continue with default consistency score
            pass

        return jsonify(result)

    except Exception as e:
        # Return our default result with the error message
        result["error"] = str(e)
        return jsonify(result)
