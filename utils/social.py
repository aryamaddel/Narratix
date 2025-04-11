import requests
import logging
import re
import time
import json
from datetime import datetime
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

# Constants
DEFAULT_TIMEOUT = 12
MAX_RETRIES = 3
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Connection": "keep-alive",
    "Cache-Control": "max-age=0",
    "Upgrade-Insecure-Requests": "1",
}

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
            r"([\d,.]+\s*people\s*like\s*this)",
            r"([\d,.]+\s*likes)",
            r"([\d,.]+\s*followers)",
        ],
    },
    "twitter": {
        "type": "profile",
        "domains": ["twitter.com", "x.com"],
        "bio_selectors": [
            '[data-testid="UserName"]',
            '[data-testid="UserDescription"]',
            ".ProfileHeaderCard",
            ".ProfileCard-bio",
        ],
        "post_selectors": [
            '[data-testid="tweet"]',
            ".tweet",
            ".content",
            ".js-tweet-text-container",
            "article",
        ],
        "follower_patterns": [
            r"(\d+[\d,.]*\s*(?:Followers|followers))",
            r"Followers:\s*(\d+[\d,.]*)",
        ],
    },
    "instagram": {
        "type": "profile",
        "domains": ["instagram.com"],
        "bio_selectors": [
            ".-vDIg",
            ".QGPIr",
            ".X7jCj",
            "header section",
            ".x7Um4d",
            "header h2",
            ".Fy4o8",
        ],
        "post_selectors": [
            ".C4VMK span",
            ".Ypffh",
            "._a9zr",
            ".xil3i",
            ".EtaWk",
            ".KcRnL",
            "._97aPb + div",
        ],
        "follower_patterns": [r"([\d,.]+\s*followers)", r"Followers\s*([\d,.]+)"],
    },
    "linkedin": {
        "type": "company",
        "domains": ["linkedin.com"],
        "bio_selectors": [
            ".org-about-us-organization-description__text",
            ".org-grid__core-rail--no-margin-left",
            ".break-words",
            ".org-page-details__description",
            ".org-top-card-summary__headline",
        ],
        "post_selectors": [
            ".feed-shared-update-v2__description",
            ".update-components-text",
            ".feed-shared-text",
            ".occludable-update",
            ".ember-view article",
        ],
        "follower_patterns": [r"([\d,.]+\s*followers)", r"Followers:\s*([\d,.]+)"],
    },
    "youtube": {
        "type": "channel",
        "domains": ["youtube.com", "youtu.be"],
        "bio_selectors": [
            "#channel-description",
            "#description-container",
            ".ytd-channel-about-metadata-renderer",
            ".about-description",
            "#meta-contents",
        ],
        "post_selectors": [
            "#video-title",
            ".yt-lockup-title",
            ".ytd-grid-video-renderer",
            ".ytd-grid-renderer",
            ".ytd-video-renderer",
        ],
        "follower_patterns": [r"([\d,.]+\s*subscribers)", r"Subscribers:\s*([\d,.]+)"],
    },
    "pinterest": {
        "type": "profile",
        "domains": ["pinterest.com"],
        "bio_selectors": [
            ".UserInfoBanner",
            ".ProfileHeader",
            ".headerDescription",
            '[data-test-id="profile-about"]',
        ],
        "post_selectors": [
            ".Pin__description",
            ".pinDescription",
            ".Pin__title",
            ".PinGridItem",
        ],
        "follower_patterns": [r"([\d,.]+\s*followers)", r"Followers:\s*([\d,.]+)"],
    },
    "tiktok": {
        "type": "profile",
        "domains": ["tiktok.com"],
        "bio_selectors": [
            ".share-desc",
            ".share-title",
            ".share-sub-title",
            ".tiktok-1ejylhp-DivBioLink",
        ],
        "post_selectors": [
            ".video-feed-item-wrapper",
            ".tiktok-1s72ajp-DivWrapper",
            ".video-card-big",
            ".video-card-container",
        ],
        "follower_patterns": [r"([\d,.]+\s*Followers)", r"Followers\s*([\d,.]+)"],
    },
    "github": {
        "type": "repository",
        "domains": ["github.com"],
        "bio_selectors": [
            ".repository-content",
            ".js-repo-meta-container",
            ".repository-meta-content",
            ".repo-meta-section",
        ],
        "post_selectors": [
            ".repo-description",
            ".repository-content",
            ".Box-body",
            ".markdown-body",
        ],
        "follower_patterns": [
            r"([\d,.]+\s*followers)",
            r"([\d,.]+\s*stars)",
            r"([\d,.]+\s*watching)",
        ],
    },
    "medium": {
        "type": "publication",
        "domains": ["medium.com"],
        "bio_selectors": [
            ".pw-author-bio",
            ".pw-author-bio-content",
            ".section-content",
            ".hero-description",
        ],
        "post_selectors": [
            ".pw-post-title",
            ".pw-post-body-paragraph",
            ".postArticle-content",
            ".graf--p",
        ],
        "follower_patterns": [r"([\d,.]+\s*followers)", r"([\d,.]+\s*Following)"],
    },
    "reddit": {
        "type": "subreddit",
        "domains": ["reddit.com"],
        "bio_selectors": [
            ".side",
            ".md",
            ".community-details",
            "._3-kbj2rAexiRJ5KmOX7bJX",
        ],
        "post_selectors": [
            ".thing",
            ".Post",
            '[data-click-id="body"]',
            ".scrollerItem",
        ],
        "follower_patterns": [r"([\d,.]+\s*members)", r"([\d,.]+\s*subscribers)"],
    },
}

