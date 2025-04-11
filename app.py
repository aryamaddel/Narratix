from flask import Flask, render_template, request, jsonify

# Import utility modules
from utils.crawler import extract_website_content, extract_social_links
from utils.socials import extract_social_content  # Updated import path
from utils.analyzer import analyze_content
from utils.llm_providers import generate_brand_story  # Updated import path
from utils.visuals import generate_visual_profile, generate_consistency_score  # Updated import path

# Initialize Flask app
app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze_website():
    """Analyze a website and generate a brand story"""
    data = request.get_json()
    url = data.get("url", "").strip()

    if not url:
        return jsonify({"error": "URL is required"}), 400

    # Normalize URL
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        # Simple workflow: Extract → Analyze → Generate
        website_content = extract_website_content(url)
        social_links = extract_social_links(url)
        social_content = extract_social_content(social_links)
        analysis = analyze_content(website_content, social_content)
        
        # Generate outputs
        brand_name = website_content.get("brand_name", "Brand")
        brand_story = generate_brand_story(brand_name, website_content.get("description", ""), analysis, social_content)
        visual_profile = generate_visual_profile(analysis)
        consistency_score = generate_consistency_score(website_content, social_content, analysis)
        
        # Return results
        return jsonify({
            "brand_name": brand_name,
            "brand_description": website_content.get("description", ""),
            "social_links": social_links,
            "social_analytics": [
                {
                    "platform": s["platform"],
                    "followers": s.get("followers", "N/A"),
                    "engagement": s.get("engagement", "Medium")
                }
                for s in social_content
            ],
            "keywords": analysis.get("keywords", []),
            "key_values": analysis.get("key_values", []),
            "brand_story": brand_story,
            "visual_profile": visual_profile,
            "consistency_score": consistency_score,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
