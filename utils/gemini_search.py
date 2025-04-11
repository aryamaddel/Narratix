import os
import json
from typing import List, Dict, Any, Optional
import re
import requests
import time
import logging
from datetime import datetime
from urllib.parse import urlparse, quote_plus
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Set up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# Create handler if not already configured
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Try to import the Google Generative AI libraries
try:
    import google.generativeai as genai
    from google.generativeai import types
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        # Set the specific model that's known to work
        DEFAULT_MODEL = "gemini-2.5-pro-exp-03-25"
        try:
            # Still check available models for logging purposes
            models = genai.list_models()
            available_models = [m.name for m in models]
            logger.debug(f"Available Gemini models: {available_models}")
            
            # Check if our specific model is in the available models
            if f"models/{DEFAULT_MODEL}" in available_models or DEFAULT_MODEL in available_models:
                logger.info(f"Specified model {DEFAULT_MODEL} is available")
                GEMINI_AVAILABLE = True
            else:
                logger.warning(f"Specified model {DEFAULT_MODEL} not found in available models, but will try to use it anyway")
                GEMINI_AVAILABLE = True
        except Exception as e:
            # If we can't list models, still try to use the specified model
            logger.warning(f"Could not list Gemini models: {str(e)}, assuming {DEFAULT_MODEL} is available")
            GEMINI_AVAILABLE = True
    else:
        GEMINI_AVAILABLE = False
        DEFAULT_MODEL = None
        logger.warning("Gemini API key not found in environment variables")
except ImportError:
    GEMINI_AVAILABLE = False
    DEFAULT_MODEL = None
    logger.warning("Gemini libraries not installed")

# Constants imported from social.py
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

# Platform definitions imported from social.py
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
    # ...existing platform definitions...
}

# Copy the remainder of the PLATFORMS dictionary from social.py
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

# ---- Utility Functions from social.py ----

def get_requests_session():
    """Create a requests session with retry capability"""
    logger.debug("Creating new requests session with retry capability")
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
    logger.debug(f"Identifying platform for URL: {url}")
    domain = urlparse(url).netloc.lower()

    for platform, config in PLATFORMS.items():
        for platform_domain in config["domains"]:
            if platform_domain in domain:
                logger.debug(f"Identified platform: {platform}")
                return platform

    logger.debug("Could not identify platform from URL")
    return None


def fetch_page(url, session=None):
    """Fetch a web page with error handling"""
    logger.debug(f"Fetching page: {url}")
    if session is None:
        session = get_requests_session()

    try:
        # Add jitter to avoid rate limiting
        time.sleep(0.5 + (time.time() % 1))

        response = session.get(url, headers=HEADERS, timeout=DEFAULT_TIMEOUT)
        if response.status_code != 200:
            logger.warning(f"Failed to fetch {url}: Status code {response.status_code}")
            return None

        logger.debug(f"Successfully fetched page: {url}")
        return response.content
    except Exception as e:
        logger.error(f"Error fetching {url}: {str(e)}")
        return None


def extract_text_from_selectors(soup, selectors, min_length=5, max_results=1):
    """Extract text from multiple potential selectors"""
    logger.debug(f"Extracting text using {len(selectors)} selectors")
    results = []

    for selector in selectors:
        try:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text().strip()
                if text and len(text) >= min_length:
                    results.append(text)
                    if max_results and len(results) >= max_results:
                        logger.debug(f"Found {len(results)} text elements")
                        return results
        except Exception as e:
            logger.debug(f"Error with selector '{selector}': {str(e)}")
            continue

    logger.debug(f"Found {len(results)} text elements total")
    return results


def extract_post_texts(soup, post_selectors, max_posts=5, min_post_length=15):
    """Extract multiple post texts from a page"""
    logger.debug(f"Extracting posts using {len(post_selectors)} selectors")
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
                        logger.debug(f"Found maximum {max_posts} posts")
                        return posts
        except Exception as e:
            logger.debug(f"Error with post selector '{selector}': {str(e)}")
            continue

    logger.debug(f"Found {len(posts)} posts total")
    return posts


def extract_count_from_text(text, patterns):
    """Extract numeric count from text using multiple patterns"""
    if not text:
        logger.debug("No text provided for count extraction")
        return None

    for pattern in patterns:
        try:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                for match in matches:
                    # If we get a tuple from the regex capture groups, take the first non-empty value
                    if isinstance(match, tuple):
                        match = next((m for m in match if m), match[0])

                    # Clean the value
                    count_text = match.strip()

                    # If value exists, return it
                    if count_text:
                        logger.debug(f"Found count: {count_text} using pattern: {pattern}")
                        return count_text
        except Exception as e:
            logger.debug(f"Error with pattern '{pattern}': {str(e)}")
            continue

    # More aggressive search for numbers near follower-related words
    follower_keywords = ["follower", "subscriber", "following", "member", "like"]
    for keyword in follower_keywords:
        try:
            # Find sentences containing the keyword
            sentences = re.split(r"[.!?]", text)
            for sentence in sentences:
                if keyword.lower() in sentence.lower():
                    # Look for numbers in this sentence
                    number_match = re.search(r"([\d,.]+[kKmM]?)", sentence)
                    if number_match:
                        logger.debug(f"Found count: {number_match.group(1)} near keyword: {keyword}")
                        return number_match.group(1)
        except Exception as e:
            logger.debug(f"Error searching near keyword '{keyword}': {str(e)}")
            continue

    logger.debug("No count found in text")
    return None


