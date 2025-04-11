import os
import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse

from .common import DEFAULT_HEADERS

def get_youtube_data(url: str) -> Optional[Dict[str, Any]]:
    """Get YouTube channel data"""
    try:
        channel_id, username = _extract_channel_info(url)
        
        # Try API if key is available
        api_key = os.environ.get("YOUTUBE_API_KEY")
        if api_key and (channel_id or username):
            data = _get_youtube_api_data(channel_id, username, api_key)
            if data:
                return data
        
        # Fallback to basic return
        return {
            "platform": "YouTube",
            "type": "channel",
            "username": username or "YouTube Channel",
            "followers": "Search web for data",
            "engagement": "Medium",
            "frequency": "Weekly",
            "url": url,
            "real_data": False
        }
    except Exception:
        return None

def _extract_channel_info(url: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract channel ID and username from YouTube URL"""
    channel_id = None
    username = None
    
    try:
        parsed_url = urlparse(url)
        path = parsed_url.path
        
        if '/channel/' in path:
            channel_id = path.split('/channel/')[1].split('/')[0]
        elif '/user/' in path:
            username = path.split('/user/')[1].split('/')[0]
        elif '/c/' in path:
            username = path.split('/c/')[1].split('/')[0]
        else:
            # Try to get name from the last part of URL
            parts = [p for p in path.split('/') if p]
            if parts:
                username = parts[-1]
    except Exception:
        pass
        
    return channel_id, username

def _get_youtube_api_data(channel_id: Optional[str], username: Optional[str], api_key: str) -> Optional[Dict[str, Any]]:
    """Get YouTube data using API"""
    try:
        if channel_id:
            endpoint = f"https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&id={channel_id}&key={api_key}"
        elif username:
            endpoint = f"https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&forUsername={username}&key={api_key}"
        else:
            return None
            
        response = requests.get(endpoint, timeout=10)
        if response.status_code != 200:
            return None
            
        data = response.json()
        items = data.get("items", [])
        if not items:
            return None
            
        channel = items[0]
        snippet = channel.get("snippet", {})
        stats = channel.get("statistics", {})
        
        return {
            "platform": "YouTube",
            "type": "channel",
            "username": snippet.get("title", username or ""),
            "followers": stats.get("subscriberCount", "0"),
            "engagement": "Medium",
            "frequency": "Weekly",
            "url": f"https://youtube.com/channel/{channel.get('id', '')}",
            "real_data": True
        }
    except Exception:
        return None
