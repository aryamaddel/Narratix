"""
Specialized API helpers for social media data extraction
"""

import requests
import json
import re
import time
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import base64
import hmac
import hashlib
from typing import Dict, Any, Optional, List
import os 

# Twitter API v2 helpers
class TwitterAPIHelper:
    """Class to handle Twitter API operations"""

    def __init__(self, bearer_token=None):
        """Initialize with optional bearer token"""
        # Default token is the Twitter web client token (public)
        self.bearer_token = os.environ.get("TWITTER_BEARER_TOKEN")
        self.guest_token = None
    
    def get_guest_token(self):
        """Get a guest token for unauthenticated API access"""
        if self.guest_token:
            return self.guest_token
            
        try:
            response = requests.post(
                "https://api.twitter.com/1.1/guest/activate.json",
                headers={"Authorization": f"Bearer {self.bearer_token}"}
            )
            
            if response.status_code == 200:
                self.guest_token = json.loads(response.text)["guest_token"]
                return self.guest_token
        except Exception as e:
            print(f"Error getting guest token: {str(e)}")
        
        return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user info by username using guest token authentication"""
        guest_token = self.get_guest_token()
        if not guest_token:
            return None
            
        try:
            headers = {
                "Authorization": f"Bearer {self.bearer_token}",
                "x-guest-token": guest_token,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            features = {
                "hidden_profile_likes_enabled": True,
                "hidden_profile_subscriptions_enabled": True,
                "responsive_web_graphql_exclude_directive_enabled": True,
                "verified_phone_label_enabled": False,
                "subscriptions_verification_info_is_identity_verified_enabled": True,
                "subscriptions_verification_info_verified_since_enabled": True,
                "highlights_tweets_tab_ui_enabled": True,
                "creator_subscriptions_tweet_preview_api_enabled": True,
                "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
                "responsive_web_graphql_timeline_navigation_enabled": True
            }
            
            features_param = json.dumps(features)
            variables_param = json.dumps({"screen_name": username, "withSafetyModeUserFields": True})
            
            url = f"https://api.twitter.com/graphql/NimuplG1OB7Fd2btCLdBOw/UserByScreenName?variables={variables_param}&features={features_param}"
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = json.loads(response.text)
                user_data = data.get("data", {}).get("user", {})
                if user_data:
                    return user_data
        except Exception as e:
            print(f"Error getting Twitter user: {str(e)}")
            
        return None
    
    def format_user_data(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format Twitter API data into standardized format"""
        if not user_data:
            return {}
            
        result = user_data.get("result", {})
        if not result:
            return {}
            
        legacy = result.get("legacy", {})
        
        # Format tweet creation date
        created_at = legacy.get("created_at", "")
        try:
            date_obj = datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y")
            formatted_date = date_obj.strftime("%Y-%m-%d")
        except:
            formatted_date = ""
        
        # Get profile image without _normal suffix for full resolution
        profile_image = legacy.get("profile_image_url_https", "")
        if profile_image:
            profile_image = re.sub(r"_normal(\.[a-zA-Z]+)$", r"\1", profile_image)
        
        return {
            "platform": "Twitter",
            "type": "profile",
            "username": legacy.get("screen_name", ""),
            "display_name": legacy.get("name", ""),
            "followers": str(legacy.get("followers_count", 0)),
            "following": str(legacy.get("friends_count", 0)),
            "posts_count": str(legacy.get("statuses_count", 0)),
            "bio": legacy.get("description", ""),
            "content": legacy.get("description", ""),
            "profile_image": profile_image,
            "location": legacy.get("location", ""),
            "created_at": formatted_date,
            "verified": result.get("is_blue_verified", False),
            "engagement": self._calculate_engagement(legacy),
            "frequency": self._calculate_frequency(legacy),
            "url": f"https://twitter.com/{legacy.get('screen_name', '')}",
            "real_data": True
        }
    
    def _calculate_engagement(self, legacy_data: Dict[str, Any]) -> str:
        """Calculate engagement level based on profile metrics"""
        followers = legacy_data.get("followers_count", 0)
        statuses = legacy_data.get("statuses_count", 0)
        
        if followers == 0:
            return "Low"
            
        ratio = statuses / max(followers, 1)
        
        if followers > 10000 and ratio > 0.1:
            return "Very High"
        elif followers > 1000 and ratio > 0.05:
            return "High"
        elif ratio > 0.01:
            return "Medium"
        else:
            return "Low"
    
    def _calculate_frequency(self, legacy_data: Dict[str, Any]) -> str:
        """Calculate posting frequency based on total tweets and account age"""
        statuses = legacy_data.get("statuses_count", 0)
        created_at = legacy_data.get("created_at", "")
        
        if not created_at:
            return "Unknown"
            
        try:
            created_date = datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y")
            days_since_creation = (datetime.now().date() - created_date.date()).days
            
            if days_since_creation == 0:
                return "New Account"
                
            tweets_per_day = statuses / days_since_creation
            
            if tweets_per_day > 5:
                return "Multiple Daily"
            elif tweets_per_day > 0.9:
                return "Daily"
            elif tweets_per_day > 0.3:
                return "Several Weekly"
            elif tweets_per_day > 0.1:
                return "Weekly"
            else:
                return "Infrequent"
        except:
            return "Unknown"