# ---- Utility Functions ----


def get_requests_session():
    """Create a requests session with retry capability"""
    session = requests.Session()
    retry_strategy = Retry(
        total=MAX_RETRIES,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def identify_platform(url):
    """Identify the social media platform from a URL"""
    domain = urlparse(url).netloc.lower()

    for platform, config in PLATFORMS.items():
        for platform_domain in config["domains"]:
            if platform_domain in domain:
                return platform

    return None


def fetch_page(url, session=None):
    """Fetch a web page with error handling"""
    if session is None:
        session = get_requests_session()

    try:
        logger.info(f"Fetching page: {url}")

        # Add jitter to avoid rate limiting
        time.sleep(0.5 + (time.time() % 1))

        response = session.get(url, headers=HEADERS, timeout=DEFAULT_TIMEOUT)
        if response.status_code != 200:
            logger.warning(
                f"Failed to fetch {url} - Status code: {response.status_code}"
            )
            return None

        logger.info(
            f"Successfully fetched {url} - Length: {len(response.content)} bytes"
        )
        return response.content
    except Exception as e:
        logger.error(f"Error fetching {url}: {str(e)}")
        return None


def extract_text_from_selectors(soup, selectors, min_length=5, max_results=1):
    """Extract text from multiple potential selectors"""
    results = []

    for selector in selectors:
        try:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text().strip()
                if text and len(text) >= min_length:
                    results.append(text)
                    if max_results and len(results) >= max_results:
                        return results
        except Exception:
            continue

    return results


def extract_post_texts(soup, post_selectors, max_posts=5, min_post_length=15):
    """Extract multiple post texts from a page"""
    posts = []
    seen_texts = set()

    for selector in post_selectors:
        try:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text().strip()
                text = re.sub(r"\s+", " ", text)  # Normalize whitespace

                if text and len(text) >= min_post_length and text not in seen_texts:
                    posts.append(text)
                    seen_texts.add(text)

                    if len(posts) >= max_posts:
                        return posts
        except Exception:
            continue

    return posts


def extract_count_from_text(text, patterns):
    """Extract numeric count from text using multiple patterns"""
    for pattern in patterns:
        try:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        except Exception:
            continue

    return None


def estimate_posting_frequency(posts, page_text):
    """Estimate posting frequency from content"""
    # Look for date patterns in posts to estimate frequency
    date_patterns = [
        r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}",  # 01/01/2023
        r"\d{1,2}\s(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s\d{2,4}",  # 1 Jan 2023
        r"(yesterday|today|hours? ago|minutes? ago|seconds? ago)",  # Relative time
        r"\d+ (day|hour|minute|second)s? ago",  # X days ago
    ]

    recent_count = 0
    for post in posts:
        for pattern in date_patterns:
            if re.search(pattern, post, re.IGNORECASE):
                if any(
                    term in post.lower()
                    for term in [
                        "today",
                        "hour ago",
                        "minute ago",
                        "second ago",
                        "just now",
                    ]
                ):
                    recent_count += 1
                break

    # Check for frequency indicators in page text
    daily_indicators = ["daily post", "daily update", "every day", "posts daily"]
    weekly_indicators = ["weekly post", "weekly update", "every week", "posts weekly"]

    for indicator in daily_indicators:
        if indicator in page_text.lower():
            return "Daily"

    for indicator in weekly_indicators:
        if indicator in page_text.lower():
            return "Weekly"

    # Estimate based on number of recent posts
    if recent_count >= 2:
        return "Daily"
    elif len(posts) >= 4:
        return "Weekly"
    elif len(posts) >= 2:
        return "Bi-weekly"
    else:
        return "Monthly"