def normalize_follower_count(count_text):
    """Convert follower count text to a normalized string format"""
    if not count_text:
        return None

    try:
        # Remove any non-numeric characters except K, M, k, m, comma and dot
        clean_count = re.sub(r"[^\d,.KkMm]", "", count_text.strip())

        # Handle K/M notation
        if "k" in clean_count.lower():
            # Remove the K and multiply by 1000
            numeric_part = re.sub(r"[kK]", "", clean_count)
            return f"{float(numeric_part.replace(',', '')) * 1000:.0f}"
        elif "m" in clean_count.lower():
            # Remove the M and multiply by 1000000
            numeric_part = re.sub(r"[mM]", "", clean_count)
            return f"{float(numeric_part.replace(',', '')) * 1000000:.0f}"
        else:
            # Just return the cleaned number
            return clean_count
    except Exception as e:
        logger.debug(f"Error normalizing count '{count_text}': {str(e)}")
        return count_text


def estimate_posting_frequency(posts, page_text):
    """Estimate posting frequency from content"""
    logger.debug(f"Estimating posting frequency from {len(posts)} posts")
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
            logger.debug(f"Posting frequency: Daily (based on indicator '{indicator}')")
            return "Daily"

    for indicator in weekly_indicators:
        if indicator in page_text.lower():
            logger.debug(f"Posting frequency: Weekly (based on indicator '{indicator}')")
            return "Weekly"

    # Estimate based on number of recent posts
    if recent_count >= 2:
        logger.debug(f"Posting frequency: Daily (based on {recent_count} recent posts)")
        return "Daily"
    elif len(posts) >= 4:
        logger.debug("Posting frequency: Weekly (based on post count)")
        return "Weekly"
    elif len(posts) >= 2:
        logger.debug("Posting frequency: Bi-weekly (based on post count)")
        return "Bi-weekly"
    else:
        logger.debug("Posting frequency: Monthly (default)")
        return "Monthly"


def clean_text_content(text, max_length=500):
    """Clean and truncate text content"""
    if not text:
        return ""

    # Remove excess whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # Truncate if too long
    truncated = len(text) > max_length
    if truncated:
        logger.debug(f"Text truncated from {len(text)} to {max_length} characters")
    
    return text[: max_length - 3] + "..." if truncated else text

# Import the remaining specialized functions from social.py for Instagram, Facebook, Twitter, etc.
# ...

# ---- Platform-Specific Extraction Functions ----
# (Add the platform-specific extraction functions from social.py)

def extract_from_facebook(url, soup):
    """Extract content from a Facebook page"""
    logger.info(f"Extracting Facebook content from: {url}")
    platform_config = PLATFORMS["facebook"]

    # Extract bio/about content
    bio_texts = extract_text_from_selectors(soup, platform_config["bio_selectors"])
    bio = " ".join(bio_texts) if bio_texts else ""

    # Extract posts
    posts = extract_post_texts(soup, platform_config["post_selectors"])

    # Extract follower count - enhanced approach for Facebook
    page_text = soup.get_text()
    follower_count = extract_count_from_text(
        page_text, platform_config["follower_patterns"]
    )

    # If still no follower count, try more specific selectors
    if not follower_count:
        # Try common Facebook follower/like display elements
        follower_elements = (
            soup.select("[data-key='followers_count']")
            or soup.select(".clearfix ._4bl9")
            or soup.select("._4-u2._6590._3xaf._4-u8")
        )

        for element in follower_elements:
            element_text = element.get_text()
            if any(
                keyword in element_text.lower()
                for keyword in ["follower", "like", "follow"]
            ):
                number_match = re.search(r"([\d,.]+[kKmM]?)", element_text)
                if number_match:
                    follower_count = number_match.group(1)
                    break

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

    result = {
        "platform": "Facebook",
        "type": platform_config["type"],
        "bio": bio,
        "posts": posts,
        "followers": follower_count,
        "engagement": engagement_level,
        "frequency": posting_frequency,
    }
    
    logger.debug(f"Facebook extraction results: followers={follower_count}, posts={len(posts)}, engagement={engagement_level}")
    return result