# Instagram API helpers
class InstagramAPIHelper:
    """Class to handle Instagram data extraction"""
    
    def __init__(self):
        """Initialize with default headers"""
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "X-IG-App-ID": "936619743392459",  # Public Instagram Web App ID
            "X-Requested-With": "XMLHttpRequest",
        }
    
    def get_profile_info(self, username: str) -> Optional[Dict[str, Any]]:
        """Get profile info using Instagram's GraphQL API"""
        try:
            session = requests.Session()
            url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
            
            headers = {
                **self.headers,
                "Referer": f"https://www.instagram.com/{username}/",
                "Origin": "https://www.instagram.com"
            }
            
            response = session.get(url, headers=headers)
            
            if response.status_code == 200:
                data = json.loads(response.text)
                user = data.get("data", {}).get("user", {})
                if user:
                    return user
                    
        except Exception as e:
            print(f"Error fetching Instagram profile: {str(e)}")
        
        return None
    
    def format_profile_data(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format Instagram profile data into standardized format"""
        if not profile_data:
            return {}
            
        # Extract basic metrics
        followers = profile_data.get("edge_followed_by", {}).get("count", 0)
        following = profile_data.get("edge_follow", {}).get("count", 0)
        posts_count = profile_data.get("edge_owner_to_timeline_media", {}).get("count", 0)
        
        # Calculate engagement level based on recent posts
        engagement = "Medium"  # Default
        recent_posts = profile_data.get("edge_owner_to_timeline_media", {}).get("edges", [])
        
        if recent_posts and followers > 0:
            total_likes = 0
            total_comments = 0
            
            for post in recent_posts[:12]:  # Use up to 12 recent posts
                node = post.get("node", {})
                total_likes += node.get("edge_liked_by", {}).get("count", 0)
                total_comments += node.get("edge_media_to_comment", {}).get("count", 0)
            
            if recent_posts:
                avg_engagement = (total_likes + total_comments) / len(recent_posts)
                engagement_rate = avg_engagement / followers
                
                if engagement_rate > 0.1:  # 10%+
                    engagement = "Very High"
                elif engagement_rate > 0.03:  # 3-10%
                    engagement = "High"
                elif engagement_rate > 0.01:  # 1-3%
                    engagement = "Medium"
                else:
                    engagement = "Low"
        
        # Format recent posts
        formatted_posts = []
        for post in recent_posts[:5]:  # Limit to 5 most recent
            node = post.get("node", {})
            caption_edges = node.get("edge_media_to_caption", {}).get("edges", [])
            
            post_data = {
                "post_img": node.get("display_url", ""),
                "post_txt": caption_edges[0]["node"]["text"] if caption_edges else "",
                "post_likes": node.get("edge_liked_by", {}).get("count", 0),
                "post_comments": node.get("edge_media_to_comment", {}).get("count", 0),
                "post_time": datetime.fromtimestamp(node.get("taken_at_timestamp", 0)).strftime("%Y-%m-%d %H:%M:%S")
            }
            formatted_posts.append(post_data)
        
        # Format content
        content_parts = []
        if profile_data.get("biography"):
            content_parts.append(f"Bio: {profile_data.get('biography', '')}")
            
        for i, post in enumerate(formatted_posts):
            if post.get("post_txt"):
                truncated_text = post["post_txt"]
                if len(truncated_text) > 150:
                    truncated_text = truncated_text[:147] + "..."
                content_parts.append(f"Post {i+1}: {truncated_text}")
        
        return {
            "platform": "Instagram",
            "type": "profile",
            "username": profile_data.get("username", ""),
            "display_name": profile_data.get("full_name", ""),
            "followers": str(followers),
            "following": str(following),
            "posts_count": str(posts_count),
            "bio": profile_data.get("biography", ""),
            "content": " | ".join(content_parts) if content_parts else "Limited content available",
            "profile_image": profile_data.get("profile_pic_url_hd", ""),
            "is_verified": profile_data.get("is_verified", False),
            "engagement": engagement,
            "frequency": self._calculate_frequency(posts_count, profile_data),
            "url": f"https://instagram.com/{profile_data.get('username', '')}",
            "real_data": True,
            "recent_posts": formatted_posts
        }
    
    def _calculate_frequency(self, posts_count: int, profile_data: Dict[str, Any]) -> str:
        """Estimate posting frequency based on post count and recent post dates"""
        if posts_count == 0:
            return "Inactive"
            
        recent_posts = profile_data.get("edge_owner_to_timeline_media", {}).get("edges", [])
        if not recent_posts:
            return "Unknown"
            
        # Check timestamps of recent posts
        try:
            timestamps = []
            for post in recent_posts[:10]:  # Check up to 10 most recent posts
                node = post.get("node", {})
                timestamp = node.get("taken_at_timestamp", 0)
                if timestamp:
                    timestamps.append(timestamp)
                    
            if not timestamps:
                return "Unknown"
                
            # Calculate average time between posts
            timestamps.sort(reverse=True)  # Most recent first
            intervals = [(timestamps[i] - timestamps[i+1]) for i in range(len(timestamps)-1)]
            
            if not intervals:
                return "Unknown"
                
            avg_interval = sum(intervals) / len(intervals)
            avg_days = avg_interval / 86400  # Convert seconds to days
            
            if avg_days < 1:
                return "Multiple Daily"
            elif avg_days < 3:
                return "Daily"
            elif avg_days < 7:
                return "Several Weekly"
            elif avg_days < 14:
                return "Weekly"
            elif avg_days < 30:
                return "Monthly"
            else:
                return "Infrequent"
        except:
            # Fallback estimation based on total post count
            account_age_estimate = 365  # Assume ~1 year account age as fallback
            posts_per_day = posts_count / account_age_estimate
            
            if posts_per_day > 0.7:
                return "Daily"
            elif posts_per_day > 0.2:
                return "Weekly"
            else:
                return "Infrequent"

# YouTube Data API helper
class YouTubeAPIHelper:
    """Class to handle YouTube data extraction"""
    
    def __init__(self, api_key=None):
        """Initialize with optional API key"""
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"
    
    def get_channel_info(self, channel_id=None, username=None, url=None):
        """Get channel info using YouTube Data API or scraping"""
        # Return empty if no API key and no identifiers
        if not self.api_key:
            return None
            
        if not channel_id and not username:
            # Try to extract channel ID or username from URL
            if url:
                channel_id, username = self._extract_channel_identifiers(url)
                if not channel_id and not username:
                    return None
            else:
                return None
                
        try:
            # Different endpoints based on available identifiers
            if channel_id:
                endpoint = f"{self.base_url}/channels?part=snippet,statistics,contentDetails&id={channel_id}&key={self.api_key}"
            else:
                endpoint = f"{self.base_url}/channels?part=snippet,statistics,contentDetails&forUsername={username}&key={self.api_key}"
                
            response = requests.get(endpoint)
            
            if response.status_code == 200:
                data = json.loads(response.text)
                items = data.get("items", [])
                
                if items:
                    return items[0]
        except Exception as e:
            print(f"Error fetching YouTube channel: {str(e)}")
            
        return None
    
    def _extract_channel_identifiers(self, url):
        """Extract channel ID or username from YouTube URL"""
        channel_id = None
        username = None
        
        try:
            parsed_url = urlparse(url)
            path = parsed_url.path
            query = parse_qs(parsed_url.query)
            
            # Check for channel ID in path
            if '/channel/' in path:
                channel_id = path.split('/channel/')[1].split('/')[0]
            # Check for username in path
            elif '/user/' in path:
                username = path.split('/user/')[1].split('/')[0]
            # Check for custom URL
            elif '/c/' in path:
                username = path.split('/c/')[1].split('/')[0]
            # Check for channel ID in query
            elif 'channel_id' in query:
                channel_id = query['channel_id'][0]
        except:
            pass
            
        return channel_id, username
    
    def format_channel_data(self, channel_data):
        """Format YouTube channel data into standardized format"""
        if not channel_data:
            return {}
            
        snippet = channel_data.get("snippet", {})
        statistics = channel_data.get("statistics", {})
        
        # Get subscriber count
        subscribers = statistics.get("subscriberCount", "0")
        view_count = statistics.get("viewCount", "0")
        video_count = statistics.get("videoCount", "0")
        
        # Calculate engagement from views per video
        engagement = "Medium"  # Default
        if int(video_count) > 0 and int(view_count) > 0:
            views_per_video = int(view_count) / int(video_count)
            subs = int(subscribers) if subscribers.isdigit() else 0
            
            if subs > 0:
                view_sub_ratio = views_per_video / subs
                
                if view_sub_ratio > 0.5:
                    engagement = "Very High"
                elif view_sub_ratio > 0.2:
                    engagement = "High"
                elif view_sub_ratio > 0.05:
                    engagement = "Medium"
                else:
                    engagement = "Low"
        
        # Format upload frequency
        frequency = "Unknown"
        if "contentDetails" in channel_data:
            upload_playlist = channel_data["contentDetails"].get("relatedPlaylists", {}).get("uploads", "")
            if upload_playlist and self.api_key:
                frequency = self._get_upload_frequency(upload_playlist)
        
        return {
            "platform": "YouTube",
            "type": "channel",
            "channel_id": channel_data.get("id", ""),
            "display_name": snippet.get("title", ""),
            "followers": subscribers,  # Using standard "followers" field for consistency
            "subscribers": subscribers,
            "view_count": view_count,
            "video_count": video_count,
            "bio": snippet.get("description", ""),
            "content": snippet.get("description", ""),
            "profile_image": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
            "engagement": engagement,
            "frequency": frequency,
            "url": f"https://youtube.com/channel/{channel_data.get('id', '')}",
            "real_data": True
        }
    
    def _get_upload_frequency(self, upload_playlist):
        """Analyze upload frequency from recent videos"""
        try:
            endpoint = f"{self.base_url}/playlistItems?part=contentDetails&maxResults=10&playlistId={upload_playlist}&key={self.api_key}"
            response = requests.get(endpoint)
            
            if response.status_code == 200:
                data = json.loads(response.text)
                items = data.get("items", [])
                
                if len(items) < 2:
                    return "Infrequent"
                    
                # Get publish dates
                dates = []
                for item in items:
                    publish_date = item.get("contentDetails", {}).get("videoPublishedAt", "")
                    if publish_date:
                        dates.append(datetime.strptime(publish_date, "%Y-%m-%dT%H:%M:%SZ"))
                
                # Sort by most recent
                dates.sort(reverse=True)
                
                # Calculate average days between uploads
                intervals = [(dates[i] - dates[i+1]).days for i in range(len(dates)-1)]
                avg_interval = sum(intervals) / len(intervals)
                
                if avg_interval < 1:
                    return "Multiple Daily"
                elif avg_interval < 3:
                    return "Daily"
                elif avg_interval < 7:
                    return "Several Weekly"
                elif avg_interval < 14:
                    return "Weekly"
                elif avg_interval < 30:
                    return "Monthly"
                else:
                    return "Infrequent"
        except:
            pass
            
        return "Unknown"

# Main function to handle social API extraction
def extract_with_api(url, platform, username=None, api_keys=None):
    """Extract social media data using appropriate API method"""
    api_keys = api_keys or {}
    
    # Extract username from URL if not provided
    if not username:
        if platform == "twitter" or platform == "x":
            username_match = re.search(r"(?:twitter|x)\.com/([^/?]+)", url)
            if username_match:
                username = username_match.group(1)
        elif platform == "instagram":
            username_match = re.search(r"instagram\.com/([^/?]+)", url)
            if username_match:
                username = username_match.group(1)
    
    # Use platform-specific API helpers
    if platform == "twitter" or platform == "x":
        helper = TwitterAPIHelper()
        user_data = helper.get_user_by_username(username)
        if user_data:
            return helper.format_user_data(user_data)
            
    elif platform == "instagram":
        helper = InstagramAPIHelper()
        profile_data = helper.get_profile_info(username)
        if profile_data:
            return helper.format_profile_data(profile_data)
            
    elif platform == "youtube":
        helper = YouTubeAPIHelper(api_key=api_keys.get("youtube"))
        channel_data = helper.get_channel_info(url=url)
        if channel_data:
            return helper.format_channel_data(channel_data)
    
    return None