def clean_text_content(text, max_length=500):
    """Clean and truncate text content"""
    if not text:
        return ""

    # Remove excess whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # Truncate if too long
    if len(text) > max_length:
        return text[: max_length - 3] + "..."

    return text


# ---- Instagram Specialized Extraction ----


class InstaData:
    """Class to handle detailed Instagram data extraction (inspired by PHP code)"""

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Connection": "keep-alive",
            "Origin": "https://www.instagram.com",
            "Referer": "https://www.instagram.com/",
        }
        self.session = get_requests_session()

    def get_data(self, username):
        """Fetch raw HTML data for a given Instagram username"""
        try:
            url = f"https://www.instagram.com/{username}/"
            response = self.session.get(
                url, headers=self.headers, timeout=DEFAULT_TIMEOUT
            )

            if response.status_code == 200:
                return response.text
            else:
                logger.warning(
                    f"Failed to fetch Instagram profile for {username}: Status code {response.status_code}"
                )
                return None
        except Exception as e:
            logger.error(f"Error fetching Instagram data for {username}: {str(e)}")
            return None

    def fetch_user_details(self, username):
        """Extract user data from Instagram profile page"""
        insta_link = self.get_data(username)
        if not insta_link:
            return {}

        try:
            # Extract shared data JSON
            pattern = r"window\._sharedData = (.*?);</script>"
            match = re.search(pattern, insta_link)

            if match:
                json_data = json.loads(match.group(1))
                user_data = (
                    json_data.get("entry_data", {})
                    .get("ProfilePage", [{}])[0]
                    .get("graphql", {})
                    .get("user", {})
                )
                return user_data
            else:
                # Try alternative pattern for newer Instagram layout
                alt_pattern = r'<script type="application/ld\+json">(.*?)</script>'
                alt_match = re.search(alt_pattern, insta_link, re.DOTALL)

                if alt_match:
                    try:
                        ld_json = json.loads(alt_match.group(1))
                        # Extract what we can from the LD+JSON
                        return {
                            "username": ld_json.get("name", username),
                            "full_name": ld_json.get("name", ""),
                            "profile_pic_url_hd": ld_json.get("image", ""),
                            "is_verified": "false",
                        }
                    except:
                        pass

                logger.warning(
                    f"Could not find shared data in Instagram page for {username}"
                )
                return {}
        except Exception as e:
            logger.error(
                f"Error parsing Instagram user details for {username}: {str(e)}"
            )
            return {}

    def fetch_account_details(self, username):
        """Extract follower counts and metrics"""
        insta_link = self.get_data(username)
        if not insta_link:
            return []

        try:
            # Look for meta content with followers info
            pattern = r'<meta content="([0-9,.KkMm]+) Followers, ([0-9,.KkMm]+) Following, ([0-9,.KkMm]+) Posts'
            match = re.search(pattern, insta_link)

            if match:
                followers = match.group(1)
                following = match.group(2)
                posts = match.group(3)
                return [followers, following, posts]
            else:
                # Alternative extraction method from user details
                user_details = self.fetch_user_details(username)
                if user_details:
                    followers = user_details.get("edge_followed_by", {}).get("count", 0)
                    following = user_details.get("edge_follow", {}).get("count", 0)
                    posts = user_details.get("edge_owner_to_timeline_media", {}).get(
                        "count", 0
                    )
                    return [str(followers), str(following), str(posts)]
                else:
                    # Last resort: try extracting numbers from page text
                    soup = BeautifulSoup(insta_link, "html.parser")
                    page_text = soup.get_text()

                    followers_pattern = r"([\d,.KkMm]+)\s*followers"
                    following_pattern = r"([\d,.KkMm]+)\s*following"
                    posts_pattern = r"([\d,.KkMm]+)\s*posts"

                    followers = re.search(followers_pattern, page_text, re.IGNORECASE)
                    following = re.search(following_pattern, page_text, re.IGNORECASE)
                    posts = re.search(posts_pattern, page_text, re.IGNORECASE)

                    return [
                        followers.group(1) if followers else "0",
                        following.group(1) if following else "0",
                        posts.group(1) if posts else "0",
                    ]

                return []
        except Exception as e:
            logger.error(
                f"Error extracting Instagram account details for {username}: {str(e)}"
            )
            return []

    def get_timeline(self, username):
        """Get recent posts from the user's timeline"""
        user_data = self.fetch_user_details(username)
        if not user_data:
            return {"data": [], "count": 0}

        try:
            timeline_edges = user_data.get("edge_owner_to_timeline_media", {}).get(
                "edges", []
            )
            count = len(timeline_edges)

            timeline_data = []
            for i, edge in enumerate(timeline_edges):
                if i >= 5:  # Limit to 5 most recent posts
                    break

                node = edge.get("node", {})
                post_caption_edges = node.get("edge_media_to_caption", {}).get(
                    "edges", []
                )
                post_txt = (
                    post_caption_edges[0]["node"]["text"] if post_caption_edges else ""
                )

                post_img = node.get("display_url", "")
                post_likes = node.get("edge_liked_by", {}).get("count", 0)
                post_comments = node.get("edge_media_to_comment", {}).get("count", 0)
                post_time = node.get("taken_at_timestamp", 0)

                # Convert timestamp to formatted date
                date = (
                    datetime.fromtimestamp(post_time) if post_time else datetime.now()
                )
                formatted_date = date.strftime("%Y-%m-%d %H:%M:%S")

                timeline_data.append(
                    {
                        "post_img": post_img,
                        "post_txt": post_txt,
                        "post_time": formatted_date,
                        "post_likes": post_likes,
                        "post_comments": post_comments,
                    }
                )

            return {"data": timeline_data, "count": count}
        except Exception as e:
            logger.error(
                f"Error extracting Instagram timeline for {username}: {str(e)}"
            )
            return {"data": [], "count": 0}

    def get_user_details(self, username):
        """Get formatted user profile information"""
        json_output = self.fetch_user_details(username)
        if not json_output:
            return {}

        try:
            user_data = {
                "img": json_output.get("profile_pic_url_hd", ""),
                "full_name": json_output.get("full_name", ""),
                "username": json_output.get("username", username),
                "is_verified": "true" if json_output.get("is_verified") else "false",
                "id": json_output.get("id", ""),
                "instaUrl": f"https://instagram.com/{username}",
            }
            return user_data
        except Exception as e:
            logger.error(
                f"Error formatting Instagram user details for {username}: {str(e)}"
            )
            return {}

    def get_account_details(self, username):
        """Get formatted account metrics"""
        user_details = self.fetch_account_details(username)
        if not user_details or len(user_details) < 3:
            return {}

        try:
            account_data = {
                "followers": user_details[0],
                "following": user_details[1],
                "posts": user_details[2],
            }
            return account_data
        except Exception as e:
            logger.error(
                f"Error formatting Instagram account details for {username}: {str(e)}"
            )
            return {}


