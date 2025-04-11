from urllib.parse import urlparse
from flask import Flask, render_template, request, jsonify

# Import utility modules
from utils.crawler import extract_social_links, extract_website_content
from utils.social import extract_social_content
from utils.analyzer import analyze_content
from utils.generator import (
    generate_brand_story,
    generate_visual_profile,
    generate_consistency_score,
)

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

    try:
        # Step 1: Extract basic website content
        website_content = extract_website_content(url)
        brand_name = website_content.get("brand_name", "Brand")
        
        # Step 2: Extract social media links
        social_links = extract_social_links(url)
        
        # Step 3: Get social media content
        social_content = extract_social_content(social_links)
        
        # Step 4: Analyze content
        analysis = analyze_content(website_content, social_content)
        
        # Step 5: Generate brand story and visual profile
        brand_story = generate_brand_story(brand_name, website_content.get("description", ""), analysis, social_content)
        visual_profile = generate_visual_profile(analysis)
        consistency_score = generate_consistency_score(website_content, social_content, analysis)
        
        # Extract social analytics for display
        social_analytics = []
        for social in social_content:
            social_analytics.append({
                "platform": social["platform"],
                "followers": social.get("followers", "N/A"),
                "engagement": social.get("engagement", "Medium"),
                "frequency": social.get("frequency", "Weekly"),
            })

        # Return the results
        return jsonify({
            "brand_name": brand_name,
            "brand_description": website_content.get("description", ""),
            "social_links": social_links,
            "social_analytics": social_analytics,
            "key_values": analysis.get("key_values", []),
            "keywords": analysis.get("keywords", []),
            "tone_analysis": analysis.get("tone_analysis", {}),
            "brand_story": brand_story,
            "visual_profile": visual_profile,
            "consistency_score": consistency_score,
        })

    except Exception as e:
        # Create basic response with error message
        domain = urlparse(url).netloc
        default_brand_name = domain.replace("www.", "").split(".")[0].capitalize()
        
        return jsonify({
            "brand_name": default_brand_name,
            "brand_description": f"Website for {default_brand_name}",
            "error": str(e),
            "social_links": [],
            "social_analytics": [],
            "key_values": ["Quality", "Innovation", "Service", "Excellence", "Integrity"],
            "keywords": ["professional", "service", "quality", "experience", "solution"],
            "tone_analysis": {
                "professional": 0.7,
                "friendly": 0.4,
                "informative": 0.6,
            },
            "brand_story": f"# {default_brand_name}: Brand Story\n\nUnable to generate complete brand story.",
            "visual_profile": {
                "color_palette": {
                    "primary": "#0A3D62",
                    "secondary": "#3E92CC",
                    "accent": "#D8D8D8",
                }
            },
            "consistency_score": 70,
        })

if __name__ == "__main__":
    app.run(debug=True)
