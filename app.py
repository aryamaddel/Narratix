#!/usr/bin/env python
"""
BrandDecoder - Website to Brand Story Generator

A Flask application that crawls websites, extracts social media links,
analyzes content across platforms, and generates comprehensive brand stories.

Author: [Your Name]
Created for: Hackathon Project
"""

import os
import logging
import json
from urllib.parse import urlparse
from flask import Flask, render_template, request, jsonify
import traceback

# Import utility modules
from utils.crawler import extract_social_links, extract_website_content
from utils.social import extract_social_content
from utils.analyzer import analyze_content
from utils.generator import (
    generate_brand_story,
    generate_visual_profile,
    generate_consistency_score,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

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

    logger.info(f"Analyzing website: {url}")

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
    }

    try:
        # Step 1: Extract social media links with error handling
        try:
            social_links = extract_social_links(url)
            logger.info(f"Found {len(social_links)} social media links")
            result["social_links"] = social_links
        except Exception as e:
            logger.error(f"Error extracting social links: {str(e)}")
            logger.debug(traceback.format_exc())
            # Continue with empty social_links from default result

        # Step 2: Extract website content with error handling
        try:
            website_content = extract_website_content(url)
            logger.info(
                f"Extracted content for brand: {website_content.get('brand_name', default_brand_name)}"
            )

            # Update result with website content
            result["brand_name"] = website_content.get("brand_name", default_brand_name)
            result["brand_description"] = website_content.get(
                "description", result["brand_description"]
            )
        except Exception as e:
            logger.error(f"Error extracting website content: {str(e)}")
            logger.debug(traceback.format_exc())
            # Continue with default website content
            website_content = {
                "brand_name": result["brand_name"],
                "description": result["brand_description"],
                "content": "",
            }

        # Step 3: Fetch social media content with error handling
        social_content = []
        try:
            social_content = extract_social_content(result["social_links"])
            logger.info(
                f"Extracted content from {len(social_content)} social platforms"
            )

            # Extract social analytics
            social_analytics = []
            for social in social_content:
                try:
                    social_analytics.append(
                        {
                            "platform": social["platform"],
                            "followers": social.get("followers", "N/A"),
                            "engagement": social.get("engagement", "N/A"),
                            "frequency": social.get("frequency", "N/A"),
                        }
                    )
                except Exception:
                    continue

            result["social_analytics"] = social_analytics
        except Exception as e:
            logger.error(f"Error extracting social content: {str(e)}")
            logger.debug(traceback.format_exc())
            # Continue with empty social_content

        # Step 4: Analyze the content with error handling
        try:
            analysis = analyze_content(website_content, social_content)
            logger.info(
                f"Content analysis complete. Found {len(analysis.get('keywords', []))} keywords"
            )

            # Update result with analysis
            result["key_values"] = analysis.get("key_values", result["key_values"])
            result["tone_analysis"] = analysis.get(
                "tone_analysis", result["tone_analysis"]
            )
            result["keywords"] = analysis.get("keywords", result["keywords"])
        except Exception as e:
            logger.error(f"Error in content analysis: {str(e)}")
            logger.debug(traceback.format_exc())
            # Continue with default analysis from result
            analysis = {
                "keywords": result["keywords"],
                "tone_analysis": result["tone_analysis"],
                "key_values": result["key_values"],
                "sentiment": {"polarity": 0.1, "subjectivity": 0.3},
            }

        # Step 5: Generate the brand story with error handling
        try:
            brand_story = generate_brand_story(
                result["brand_name"],
                result["brand_description"],
                analysis,
                social_content,
            )
            logger.info("Brand story generated successfully")
            result["brand_story"] = brand_story
        except Exception as e:
            logger.error(f"Error generating brand story: {str(e)}")
            logger.debug(traceback.format_exc())
            # Create a simple brand story as fallback (already in result defaults)

        # Step 6: Generate visual profile data with error handling
        try:
            visual_profile = generate_visual_profile(analysis)
            result["visual_profile"] = visual_profile
        except Exception as e:
            logger.error(f"Error generating visual profile: {str(e)}")
            logger.debug(traceback.format_exc())
            # Continue with default visual profile

        # Step 7: Calculate consistency score with error handling
        try:
            consistency_score = generate_consistency_score(
                website_content, social_content, analysis
            )
            logger.info(f"Brand consistency score: {consistency_score}/100")
            result["consistency_score"] = consistency_score
        except Exception as e:
            logger.error(f"Error calculating consistency score: {str(e)}")
            logger.debug(traceback.format_exc())
            # Continue with default consistency score

        return jsonify(result)

    except Exception as e:
        logger.error(f"Unexpected error in analysis process: {str(e)}")
        logger.debug(traceback.format_exc())
        # Return our default result with the error message
        result["error"] = str(e)
        return jsonify(result)


if __name__ == "__main__":
    # Check if we are in a development environment
    debug_mode = os.environ.get("FLASK_ENV") == "development"
    app.run(debug=debug_mode, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