def extract_detailed_instagram(url):
    """Enhanced Instagram extraction using InstaData class"""
    # Extract username from URL
    username_match = re.search(r"instagram\.com/([^/?]+)", url)
    if not username_match:
        logger.warning(f"Could not extract username from Instagram URL: {url}")
        return None

    username = username_match.group(1)
    logger.info(f"Attempting detailed Instagram extraction for: {username}")

    insta = InstaData()

    try:
        # Get various Instagram data
        user_details = insta.get_user_details(username)
        account_details = insta.get_account_details(username)
        timeline = insta.get_timeline(username)

        if not user_details and not account_details:
            logger.warning(f"Could not extract detailed Instagram data for {username}")
            return None

        # Format data for our application
        followers = account_details.get("followers", "0")
        following = account_details.get("following", "0")
        posts_count = account_details.get("posts", "0")

        # Calculate engagement if possible
        engagement = "Medium"  # Default
        timeline_data = timeline.get("data", [])
        if timeline_data and followers and followers not in ["0", ""]:
            try:
                # Clean the followers value for calculation
                followers_cleaned = followers.replace(",", "")
                followers_cleaned = re.sub(r"[KkMm]", "", followers_cleaned)
                if "k" in followers.lower():
                    followers_num = float(followers_cleaned) * 1000
                elif "m" in followers.lower():
                    followers_num = float(followers_cleaned) * 1000000
                else:
                    followers_num = float(followers_cleaned)

                # Calculate average engagement from last posts
                likes_sum = sum(post.get("post_likes", 0) for post in timeline_data)
                comments_sum = sum(
                    post.get("post_comments", 0) for post in timeline_data
                )

                if timeline_data and followers_num > 0:
                    avg_engagement = (likes_sum + comments_sum) / len(timeline_data)
                    engagement_rate = avg_engagement / followers_num

                    if engagement_rate > 0.1:  # 10%+
                        engagement = "Very High"
                    elif engagement_rate > 0.03:  # 3-10%
                        engagement = "High"
                    elif engagement_rate > 0.01:  # 1-3%
                        engagement = "Medium"
                    else:
                        engagement = "Low"
            except Exception as e:
                logger.error(f"Error calculating Instagram engagement: {str(e)}")

        # Estimate posting frequency
        frequency = "Monthly"  # Default
        if timeline_data:
            try:
                if len(timeline_data) >= 3:
                    # Check last post date
                    latest_post = timeline_data[0]
                    post_date = datetime.strptime(
                        latest_post.get("post_time"), "%Y-%m-%d %H:%M:%S"
                    )
                    days_since = (datetime.now() - post_date).days

                    if days_since < 2:
                        frequency = "Daily"
                    elif days_since < 7:
                        frequency = "Weekly"
                    elif days_since < 14:
                        frequency = "Bi-weekly"
                    else:
                        frequency = "Monthly"
            except Exception as e:
                logger.error(f"Error estimating Instagram frequency: {str(e)}")

        # Format content
        content_parts = []
        if user_details.get("full_name"):
            content_parts.append(f"Name: {user_details['full_name']}")

        # Add recent post captions
        for i, post in enumerate(timeline_data[:3]):  # Include up to 3 recent posts
            if post.get("post_txt"):
                content_parts.append(
                    f"Post {i+1}: {clean_text_content(post['post_txt'], 150)}"
                )

        # Create detailed Instagram data
        instagram_data = {
            "platform": "Instagram",
            "type": "profile",
            "followers": followers,
            "following": following,
            "posts_count": posts_count,
            "engagement": engagement,
            "frequency": frequency,
            "is_verified": user_details.get("is_verified", "false"),
            "profile_image": user_details.get("img", ""),
            "content": (
                " | ".join(content_parts)
                if content_parts
                else "Limited content available"
            ),
            "real_data": True,
            "url": url,
            "recent_posts": timeline_data,
        }

        return instagram_data

    except Exception as e:
        logger.error(f"Error in detailed Instagram extraction for {username}: {str(e)}")
        return None