def extract_from_twitter(url, soup):
    """Extract content from a Twitter profile"""
    logger.info(f"Extracting Twitter content from: {url}")
    platform_config = PLATFORMS["twitter"]

    # Extract bio
    bio_texts = extract_text_from_selectors(soup, platform_config["bio_selectors"])
    bio = " ".join(bio_texts) if bio_texts else ""

    # Extract tweets
    posts = extract_post_texts(soup, platform_config["post_selectors"])

    # Extract follower count - enhanced for Twitter
    page_text = soup.get_text()
    follower_count = extract_count_from_text(
        page_text, platform_config["follower_patterns"]
    )

    # If still no follower count, try more specific Twitter selectors
    if not follower_count:
        # Try common Twitter follower count elements
        follower_elements = (
            soup.select('[data-testid="UserProfileHeader_Items"]')
            or soup.select('[data-nav="followers"]')
            or soup.select(".ProfileNav-item--followers")
        )

        for element in follower_elements:
            element_text = element.get_text()
            if "follower" in element_text.lower():
                number_match = re.search(r"([\d,.]+[kKmM]?)", element_text)
                if number_match:
                    follower_count = number_match.group(1)
                    break

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

    logger.debug(f"Twitter extraction results: followers={follower_count}, posts={len(posts)}, engagement={engagement_level}")
    return {
        "platform": "Twitter",
        "type": platform_config["type"],
        "bio": bio,
        "posts": posts,
        "followers": follower_count,
        "engagement": engagement_level,
        "frequency": posting_frequency,
    }

