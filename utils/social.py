import requests
import logging
import re
import time
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


def extract_from_instagram(url, soup):
    """Extract content from an Instagram profile"""
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

                if platform_data.get("bio"):
                    content_parts.append(
                        f"Bio: {clean_text_content(platform_data['bio'], 300)}"
                    )

                posts = platform_data.get("posts", [])
                for i, post in enumerate(posts):
                    content_parts.append(f"Post {i+1}: {clean_text_content(post, 250)}")

                # Combine into a single content field
                platform_data["content"] = (
                    " | ".join(content_parts)
                    if content_parts
                    else "Limited content available"
                )

                # Add URL and real_data flag
                platform_data["url"] = url
                platform_data["real_data"] = bool(
                    platform_data.get("bio") or platform_data.get("posts")
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
