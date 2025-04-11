import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, Any, Optional

from .common import DEFAULT_HEADERS, PLATFORMS

def get_facebook_data(url: str, page_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Get Facebook page data through scraping"""
    try:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=10)
        if response.status_code != 200:
            return None
            
        soup = BeautifulSoup(response.content, "html.parser")
        page_text = soup.get_text()
        
        # Extract follower count
        followers = "Unknown"
        follower_pattern = PLATFORMS["facebook"]["pattern"]
        follower_match = re.search(follower_pattern, page_text, re.IGNORECASE)
        if follower_match:
            followers = follower_match.group(1)
        
        # Get page title
        page_name = ""
        title_tag = soup.find("title")
        if title_tag:
            page_name = title_tag.text.replace(" | Facebook", "").strip()
        elif page_id:
            page_name = page_id
        
        return {
            "platform": "Facebook",
            "type": "page",
            "username": page_name,
            "followers": followers,
            "engagement": "Medium",  # Default
            "frequency": "Weekly",   # Default
            "url": url,
            "content": f"Content from Facebook page: {page_name}",
            "real_data": follower_match is not None
        }
    except Exception:
        return None