# Add the other platform-specific functions

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
    logger.info(f"Extracting social content from {len(social_links) if social_links else 0} links")
    social_content = []

    # Exit early if no social links
    if not social_links:
        logger.info("No social links provided, returning empty results")
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
                continue

            # Parse domain to avoid duplicate requests
            parsed_url = urlparse(url)
            domain = parsed_url.netloc

            # Skip if we've already scraped this domain
            if domain in scraped_domains:
                continue

            scraped_domains.add(domain)

            # Fetch page content
            html_content = fetch_page(url, session)
            if not html_content:
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
            except Exception:
                continue

            # Extract content based on platform
            platform_data = None

            if platform_name == "facebook":
                platform_data = extract_from_facebook(url, soup)
            elif platform_name in ["twitter", "x"]:
                platform_data = extract_from_twitter(url, soup)
            # Add conditional blocks for other platforms
            else:
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

                # Normalize follower count if present
                if "followers" in platform_data:
                    platform_data["followers"] = normalize_follower_count(
                        platform_data["followers"]
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

        except Exception:
            pass  # Silently ignore errors

    # Sort social content by platform name for consistency
    social_content.sort(key=lambda x: x.get("platform", ""))
    logger.info(f"Extracted content from {len(social_content)} social profiles")

    return social_content


# ---- Enhanced Search Functions ----

def search_google_for_brand_info(brand_name, include_socials=True):
    """
    Search Google for brand information and social media profiles
    
    Args:
        brand_name: Brand name to search for
        include_socials: Whether to include social media specific searches
        
    Returns:
        Dictionary with brand information and found social profiles
    """
    logger.info(f"Searching Google for brand info: {brand_name}")
    results = {
        "brand_info": {},
        "social_profiles": []
    }
    
    if not brand_name:
        logger.warning("No brand name provided for search")
        return results
    
    # Create session for multiple requests
    session = get_requests_session()
    
    try:
        # First search: Basic brand information
        main_search_query = f"{brand_name} company information"
        main_search_url = f"https://www.google.com/search?q={quote_plus(main_search_query)}"
        
        main_response = fetch_page(main_search_url, session)
        if main_response:
            soup = BeautifulSoup(main_response, "html.parser")
            
            # Extract potential description from search result
            description = ""
            for selector in [".kno-rdesc span", ".hgKElc", ".VwiC3b", ".ILfuVd"]:
                desc_elements = soup.select(selector)
                if desc_elements:
                    description = desc_elements[0].get_text().strip()
                    break
                    
            results["brand_info"] = {
                "brand_name": brand_name,
                "description": description
            }
        
        # Only perform social media searches if requested
        if include_socials:
            # Define common social platforms to search for
            social_platforms = {
                "instagram": "Instagram",
                "facebook": "Facebook",
                "twitter": "Twitter",
                "linkedin": "LinkedIn",
                "youtube": "YouTube",
                "tiktok": "TikTok"
            }
            
            for platform_key, platform_name in social_platforms.items():
                # Create a specific search query for this platform
                search_query = f"{brand_name} {platform_name} official account followers"
                search_url = f"https://www.google.com/search?q={quote_plus(search_query)}"
                
                # Add some delay to avoid being blocked
                time.sleep(0.5 + (time.time() % 1))
                
                response = fetch_page(search_url, session)
                if not response:
                    continue
                    
                soup = BeautifulSoup(response, "html.parser")
                page_text = soup.get_text()
                
                # Look for URLs for this platform
                platform_domains = PLATFORMS.get(platform_key, {}).get("domains", [])
                if not platform_domains:
                    continue
                    
                domain_pattern = "|".join(platform_domains).replace(".", r"\.")
                url_pattern = fr"https?://(?:www\.)?(?:{domain_pattern})/([\\w\\.\-]+)"
                
                matches = re.findall(url_pattern, response.decode('utf-8', errors='ignore'))
                
                # Initialize variables before the loop
                profile_url = None
                username = None
                
                if matches:
                    # Look for the first URL that looks like a profile/username
                    for match in matches:
                        # Avoid search results and other non-profile paths
                        if "search" in match or match.startswith("?") or match.startswith("hashtag"):
                            continue
                            
                        # Clean up the match to get just username
                        username = match.split("/")[0] if "/" in match else match
                        username = username.split("?")[0] if "?" in username else username
                        
                        if username and len(username) > 1:
                            # Construct the URL
                            if platform_key == "instagram":
                                profile_url = f"https://www.instagram.com/{username}/"
                            elif platform_key == "twitter":
                                profile_url = f"https://twitter.com/{username}"
                            elif platform_key == "facebook":
                                profile_url = f"https://www.facebook.com/{username}"
                            elif platform_key == "linkedin":
                                profile_url = f"https://www.linkedin.com/company/{username}"
                            elif platform_key == "youtube":
                                profile_url = f"https://www.youtube.com/{username}"
                            elif platform_key == "tiktok":
                                profile_url = f"https://www.tiktok.com/@{username}"
                            break
                
                # If we found a profile URL
                if profile_url:
                    # Look for follower counts in the search results
                    follower_count = None
                    follower_patterns = PLATFORMS.get(platform_key, {}).get("follower_patterns", [])
                    
                    # Add generic follower patterns
                    follower_patterns.extend([
                        r"([\d,.]+[kKmM]?)\s*followers",
                        r"([\d,.]+[kKmM]?)\s*subscribers", 
                        r"([\d,.]+[kKmM]?)\s*following",
                        r"([\d,.]+[kKmM]?)\s*likes"
                    ])
                    
                    for pattern in follower_patterns:
                        matches = re.search(pattern, page_text, re.IGNORECASE)
                        if matches:
                            follower_count = matches.group(1)
                            break
                    
                    # Create profile entry
                    profile = {
                        "platform": platform_name,
                        "url": profile_url,
                        "followers": normalize_follower_count(follower_count) if follower_count else "Unknown",
                        "frequency": "Unknown",
                        "engagement": "Medium",
                        "content": f"Found via Google Search: {username}",
                        "search_based": True
                    }
                    
                    results["social_profiles"].append(profile)
        
        # Log result summary
        logger.info(f"Search results: found {len(results['social_profiles'])} social profiles")
        return results
        
    except Exception as e:
        logger.error(f"Error in Google search for {brand_name}: {str(e)}")
        # If something goes wrong, return the partial results
        return results

# ---- Gemini Functions (Keep these from the existing gemini_search.py) ----

def search_website_content(url: str) -> Dict[str, Any]:
    """
    Use Gemini API to extract content information from a website
    
    Args:
        url: Website URL to analyze
        
    Returns:
        Dictionary containing website content information
    """
    logger.info(f"Searching website content: {url}")
    
    if not GEMINI_AVAILABLE or not DEFAULT_MODEL:
        logger.info("Gemini not available, using traditional crawler")
        from utils.crawler import extract_website_content
        return extract_website_content(url)
    
    try:
        # Use Gemini to extract website content
        prompt = f"""
        Please analyze this website: {url}
        
        Extract the following information:
        1. Brand name
        2. Brief description of the brand/company
        3. Main content from the website that describes what they do
        
        Format your response as JSON with the following structure:
        {{
            "brand_name": "Name of the brand",
            "description": "Brief description",
            "content": "Longer content about what they do"
        }}
        """
        
        # Generate content with Gemini using the available model
        model = genai.GenerativeModel(DEFAULT_MODEL)
        logger.debug(f"Sending content extraction prompt to Gemini using model {DEFAULT_MODEL}")
        response = model.generate_content(prompt)
        
        if response and hasattr(response, "text"):
            logger.debug("Received response from Gemini API")
            # Parse the JSON response
            try:
                # Extract JSON from the response text
                json_str = response.text.strip()
                # Handle case where response might have markdown code block
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0].strip()
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].split("```")[0].strip()
                    
                return json.loads(json_str)
            except Exception as e:
                # If parsing fails, return a simple structure
                return {
                    "brand_name": "",
                    "description": "",
                    "content": response.text,
                    "error": str(e)
                }
        else:
            logger.error("Empty or invalid response from Gemini API")
            raise Exception("Failed to get response from Gemini API")
            
    except Exception as e:
        logger.warning(f"Error using Gemini for website content: {str(e)}, falling back to crawler")
        # Fall back to crawler-based extraction
        from utils.crawler import extract_website_content
        return extract_website_content(url)

