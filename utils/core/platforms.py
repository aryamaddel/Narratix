import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Platform definitions
PLATFORMS = {
    "facebook": {
        "type": "page",
        "domains": ["facebook.com", "fb.com"],
        "bio_selectors": [
            "#PagesProfileAboutInfoPagelet",
            ".about_header",
            '[data-key="about"]',
            ".uiHeaderTitle + div",
            "#entity_sidebar",
        ],
        "post_selectors": [
            ".userContent",
            "._5pbx",
            ".text_exposed_root",
            '[data-testid="post_message"]',
            ".story_body_container",
            "._5rgt._5nk5",
        ],
        "follower_patterns": [
            r"([\d,.]+[kKmM]?)\s*people\s*like\s*this",
            r"([\d,.]+[kKmM]?)\s*likes",
            r"([\d,.]+[kKmM]?)\s*followers",
            r"([\d,\.]+[kKmM]?)\s*Followers",
            r"Followers:\s*([\d,\.]+[kKmM]?)",
            r"([0-9,.]+[kKmM]?)\s*people follow this",
        ],
    },
}

# Add other platforms with default configs
for platform in ["twitter", "instagram", "linkedin", "youtube", "pinterest", "tiktok",
                "github", "medium", "reddit"]:
    if platform not in PLATFORMS:
        PLATFORMS[platform] = {
            "type": "profile",
            "domains": [f"{platform}.com"],
            "bio_selectors": [],
            "post_selectors": [],
            "follower_patterns": []
        }

def identify_platform(url):
    """Identify the social media platform from a URL"""
    logger.debug(f"Identifying platform for URL: {url}")
    domain = urlparse(url).netloc.lower()

    for platform, config in PLATFORMS.items():
        for platform_domain in config["domains"]:
            if platform_domain in domain:
                logger.debug(f"Identified platform: {platform}")
                return platform

    logger.debug("Could not identify platform from URL")
    return None
