import requests
import re
from urllib.parse import urlparse
from typing import Dict, List, Any, Optional

# Constants
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
}

# Platform definitions
PLATFORMS = {
    "facebook": {"domains": ["facebook.com", "fb.com"], "pattern": r"([\d,.]+[kKmM]?)\s*(?:followers|people follow this|likes)"},
    "twitter": {"domains": ["twitter.com", "x.com"], "pattern": r"(\d+[\d,.]*[kKmM]?)\s*(?:Followers|followers)"},
    "instagram": {"domains": ["instagram.com"], "pattern": r"([\d,.]+[kKmM]?)\s*followers"},
    "linkedin": {"domains": ["linkedin.com"], "pattern": r"([\d,.]+\s*followers)"},
    "youtube": {"domains": ["youtube.com", "youtu.be"], "pattern": r"([\d,.]+\s*subscribers)"},
    "pinterest": {"domains": ["pinterest.com"], "pattern": r"([\d,.]+\s*followers)"},
    "tiktok": {"domains": ["tiktok.com"], "pattern": r"([\d,.]+\s*Followers)"},
}

def identify_platform(url: str) -> Optional[str]:
    """Identify the social media platform from a URL"""
    if not url:
        return None
        
    domain = urlparse(url).netloc.lower()
    for platform, config in PLATFORMS.items():
        if any(platform_domain in domain for platform_domain in config["domains"]):
            return platform
    return None

def extract_username_from_url(url: str, platform: str) -> Optional[str]:
    """Extract username from social media URL"""
    if platform == "twitter" or platform == "x":
        match = re.search(r"(?:twitter|x)\.com/([^/?]+)", url)
        return match.group(1) if match else None
    elif platform == "instagram":
        match = re.search(r"instagram\.com/([^/?]+)", url)
        return match.group(1) if match else None
    elif platform == "facebook":
        # Extract Facebook page name/ID
        match = re.search(r"facebook\.com/([^/?]+)", url)
        return match.group(1) if match else None
    
    return None