def search_social_media(url: str, brand_name: str) -> List[Dict[str, Any]]:
    """
    Use Gemini API to find and analyze social media profiles for a website/brand
    
    Args:
        url: Website URL to analyze
        brand_name: Name of the brand to search for
        
    Returns:
        List of dictionaries containing social media information
    """
    logger.info(f"Searching social media for: {brand_name} ({url})")
    
    if not GEMINI_AVAILABLE or not DEFAULT_MODEL:
        logger.info("Gemini not available, using traditional methods")
        # Use our unified function
        return get_social_profiles(brand_name=brand_name, website_url=url)
    
    try:
        # First attempt: Use search-based approach
        logger.debug("Starting with search-based approach")
        search_results = search_google_for_brand_info(brand_name, include_socials=True)
        
        # Use the search results to enhance Gemini's prompt
        search_context = ""
        if search_results and search_results.get("social_profiles"):
            search_context = "Here are some social profiles I found via search:\n\n"
            for profile in search_results.get("social_profiles", []):
                platform = profile.get("platform", "Unknown")
                profile_url = profile.get("url", "")
                followers = profile.get("followers", "Unknown")
                search_context += f"- {platform}: {profile_url} (Followers: {followers})\n"
        
        # Use Gemini to analyze social profiles with enhanced knowledge from search
        prompt = f"""
        Please find social media profiles for this brand:
        Brand name: {brand_name}
        Website: {url}
        
        {search_context}
        
        For each social media profile you can find, extract:
        1. Platform name (Facebook, Instagram, Twitter, LinkedIn, etc.)
        2. Profile URL
        3. Approximate follower count
        4. Posting frequency (Daily, Weekly, Monthly)
        5. Engagement level (High, Medium, Low)
        6. Sample content
        
        Format your response as JSON with an array of social media profiles:
        [
            {{
                "platform": "platform name",
                "url": "profile url",
                "followers": "follower count",
                "frequency": "posting frequency",
                "engagement": "engagement level",
                "content": "sample of recent content"
            }}
        ]
        """
        
        # Generate content with Gemini using the available model
        model = genai.GenerativeModel(DEFAULT_MODEL)
        logger.debug(f"Sending social media analysis prompt to Gemini using model {DEFAULT_MODEL}")
        response = model.generate_content(prompt)
        
        # Rest of the function remains unchanged
        if response and hasattr(response, "text"):
            logger.debug("Received response from Gemini API")
            # Parse the JSON response
            try:
                # Extract JSON from the response text
                json_str = response.text.strip()
                # Handle case where response might have markdown code block
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0].strip()
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].split("```")[0].strip()
                    
                social_data = json.loads(json_str)
                
                # Ensure all profiles have required fields
                for profile in social_data:
                    profile.setdefault("platform", "Unknown")
                    profile.setdefault("url", "")
                    profile.setdefault("followers", "N/A")
                    profile.setdefault("frequency", "Unknown")
                    profile.setdefault("engagement", "Medium")
                    profile.setdefault("content", "")
                    profile["real_data"] = True  # Mark as from API
                
                # Merge with any detected social profiles from search
                if search_results and search_results.get("social_profiles"):
                    # Create a map of platforms we already have from Gemini
                    existing_platforms = {p.get("platform", "").lower(): True for p in social_data}
                    
                    # Add any platforms from search that weren't found by Gemini
                    for search_profile in search_results.get("social_profiles", []):
                        platform = search_profile.get("platform", "").lower()
                        if platform and platform not in existing_platforms:
                            social_data.append(search_profile)
                
                logger.info(f"Found {len(social_data)} social profiles via Gemini")
                return social_data
            except Exception as json_error:
                logger.error(f"Error parsing Gemini response: {str(json_error)}")
                # Fall back to search-based approach if JSON parsing fails
                if search_results and search_results.get("social_profiles"):
                    return search_results.get("social_profiles")
                else:
                    # If both Gemini and search failed, use traditional scraping
                    pass
                
        # If anything fails, fall back to our unified approach
        logger.warning("Failed to get valid response from Gemini API, falling back to unified approach")
        return get_social_profiles(brand_name=brand_name, website_url=url)
            
    except Exception as e:
        logger.error(f"Error in social media search: {str(e)}, falling back to unified approach")
        # Fall back to our unified approach
        return get_social_profiles(brand_name=brand_name, website_url=url)

# ---- Unified Flow ----

def get_social_profiles(brand_name=None, website_url=None):
    """
    Unified function to get social media profiles using both search and scraping approaches
    
    Args:
        brand_name: Name of the brand (for search-based approach)
        website_url: Website URL (for scraping-based approach)
        
    Returns:
        List of dictionaries containing social media information
    """
    logger.info(f"Getting social profiles for brand: {brand_name}, website: {website_url}")
    results = []
    
    # First attempt: Use search-based approach if brand_name is provided
    if brand_name:
        try:
            logger.debug("Attempting search-based approach")
            search_results = search_google_for_brand_info(brand_name, include_socials=True)
            if search_results and search_results.get("social_profiles"):
                results.extend(search_results.get("social_profiles"))
                logger.info(f"Found {len(search_results.get('social_profiles'))} profiles via search")
        except Exception as e:
            logger.error(f"Error in search-based approach: {str(e)}")
            pass
    
    # Second attempt/fallback: Use traditional scraping if we have a website URL
    if website_url:
        try:
            logger.debug("Attempting scrape-based approach")
            from utils.crawler import extract_social_links
            social_links = extract_social_links(website_url)
            scrape_results = extract_social_content(social_links)
            
            # If we got search results, merge them with scraped results
            if results:
                # Create a map of platforms we already have
                existing_platforms = {p.get("platform", "").lower(): p for p in results}
                
                # Add or update with scrape results
                for profile in scrape_results:
                    platform = profile.get("platform", "").lower()
                    if platform not in existing_platforms or profile.get("real_data", False):
                        results.append(profile)
            else:
                # If no search results, just use scrape results
                results = scrape_results
            
            logger.info(f"Found {len(scrape_results)} profiles via scraping")
        except Exception as e:
            logger.error(f"Error in scrape-based approach: {str(e)}")
            pass
    
    # Deduplicate results by platform
    deduplicated = {}
    for profile in results:
        platform = profile.get("platform", "").lower()
        if platform not in deduplicated or profile.get("real_data", False):
            deduplicated[platform] = profile
    
    logger.info(f"Returning {len(deduplicated)} unique social profiles")
    return list(deduplicated.values())

