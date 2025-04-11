import requests
from typing import Dict, Any, Optional

from .common import DEFAULT_HEADERS

def get_instagram_data(username: str) -> Optional[Dict[str, Any]]:
    """Get Instagram profile data"""
    if not username:
        return None
        
    try:
        headers = {
            **DEFAULT_HEADERS,
            "X-IG-App-ID": "936619743392459",  # Public Instagram Web App ID
        }
        
        url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
        
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return _get_instagram_scrape_data(username)
            
        data = response.json()
        user = data.get("data", {}).get("user", {})
        if not user:
            return _get_instagram_scrape_data(username)
            
        followers = user.get("edge_followed_by", {}).get("count", 0)
        
        return {
            "platform": "Instagram",
            "type": "profile",
            "username": user.get("username", ""),
            "followers": str(followers),
            "engagement": "Medium",
            "frequency": "Weekly",
            "url": f"https://instagram.com/{username}",
            "real_data": True
        }
    except Exception:
        return _get_instagram_scrape_data(username)

def _get_instagram_scrape_data(username: str) -> Optional[Dict[str, Any]]:
    """Fallback to scraping Instagram data"""
    try:
        url = f"https://www.instagram.com/{username}/"
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=10)
        
        return {
            "platform": "Instagram",
            "type": "profile",
            "username": username,
            "followers": "Unknown",
            "engagement": "Medium",
            "frequency": "Weekly",
            "url": url,
            "real_data": False
        }
    except Exception:
        return None