def extract_from_instagram(url, soup):
    """
    Extract content from an Instagram profile
    Now with enhanced data extraction option
    """
    # First try the specialized extraction
    detailed_data = extract_detailed_instagram(url)
    if detailed_data:
        logger.info(f"Successfully extracted detailed Instagram data from {url}")
        return detailed_data

    # Fall back to the original method if detailed extraction fails
    logger.info(f"Falling back to generic Instagram extraction for {url}")
    platform_config = PLATFORMS["instagram"]

    # Extract bio
    bio_texts = extract_text_from_selectors(soup, platform_config["bio_selectors"])
    bio = " ".join(bio_texts) if bio_texts else ""

    # Extract posts
    posts = extract_post_texts(soup, platform_config["post_selectors"])

    # Extract follower count
    page_text = soup.get_text()
    follower_count = extract_count_from_text(
        page_text, platform_config["follower_patterns"]
    )

    # Instagram typically has high engagement
    engagement_level = "High"

    # Estimate posting frequency from posts or page text
    posting_frequency = estimate_posting_frequency(posts, page_text)

    return {
        "platform": "Instagram",
        "type": platform_config["type"],
        "bio": bio,
        "posts": posts,
        "followers": follower_count,
        "engagement": engagement_level,
        "frequency": posting_frequency,
    }