# ---- Generator Functions ----

def generate_brand_story(brand_name: str, brand_description: str, analysis: Dict[str, Any], 
                        social_content: List[Dict[str, Any]]) -> str:
    """
    Generate a brand story based on the analyzed content
    
    Args:
        brand_name: Name of the brand
        brand_description: Brief description of the brand
        analysis: Content analysis data
        social_content: Social media profiles data
        
    Returns:
        Formatted brand story as markdown text
    """
    logger.info(f"Generating brand story for: {brand_name}")
    
    if GEMINI_AVAILABLE and DEFAULT_MODEL:
        try:
            # Add null checks for analysis parameters
            keywords = ", ".join(analysis.get("keywords", ["professional", "quality", "service"]) if analysis else ["professional", "quality", "service"])
            key_values = ", ".join(analysis.get("key_values", ["Quality", "Innovation", "Service"]) if analysis else ["Quality", "Innovation", "Service"])
            
            # Get tone information with null check
            tone = analysis.get("tone_analysis", {}) if analysis else {}
            top_tones = sorted(tone.items(), key=lambda x: x[1], reverse=True)[:3] if tone else []
            tone_description = ", ".join([f"{t[0]} ({int(t[1]*100)}%)" for t in top_tones]) if top_tones else "Professional, Informative"
            
            # Social media context
            social_context = "The brand maintains presence on "
            if social_content:
                platforms = [s.get("platform", "social media") for s in social_content]
                social_context += ", ".join(platforms)
                followers_info = [s for s in social_content if s.get("followers") not in ["N/A", "Unknown", ""]]
                if followers_info:
                    # Use safe max function
                    max_followers = max(followers_info, key=lambda x: int(x.get("followers", "0").replace(",", "").replace(".", "").strip()) if isinstance(x.get("followers", "0"), str) and x.get("followers", "0").replace(",", "").replace(".", "").strip().isdigit() else 0)
                    social_context += f". Most active on {max_followers.get('platform', 'social media')}."
            else:
                social_context = "Limited social media presence detected."
            
            # Use Gemini to generate the brand story with the available model
            prompt = f"""
            Create a comprehensive brand story for {brand_name}. 
            
            About the brand:
            - Description: {brand_description}
            - Key values: {key_values}
            - Key keywords: {keywords}
            - Brand tone: {tone_description}
            - {social_context}
            
            Structure the brand story in markdown format with these sections:
            1. Brand Overview (brief introduction)
            2. Mission and Values (what the brand stands for)
            3. Brand Voice and Personality (how the brand communicates)
            4. Audience and Positioning (who the brand speaks to and its market position)
            5. Visual Identity (brief description of visual elements that represent the brand)
            6. Content Strategy (recommendations for content that aligns with the brand)
            
            Make it professional but engaging, around 400-500 words total.
            """
            
            # Generate content with Gemini
            model = genai.GenerativeModel(DEFAULT_MODEL)
            logger.debug(f"Sending brand story prompt to Gemini using model {DEFAULT_MODEL}")
            response = model.generate_content(prompt)
            
            if response and hasattr(response, "text"):
                logger.info("Successfully generated brand story with Gemini")
                return response.text
            else:
                logger.error("Empty or invalid response from Gemini API")
                raise Exception("Failed to get response from Gemini API")
                
        except Exception as e:
            logger.warning(f"Error generating brand story with Gemini: {str(e)}, falling back to template")
            # Fall back to a basic template
            pass
    else:
        logger.info("Gemini not available, using template brand story")
    
    # Fallback template if Gemini fails or isn't available
    story = f"""# {brand_name}: Brand Story

## Brand Overview
{brand_description}

## Mission and Values
{brand_name} is committed to delivering exceptional value through innovation and quality service.

## Brand Voice and Personality
The brand communicates with a professional and approachable tone, focusing on clarity and expertise.

## Audience and Positioning
{brand_name} serves customers looking for reliable solutions in its market segment.

## Visual Identity
The visual identity features a clean, professional aesthetic that conveys trust and expertise.

## Content Strategy
Content should emphasize the brand's key values and demonstrate expertise while maintaining consistency across all platforms.
"""
    logger.info("Generated template-based brand story")
    return story

