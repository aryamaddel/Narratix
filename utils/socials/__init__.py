import re
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional

from .common import identify_platform, PLATFORMS, extract_username_from_url
from .twitter import get_twitter_data
from .instagram import get_instagram_data
from .youtube import get_youtube_data
from .facebook import get_facebook_data

# Constants
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
}

def extract_social_content(social_links: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """Extract content from social media platforms using platform-specific modules"""
    if not social_links:
        return []
    
    social_content = []
    processed_domains = set()
    
    for link in social_links:
        try:
            url = link.get("url")
            if not url:
                continue
                
            domain = urlparse(url).netloc
            if domain in processed_domains:
                continue
                
            processed_domains.add(domain)
            platform = link.get("platform") or identify_platform(url)
            
            if not platform:
                continue
            
            # Get data using platform-specific modules
            platform_data = extract_with_api(url, platform)
            
            # Fallback to basic scraping if API extraction fails
            if not platform_data:
                platform_data = extract_with_scraping(url, platform)
                
            if platform_data:
                social_content.append(platform_data)
                
        except Exception as e:
            print(f"Error processing {link.get('url')}: {str(e)}")
            
    return social_content

def extract_with_scraping(url: str, platform: str) -> Optional[Dict[str, Any]]:
    """Basic scraping fallback method"""
    try:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=10)
        if response.status_code != 200:
            return None
            
        soup = BeautifulSoup(response.content, "html.parser")
        page_text = soup.get_text()
        
        # Extract follower count
        followers = "Unknown"
        follower_pattern = PLATFORMS.get(platform, {}).get("pattern")
        if follower_pattern:
            follower_match = re.search(follower_pattern, page_text, re.IGNORECASE)
            if follower_match:
                followers = follower_match.group(1)
        
        # Create platform data
        return {
            "platform": platform.capitalize(),
            "type": "profile",
            "followers": followers,
            "engagement": "Medium",  # Default
            "frequency": "Weekly",   # Default
            "url": url,
            "content": f"Content from {platform.capitalize()}"
        }
    except Exception:
        return None

def extract_with_api(url: str, platform: str) -> Optional[Dict[str, Any]]:
    """Extract data using platform-specific APIs"""
    username = extract_username_from_url(url, platform)
    
    # Process based on platform
    if platform == "twitter" or platform == "x":
        return get_twitter_data(username) if username else None
    elif platform == "instagram":
        return get_instagram_data(username) if username else None
    elif platform == "youtube":
        return get_youtube_data(url)
    elif platform == "facebook":
        return get_facebook_data(url, username)
    
    return None

__all__ = [
    'identify_platform',
    'PLATFORMS', 
    'extract_username_from_url',
    'get_twitter_data', 
    'get_instagram_data', 
    'get_youtube_data',
    'get_facebook_data',
    'extract_social_content',
    'extract_with_scraping',
    'extract_with_api'
]