# ---- Platform-Specific Extraction Functions ----


def extract_from_facebook(url, soup):
    """Extract content from a Facebook page"""
    platform_config = PLATFORMS["facebook"]

    # Extract bio/about content
    bio_texts = extract_text_from_selectors(soup, platform_config["bio_selectors"])
    bio = " ".join(bio_texts) if bio_texts else ""

    # Extract posts
    posts = extract_post_texts(soup, platform_config["post_selectors"])

    # Extract follower count
    page_text = soup.get_text()
    follower_count = extract_count_from_text(
        page_text, platform_config["follower_patterns"]
    )

    # Estimate engagement level based on likes and comments
    engagement_indicators = ["like", "comment", "share"]
    engagement_count = sum(
        1 for indicator in engagement_indicators if indicator in page_text.lower()
    )
    engagement_level = (
        "High"
        if engagement_count >= 2
        else "Medium" if engagement_count >= 1 else "Low"
    )

    # Estimate posting frequency
    posting_frequency = estimate_posting_frequency(posts, page_text)

    return {
        "platform": "Facebook",
        "type": platform_config["type"],
        "bio": bio,
        "posts": posts,
        "followers": follower_count,
        "engagement": engagement_level,
        "frequency": posting_frequency,
    }


def extract_from_twitter(url, soup):
    """Extract content from a Twitter profile"""
    platform_config = PLATFORMS["twitter"]

    # Extract bio
    bio_texts = extract_text_from_selectors(soup, platform_config["bio_selectors"])
    bio = " ".join(bio_texts) if bio_texts else ""

    # Extract tweets
    posts = extract_post_texts(soup, platform_config["post_selectors"])

    # Extract follower count
    page_text = soup.get_text()
    follower_count = extract_count_from_text(
        page_text, platform_config["follower_patterns"]
    )

    # Estimate engagement from retweets, likes, and replies
    engagement_indicators = ["retweet", "like", "reply", "favorite"]
    engagement_count = sum(
        1
        for post in posts
        for indicator in engagement_indicators
        if indicator.lower() in post.lower()
    )
    engagement_level = (
        "High"
        if engagement_count >= 5
        else "Medium" if engagement_count >= 2 else "Low"
    )

    # Estimate posting frequency
    posting_frequency = estimate_posting_frequency(posts, page_text)
    if not posting_frequency:
        # Twitter is typically high frequency
        posting_frequency = "Daily" if len(posts) >= 3 else "Weekly"

    return {
        "platform": "Twitter",
        "type": platform_config["type"],
        "bio": bio,
        "posts": posts,
        "followers": follower_count,
        "engagement": engagement_level,
        "frequency": posting_frequency,
    }


def extract_from_linkedin(url, soup):
    """Extract content from a LinkedIn page"""
    platform_config = PLATFORMS["linkedin"]

    # Extract bio/description
    bio_texts = extract_text_from_selectors(soup, platform_config["bio_selectors"])
    bio = " ".join(bio_texts) if bio_texts else ""

    # Extract posts
    posts = extract_post_texts(soup, platform_config["post_selectors"])

    # Extract follower count
    page_text = soup.get_text()
    follower_count = extract_count_from_text(
        page_text, platform_config["follower_patterns"]
    )

    # LinkedIn typically has more professional, moderate engagement
    engagement_indicators = ["comment", "like", "share", "reaction"]
    engagement_count = sum(
        1
        for post in posts
        for indicator in engagement_indicators
        if indicator.lower() in post.lower()
    )
    engagement_level = (
        "High"
        if engagement_count >= 5
        else "Medium" if engagement_count >= 2 else "Low"
    )

    # LinkedIn typically has lower posting frequency
    posting_frequency = "Weekly" if len(posts) >= 2 else "Bi-weekly"

    return {
        "platform": "LinkedIn",
        "type": platform_config["type"],
        "bio": bio,
        "posts": posts,
        "followers": follower_count,
        "engagement": engagement_level,
        "frequency": posting_frequency,
    }