def generate_visual_profile(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate visual profile recommendations based on content analysis
    
    Args:
        analysis: Content analysis data
        
    Returns:
        Visual profile recommendations
    """
    logger.info("Generating visual profile recommendations")
    # Default visual profile
    default_profile = {
        "color_palette": {
            "primary": "#0A3D62",
            "secondary": "#3E92CC",
            "accent": "#D8D8D8",
            "neutral": "#F5F5F5",
            "highlight": "#2E86AB",
        },
        "font_style": {
            "heading": "Montserrat or Georgia",
            "body": "Open Sans or Roboto",
            "style": "Clean, structured typography with proper hierarchy",
        },
        "image_style": "Polished, high-quality photography with clean compositions.",
        "tone_indicators": [
            {"name": "Professional", "value": 0.7},
            {"name": "Informative", "value": 0.6},
            {"name": "Friendly", "value": 0.4},
        ],
    }
    
    if GEMINI_AVAILABLE and DEFAULT_MODEL:
        try:
            # Extract tone information with null check
            tone = analysis.get("tone_analysis", {}) if analysis else {}
            tone_str = ", ".join([f"{k}: {v:.1f}" for k, v in tone.items()]) if tone else "Professional: 0.7, Informative: 0.6"
            
            # Extract keywords and values with null checks
            keywords = ", ".join(analysis.get("keywords", ["professional", "quality"]) if analysis else ["professional", "quality"])
            values = ", ".join(analysis.get("key_values", ["Quality", "Service"]) if analysis else ["Quality", "Service"])
            
            # Use Gemini to generate visual profile recommendations with the available model
            prompt = f"""
            Create a visual brand profile based on these brand characteristics:
            - Tone profile: {tone_str}
            - Keywords: {keywords}
            - Key values: {values}
            
            Provide recommendations for:
            1. Color palette (primary, secondary, accent, neutral, and highlight colors as hex codes)
            2. Font style (heading font, body font, and overall typography style)
            3. Image style guidance
            4. Top 3 tone indicators with values from 0-1
            
            Format response as JSON with this structure:
            {{
                "color_palette": {{
                    "primary": "#hex",
                    "secondary": "#hex",
                    "accent": "#hex",
                    "neutral": "#hex",
                    "highlight": "#hex"
                }},
                "font_style": {{
                    "heading": "font names",
                    "body": "font names",
                    "style": "description"
                }},
                "image_style": "description",
                "tone_indicators": [
                    {{"name": "tone1", "value": 0.x}},
                    {{"name": "tone2", "value": 0.x}},
                    {{"name": "tone3", "value": 0.x}}
                ]
            }}
            """
            
            # Generate content with Gemini
            model = genai.GenerativeModel(DEFAULT_MODEL)
            logger.debug(f"Sending visual profile prompt to Gemini using model {DEFAULT_MODEL}")
            response = model.generate_content(prompt)
            
            # Rest of the function remains unchanged
            if response and hasattr(response, "text"):
                logger.debug("Received response from Gemini API")
                # Parse the JSON response
                try:
                    # Extract JSON from the response text
                    json_str = response.text.strip()
                    # Handle case where response might have markdown code block
                    if "```json" in json_str:
                        json_str = json_str.split("```json")[1].split("```")[0].strip()
                    elif "```" in json_str:
                        json_str = json_str.split("```")[1].split("```")[0].strip()
                        
                    visual_profile = json.loads(json_str)
                    logger.info("Successfully generated visual profile with Gemini")
                    return visual_profile
                except Exception as e:
                    logger.error(f"Error parsing Gemini response: {str(e)}")
                    # Return default if JSON parsing fails
                    return default_profile
            else:
                logger.error("Empty or invalid response from Gemini API")
                return default_profile
                
        except Exception as e:
            logger.warning(f"Error generating visual profile: {str(e)}, using default")
            # Fall back to the default profile
            return default_profile
    
    # Return the default profile if Gemini isn't available
    logger.info("Using default visual profile (Gemini unavailable or failed)")
    return default_profile

def generate_consistency_score(website_content: Dict[str, Any], 
                              social_content: List[Dict[str, Any]],
                              analysis: Dict[str, Any]) -> int:
    """
    Calculate a brand consistency score based on website and social media content
    
    Args:
        website_content: Website content data
        social_content: Social media profiles data
        analysis: Content analysis data
        
    Returns:
        Consistency score (0-100)
    """
    logger.info("Generating brand consistency score")
    # Start with a base score
    score = 70
    
    if GEMINI_AVAILABLE and DEFAULT_MODEL:
        try:
            # Extract social platforms for context with null checks
            platforms = []
            if social_content:
                for social in social_content:
                    if social.get("platform"):
                        platforms.append(social.get("platform"))
            platforms_str = ", ".join(platforms) if platforms else "No social platforms detected"
            
            # Handle null analysis
            keywords = analysis.get("keywords", ["Unknown"]) if analysis else ["Unknown"]
            
            # Use Gemini to calculate a consistency score with the available model
            prompt = f"""
            Calculate a brand consistency score (0-100) based on this information:
            
            Website content detected: {"Yes" if website_content else "Limited or None"}
            Social platforms detected: {platforms_str}
            Keywords identified: {", ".join(keywords)}
            
            Factors to consider:
            1. Presence across multiple platforms
            2. Consistent messaging across platforms
            3. Brand voice clarity
            
            Return only the numeric score (0-100) with no additional text.
            """
            
            # Generate content with Gemini
            model = genai.GenerativeModel(DEFAULT_MODEL)
            logger.debug(f"Sending consistency score prompt to Gemini using model {DEFAULT_MODEL}")
            response = model.generate_content(prompt)
            
            if response and hasattr(response, "text"):
                # Parse the score
                try:
                    score_text = response.text.strip()
                    # Extract just the number
                    score_match = re.search(r'\b(\d{1,3})\b', score_text)
                    if score_match:
                        numeric_score = int(score_match.group(1))
                        # Validate the score is in range
                        if 0 <= numeric_score <= 100:
                            logger.info(f"Generated consistency score with Gemini: {numeric_score}")
                            return numeric_score
                        else:
                            logger.warning(f"Gemini score out of range: {numeric_score}, falling back to manual calculation")
                except Exception as e:
                    logger.error(f"Error parsing Gemini score: {str(e)}")
                    # Continue with calculating score manually
                    pass
        except Exception as e:
            logger.warning(f"Error generating consistency score with Gemini: {str(e)}")
            # Fall back to calculating score manually
            pass
    
    # Manual calculation if Gemini fails or isn't available
    logger.info("Using manual consistency score calculation")
    
    # Adjust score based on social media presence
    if social_content:
        score += min(len(social_content) * 5, 15)  # Up to +15 for social presence
        logger.debug(f"Adjusted score for social presence: +{min(len(social_content) * 5, 15)}")
    else:
        score -= 10  # Penalty for no social presence
        logger.debug("Adjusted score for missing social presence: -10")
    
    # Adjust for content analysis
    if analysis:
        # If we have keywords, that's a good sign
        if analysis.get("keywords") and len(analysis.get("keywords", [])) >= 3:
            score += 5
            logger.debug("Adjusted score for keywords: +5")
            
        # If we have tone analysis, that's also good
        if analysis.get("tone_analysis") and len(analysis.get("tone_analysis", {})) >= 3:
            score += 5
            logger.debug("Adjusted score for tone analysis: +5")
            
        # If we have key values identified
        if analysis.get("key_values") and len(analysis.get("key_values", [])) >= 2:
            score += 5
            logger.debug("Adjusted score for key values: +5")
    else:
        score -= 10  # Penalty for limited analysis
        logger.debug("Adjusted score for limited analysis: -10")
    
    # Ensure score stays within 0-100 range
    final_score = max(0, min(score, 100))
    logger.info(f"Calculated manual consistency score: {final_score}")
    return final_score

# Add the missing extract_generic_content function
def extract_generic_content(url, soup, platform_name):
    """Generic extraction for platforms without specific implementations"""
    logger.info(f"Using generic extraction for {platform_name} - {url}")
    
    if not platform_name or platform_name not in PLATFORMS:
        # Try to identify the platform
        platform_name = identify_platform(url)
        if not platform_name:
            logger.warning(f"Could not identify platform for URL: {url}")
            return None

    platform_config = PLATFORMS.get(platform_name, {})
    if not platform_config:
        logger.warning(f"No configuration found for platform: {platform_name}")
        return None

    # Extract bio/about content
    bio_texts = extract_text_from_selectors(
        soup, platform_config.get("bio_selectors", [])
    )
    bio = " ".join(bio_texts) if bio_texts else ""

    # Extract posts
    posts = extract_post_texts(soup, platform_config.get("post_selectors", []))

    # Extract follower count
    page_text = soup.get_text()
    follower_count = extract_count_from_text(
        page_text, platform_config.get("follower_patterns", [])
    )

    # Default engagement and frequency
    engagement_level = "Medium"
    posting_frequency = estimate_posting_frequency(posts, page_text)

    # Create the result dictionary with special handling for YouTube
    result = {
        "platform": platform_name.capitalize(),
        "type": platform_config.get("type", "profile"),
        "bio": bio,
        "posts": posts,
        "engagement": engagement_level,
        "frequency": posting_frequency,
    }

    # Use "subscribers" field name for YouTube, "followers" for everything else
    if platform_name.lower() == "youtube":
        result["subscribers"] = follower_count
        logger.debug(f"YouTube extraction results: subscribers={follower_count}, posts={len(posts)}")
    else:
        result["followers"] = follower_count
        logger.debug(f"{platform_name} extraction results: followers={follower_count}, posts={len(posts)}")

    return result
