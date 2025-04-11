import os
import json
import requests
from typing import Dict, Any, Optional

from .common import DEFAULT_HEADERS

def get_twitter_data(username: str) -> Optional[Dict[str, Any]]:
    """Get Twitter profile data using API or scraping"""
    bearer_token = os.environ.get("TWITTER_BEARER_TOKEN")
    if not username:
        return None
        
    # Try API method first if token available
    if bearer_token:
        result = _get_twitter_api_data(username, bearer_token)
        if result:
            return result
    
    # Fallback to scraping
    return _get_twitter_scrape_data(username)

def _get_twitter_api_data(username: str, bearer_token: str) -> Optional[Dict[str, Any]]:
    """Get Twitter data using API"""
    try:
        # Get guest token for unauthenticated access
        response = requests.post(
            "https://api.twitter.com/1.1/guest/activate.json",
            headers={"Authorization": f"Bearer {bearer_token}"}
        )
        
        if response.status_code != 200:
            return None
            
        guest_token = response.json().get("guest_token")
        if not guest_token:
            return None
        
        # Get user data
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "x-guest-token": guest_token,
        }
        
        variables = json.dumps({"screen_name": username, "withSafetyModeUserFields": True})
        features = json.dumps({"responsive_web_graphql_timeline_navigation_enabled": True})
        
        endpoint = f"https://api.twitter.com/graphql/NimuplG1OB7Fd2btCLdBOw/UserByScreenName?variables={variables}&features={features}"
        
        response = requests.get(endpoint, headers=headers)
        if response.status_code != 200:
            return None
            
        data = response.json()
        user = data.get("data", {}).get("user", {})
        if not user:
            return None
            
        result = user.get("result", {})
        legacy = result.get("legacy", {})
        
        return {
            "platform": "Twitter",
            "type": "profile",
            "username": legacy.get("screen_name", ""),
            "followers": str(legacy.get("followers_count", 0)),
            "engagement": "Medium",
            "frequency": "Weekly",
            "url": f"https://twitter.com/{username}",
            "real_data": True
        }
    except Exception:
        return None

def _get_twitter_scrape_data(username: str) -> Optional[Dict[str, Any]]:
    """Get Twitter data via scraping as fallback"""
    try:
        url = f"https://twitter.com/{username}"
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=10)
        
        # Basic return with minimal data
        return {
            "platform": "Twitter",
            "type": "profile",
            "username": username,
            "followers": "Unknown", 
            "engagement": "Unknown",
            "frequency": "Unknown",
            "url": url,
            "real_data": False
        }
    except Exception:
        return None