def extract_from_youtube(url, soup):
    """Extract content from a YouTube channel"""
    platform_config = PLATFORMS["youtube"]

    # Extract channel description
    bio_texts = extract_text_from_selectors(soup, platform_config["bio_selectors"])
    bio = " ".join(bio_texts) if bio_texts else ""

    # Extract video titles and descriptions
    posts = extract_post_texts(soup, platform_config["post_selectors"])

    # Extract subscriber count
    page_text = soup.get_text()
    follower_count = extract_count_from_text(
        page_text, platform_config["follower_patterns"]
    )

    # YouTube engagement can be estimated from views, likes, and comments
    engagement_indicators = ["view", "like", "comment", "subscribe"]
    engagement_count = sum(
        1 for indicator in engagement_indicators if indicator in page_text.lower()
    )
    engagement_level = (
        "High"
        if engagement_count >= 3
        else "Medium" if engagement_count >= 2 else "Low"
    )

    # Estimate posting frequency (YouTube typically less frequent than social)
    posting_frequency = (
        "Weekly" if len(posts) >= 3 else "Bi-weekly" if len(posts) >= 1 else "Monthly"
    )

    return {
        "platform": "YouTube",
        "type": platform_config["type"],
        "bio": bio,
        "posts": posts,
        "followers": follower_count,
        "engagement": engagement_level,
        "frequency": posting_frequency,
    }


def extract_generic_content(url, soup, platform_name):
    """Extract content from a generic social media platform"""
    # Try to find the platform in our config
    platform_config = None
    for platform, config in PLATFORMS.items():
        if platform.lower() == platform_name.lower():
            platform_config = config
            break

    if not platform_config:
        # Create generic selectors
        platform_config = {
            "type": "profile",
            "bio_selectors": [
                ".bio",
                ".about",
                ".description",
                ".profile-info",
                '[itemprop="description"]',
                ".user-profile",
                ".profile-header",
            ],
            "post_selectors": [
                ".post",
                ".content",
                ".feed-item",
                ".status",
                "article",
                ".entry",
                ".media",
                ".card",
            ],
            "follower_patterns": [
                r"([\d,.]+\s*followers)",
                r"([\d,.]+\s*subscrib(er|ers))",
                r"([\d,.]+\s*following)",
                r"([\d,.]+\s*fans)",
                r"([\d,.]+\s*members)",
            ],
        }

    # Extract bio
    bio_texts = extract_text_from_selectors(soup, platform_config["bio_selectors"])
    bio = " ".join(bio_texts) if bio_texts else ""

    # Extract posts
    posts = extract_post_texts(soup, platform_config["post_selectors"])

    # Extract follower count
    page_text = soup.get_text()
    follower_count = extract_count_from_text(
        page_text, platform_config["follower_patterns"]
    )

    # Determine platform type
    platform_type = platform_config.get("type", "profile")

    # Generic engagement estimation
    engagement_indicators = ["like", "comment", "share", "view", "reaction"]
    engagement_count = sum(
        1
        for post in posts
        for indicator in engagement_indicators
        if indicator.lower() in post.lower()
    )
    engagement_level = (
        "High"
        if engagement_count >= 5
        else "Medium" if engagement_count >= 2 else "Low"
    )

    # Estimate posting frequency
    posting_frequency = estimate_posting_frequency(posts, page_text)

    return {
        "platform": platform_name.capitalize(),
        "type": platform_type,
        "bio": bio,
        "posts": posts,
        "followers": follower_count,
        "engagement": engagement_level,
        "frequency": posting_frequency,
    }


# ---- Main Extraction Function ----


def extract_social_content(social_links):
    """
    Extract content from social media platforms

    This function focuses on retrieving real data from social media sites
    through web scraping. It works directly with public content without requiring
    API authentication.

    Args:
        social_links: List of dictionaries containing platform and URL information

    Returns:
        List of dictionaries containing extracted social media content
    """
    social_content = []

    # Exit early if no social links
    if not social_links:
        logger.info("No social links provided")
        return social_content

    # Create a session for multiple requests
    session = get_requests_session()

    # Track domains we've already scraped to avoid duplicates
    scraped_domains = set()

    for link in social_links:
        try:
            platform_name = link.get("platform", "").lower()
            url = link.get("url", "")

            if not platform_name or not url:
                logger.warning(f"Skipping invalid social link: {link}")
                continue

            # Parse domain to avoid duplicate requests
            parsed_url = urlparse(url)
            domain = parsed_url.netloc

            # Skip if we've already scraped this domain
            if domain in scraped_domains:
                logger.info(f"Skipping duplicate domain: {domain}")
                continue

            scraped_domains.add(domain)
            logger.info(f"Processing {platform_name} at {url}")

            # Fetch page content
            html_content = fetch_page(url, session)
            if not html_content:
                logger.warning(f"Failed to fetch content from {url}")
                # Add a minimal entry to indicate we tried
                social_content.append(
                    {
                        "platform": platform_name.capitalize(),
                        "type": PLATFORMS.get(platform_name, {}).get("type", "profile"),
                        "content": f"Could not access content from {platform_name}",
                        "url": url,
                        "real_data": False,
                    }
                )
                continue

            # Parse HTML
            try:
                soup = BeautifulSoup(html_content, "html.parser")
                # Remove script and style elements
                for tag in soup(["script", "style", "noscript"]):
                    tag.decompose()
            except Exception as e:
                logger.error(f"Error parsing HTML from {url}: {str(e)}")
                continue

            # Extract content based on platform
            platform_data = None

            if platform_name == "facebook":
                platform_data = extract_from_facebook(url, soup)
            elif platform_name in ["twitter", "x"]:
                platform_data = extract_from_twitter(url, soup)
            elif platform_name == "instagram":
                platform_data = extract_from_instagram(url, soup)
            elif platform_name == "linkedin":
                platform_data = extract_from_linkedin(url, soup)
            elif platform_name == "youtube":
                platform_data = extract_from_youtube(url, soup)
            else:
                # Try to identify platform from URL if not specified
                if not platform_name:
                    detected_platform = identify_platform(url)
                    if detected_platform:
                        platform_name = detected_platform

                # Use generic extraction
                platform_data = extract_generic_content(url, soup, platform_name)

            if platform_data:
                # Convert posts and bio to a single content field
                content_parts = []

                # Handle special case for Instagram with recent_posts already extracted
                if platform_name == "instagram" and "recent_posts" in platform_data:
                    # Keep the recent_posts in the platform data
                    pass
                elif platform_data.get("bio"):
                    content_parts.append(
                        f"Bio: {clean_text_content(platform_data['bio'], 300)}"
                    )

                    posts = platform_data.get("posts", [])
                    for i, post in enumerate(posts):
                        content_parts.append(
                            f"Post {i+1}: {clean_text_content(post, 250)}"
                        )

                    # Combine into a single content field
                    if "content" not in platform_data:  # Only set if not already set
                        platform_data["content"] = (
                            " | ".join(content_parts)
                            if content_parts
                            else "Limited content available"
                        )

                # Add URL and real_data flag if not already set
                if "url" not in platform_data:
                    platform_data["url"] = url
                if "real_data" not in platform_data:
                    platform_data["real_data"] = bool(
                        platform_data.get("bio")
                        or platform_data.get("posts")
                        or platform_data.get("content")
                    )

                # Remove internal fields
                platform_data.pop("bio", None)
                platform_data.pop("posts", None)

                # Add to results
                social_content.append(platform_data)

                logger.info(
                    f"Successfully extracted content from {platform_name} at {url}"
                )
            else:
                logger.warning(f"No content extracted from {platform_name} at {url}")

        except Exception as e:
            logger.error(
                f"Error processing social link {platform_name} at {url}: {str(e)}"
            )

    # Sort social content by platform name for consistency
    social_content.sort(key=lambda x: x.get("platform", ""))

    return social_content
