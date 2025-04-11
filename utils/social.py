import requests
import re
import time
import json
from datetime import datetime
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Try to import optional dependencies
try:
    from seleniumwire import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

try:
    import playwright.sync_api as playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

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
            r"([\d,.]+[kKmM]?)\s*people\s*like\s*this",
            r"([\d,.]+[kKmM]?)\s*likes",
            r"([\d,.]+[kKmM]?)\s*followers",
            r"([\d,\.]+[kKmM]?)\s*Followers",
            r"Followers:\s*([\d,\.]+[kKmM]?)",
            r"([0-9,.]+[kKmM]?)\s*people follow this",
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
            r"(\d+[\d,.]*[kKmM]?)\s*(?:Followers|followers)",
            r"Followers:\s*(\d+[\d,.]*[kKmM]?)",
            r"([0-9,.]+[kKmM]?)\s*Followers",
            r"Followers\s*([0-9,.]+[kKmM]?)",
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
        "follower_patterns": [
            r"([\d,.]+[kKmM]?)\s*followers",
            r"Followers\s*([\d,.]+[kKmM]?)",
            r"([0-9,.]+[kKmM]?)\s*Followers",
            r"follower[s]?\s*([0-9,.]+[kKmM]?)",
        ],
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
        # Add jitter to avoid rate limiting
        time.sleep(0.5 + (time.time() % 1))

        response = session.get(url, headers=HEADERS, timeout=DEFAULT_TIMEOUT)
        if response.status_code != 200:
            return None

        return response.content
    except Exception as e:
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
    if not text:
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

                        return count_text
        except Exception as e:

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

                        return number_match.group(1)
        except Exception:
            continue

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

        return count_text


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


# New API-based extraction methods
def extract_from_twitter_api(username):
    """
    Extract Twitter data using the new guest token method
    (doesn't require developer account)
    """
    try:
        # Get a guest token
        session = requests.Session()
        response = session.post(
            "https://api.twitter.com/1.1/guest/activate.json",
            headers={"Authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs=1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"}
        )
        guest_token = json.loads(response.text)["guest_token"]
        
        # Use the token to get user data
        headers = {
            "Authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs=1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
            "x-guest-token": guest_token
        }
        
        # Get user data
        user_response = session.get(
            f"https://api.twitter.com/graphql/NimuplG1OB7Fd2btCLdBOw/UserByScreenName?variables=%7B%22screen_name%22%3A%22{username}%22%2C%22withSafetyModeUserFields%22%3Atrue%7D",
            headers=headers
        )
        
        if user_response.status_code == 200:
            user_data = json.loads(user_response.text)
            user = user_data.get("data", {}).get("user", {})
            if not user:
                return None
                
            result = user.get("result", {})
            legacy = result.get("legacy", {})
            
            return {
                "platform": "Twitter",
                "type": "profile",
                "followers": str(legacy.get("followers_count", 0)),
                "following": str(legacy.get("friends_count", 0)),
                "bio": result.get("legacy", {}).get("description", ""),
                "content": result.get("legacy", {}).get("description", ""),
                "engagement": "Medium",
                "frequency": "Daily" if legacy.get("statuses_count", 0) > 1000 else "Weekly",
                "real_data": True,
                "url": f"https://twitter.com/{username}"
            }
    except Exception as e:
        print(f"Twitter API error: {str(e)}")
        return None

def extract_instagram_with_graphql(username):
    """Extract Instagram data using the GraphQL API"""
    try:
        # Try to extract data using Instagram's public GraphQL endpoint
        session = requests.Session()
        url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "X-IG-App-ID": "936619743392459",  # Public Instagram Web App ID
            "X-Requested-With": "XMLHttpRequest",
            "Connection": "keep-alive",
            "Referer": f"https://www.instagram.com/{username}/",
            "Origin": "https://www.instagram.com"
        }
        
        response = session.get(url, headers=headers)
        
        if response.status_code == 200:
            data = json.loads(response.text)
            user_data = data.get("data", {}).get("user", {})
            
            if user_data:
                return {
                    "platform": "Instagram",
                    "type": "profile",
                    "followers": str(user_data.get("edge_followed_by", {}).get("count", 0)),
                    "following": str(user_data.get("edge_follow", {}).get("count", 0)),
                    "content": user_data.get("biography", ""),
                    "profile_image": user_data.get("profile_pic_url_hd", ""),
                    "posts_count": str(user_data.get("edge_owner_to_timeline_media", {}).get("count", 0)),
                    "engagement": "Medium",
                    "frequency": "Weekly",
                    "real_data": True,
                    "url": f"https://instagram.com/{username}"
                }
                
        return None
    except Exception as e:
        print(f"Instagram GraphQL error: {str(e)}")
        return None

# Browser automation methods for JavaScript-heavy sites
def extract_generic_content(url, soup, platform_name):
    """Extract content from a generic social media platform"""
    if not platform_name or platform_name not in PLATFORMS:
        return None
        
    platform_config = PLATFORMS[platform_name]
    
    # Extract bio text
    bio_texts = extract_text_from_selectors(soup, platform_config["bio_selectors"])
    bio = bio_texts[0] if bio_texts else ""
    
    # Extract posts
    posts = extract_post_texts(soup, platform_config["post_selectors"])
    
    # Extract follower count
    follower_count = None
    page_text = soup.get_text()
    follower_count = extract_count_from_text(page_text, platform_config["follower_patterns"])
    
    # Build result
    result = {
        "platform": platform_name.capitalize(),
        "type": platform_config["type"],
        "bio": bio,
        "posts": posts,
        "followers": follower_count if follower_count else "N/A",
        "content": bio,
        "engagement": "Medium",
        "frequency": "Weekly",
        "real_data": bool(bio or posts),
        "url": url
    }
    
    return result

def extract_with_selenium(url, platform_name):
    """
    Extract data using Selenium WebDriver for JavaScript-heavy sites
    """
    if not SELENIUM_AVAILABLE:
        return None
        
    try:
        # Setup WebDriver
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-notifications")
        options.add_argument(f"user-agent={HEADERS['User-Agent']}")
        
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(30)
        
        try:
            driver.get(url)
            # Wait for page to load
            time.sleep(5)
            
            # Get the page source after JavaScript execution
            html_content = driver.page_source
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Extract content based on platform
            if platform_name == "twitter":
                # Extract Twitter followers using Selenium-specific selectors
                try:
                    followers_el = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="UserName"] + div span'))
                    )
                    followers_text = followers_el.text
                    follower_count = extract_count_from_text(followers_text, PLATFORMS["twitter"]["follower_patterns"])
                except:
                    follower_count = None
                    
                # Extract Bio
                try:
                    bio_el = driver.find_element(By.CSS_SELECTOR, '[data-testid="UserDescription"]')
                    bio = bio_el.text
                except:
                    bio = ""
                    
                return {
                    "platform": "Twitter",
                    "type": "profile",
                    "bio": bio,
                    "followers": follower_count,
                    "content": bio,
                    "engagement": "Medium",
                    "frequency": "Daily",
                    "real_data": True,
                    "url": url
                }
            
            elif platform_name == "instagram":
                # Wait for follower count to load
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "header section ul li"))
                    )
                    # Get follower count
                    follower_elements = driver.find_elements(By.CSS_SELECTOR, "header section ul li")
                    follower_count = None
                    
                    for el in follower_elements:
                        text = el.text.lower()
                        if "follower" in text:
                            follower_count = extract_count_from_text(text, PLATFORMS["instagram"]["follower_patterns"])
                            break
                            
                    # Get bio
                    try:
                        bio_el = driver.find_element(By.CSS_SELECTOR, "header section h2 + span")
                        bio = bio_el.text
                    except:
                        bio = ""
                        
                    return {
                        "platform": "Instagram",
                        "type": "profile",
                        "bio": bio,
                        "followers": follower_count,
                        "content": bio,
                        "engagement": "High",
                        "frequency": "Weekly",
                        "real_data": True,
                        "url": url
                    }
                except:
                    pass
            
            return extract_generic_content(url, soup, platform_name)
        finally:
            driver.quit()
    except Exception as e:
        print(f"Selenium error: {str(e)}")
        return None

def extract_with_playwright(url, platform_name):
    """
    Extract content using Playwright for modern JavaScript-heavy sites
    """
    if not PLAYWRIGHT_AVAILABLE:
        return None
        
    try:
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=HEADERS["User-Agent"],
                viewport={"width": 1920, "height": 1080}
            )
            
            page = context.new_page()
            page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Wait for content to load
            page.wait_for_timeout(2000)
            
            # Get page content
            content = page.content()
            soup = BeautifulSoup(content, "html.parser")
            
            # Platform-specific extraction
            if platform_name == "twitter":
                # Try to get followers count
                followers = None
                try:
                    followers_el = page.query_selector('[data-testid="UserName"] + div span')
                    if followers_el:
                        followers_text = followers_el.inner_text()
                        followers = extract_count_from_text(followers_text, PLATFORMS["twitter"]["follower_patterns"])
                except:
                    pass
                    
                # Try to get bio
                bio = ""
                try:
                    bio_el = page.query_selector('[data-testid="UserDescription"]')
                    if bio_el:
                        bio = bio_el.inner_text()
                except:
                    pass
                    
                return {
                    "platform": "Twitter",
                    "type": "profile",
                    "bio": bio,
                    "followers": followers,
                    "content": bio,
                    "engagement": "Medium",
                    "frequency": "Daily",
                    "real_data": True,
                    "url": url
                }
            
            # Generic extraction for other platforms
            browser.close()
            return extract_generic_content(url, soup, platform_name)
    except Exception as e:
        print(f"Playwright error: {str(e)}")
        return None

def extract_social_content(social_links):
    """
    Extract content from social media platforms using multiple methods
    """
    social_content = []

    # Exit early if no social links
    if not social_links:
        return social_content

    # Create a session for multiple requests
    session = get_requests_session()

    # Track domains we've already scraped to avoid duplicates
    scraped_domains = set()
    # Define the extract_generic_content function
    def extract_generic_content(url, soup, platform_name):
        """Extract content from a generic social media platform"""
        if not platform_name or platform_name not in PLATFORMS:
            return None
            
        platform_config = PLATFORMS[platform_name]
        
        # Extract bio text
        bio_texts = extract_text_from_selectors(soup, platform_config["bio_selectors"])
        bio = bio_texts[0] if bio_texts else ""
        
        # Extract posts
        posts = extract_post_texts(soup, platform_config["post_selectors"])
        
        # Extract follower count
        follower_count = None
        page_text = soup.get_text()
        follower_count = extract_count_from_text(page_text, platform_config["follower_patterns"])
        
        # Build result
        result = {
            "platform": platform_name.capitalize(),
            "type": platform_config["type"],
            "bio": bio,
            "posts": posts,
            "followers": follower_count if follower_count else "N/A",
            "content": bio,
            "engagement": "Medium",
            "frequency": "Weekly",
            "real_data": bool(bio or posts),
            "url": url
        }
        
        return result

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
            
            # Extract username for API methods
            username = None
            if platform_name == "twitter" or platform_name == "x":
                username_match = re.search(r"(?:twitter|x)\.com/([^/?]+)", url)
                if username_match:
                    username = username_match.group(1)
                    
                    # Try API-based extraction first
                    platform_data = extract_from_twitter_api(username)
                    if platform_data and platform_data.get("followers") not in ["0", "", "N/A", None]:
                        social_content.append(platform_data)
                        continue
            
            elif platform_name == "instagram":
                username_match = re.search(r"instagram\.com/([^/?]+)", url)
                if username_match:
                    username = username_match.group(1)
                    
                    # Try GraphQL API extraction
                    platform_data = extract_instagram_with_graphql(username)
                    if platform_data and platform_data.get("followers") not in ["0", "", "N/A", None]:
                        social_content.append(platform_data)
                        continue

            # Fetch page content with standard method
            html_content = fetch_page(url, session)
            platform_data = None
            
            if html_content:
                # Parse HTML
                try:
                    soup = BeautifulSoup(html_content, "html.parser")
                    # Remove script and style elements
                    for tag in soup(["script", "style", "noscript"]):
                        tag.decompose()
                except Exception as e:
                    continue

                # Extract content based on platform
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
            
            # If standard extraction failed or didn't find followers, try Selenium
            if not platform_data or platform_data.get("followers") in ["N/A", "0", "", None]:
                selenium_data = extract_with_selenium(url, platform_name)
                if selenium_data and selenium_data.get("followers") not in ["N/A", "0", "", None]:
                    platform_data = selenium_data
            
            # If still no good data, try Playwright
            if not platform_data or platform_data.get("followers") in ["N/A", "0", "", None]:
                playwright_data = extract_with_playwright(url, platform_name)
                if playwright_data and playwright_data.get("followers") not in ["N/A", "0", "", None]:
                    platform_data = playwright_data

            if platform_data:
                # Process content and format data
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

                # Normalize follower count if present
                if "followers" in platform_data:
                    platform_data["followers"] = normalize_follower_count(
                        platform_data["followers"]
                    )
                elif "subscribers" in platform_data:
                    # Standardize: rename subscribers to followers for consistency
                    platform_data["followers"] = normalize_follower_count(
                        platform_data["subscribers"]
                    )
                    platform_data.pop("subscribers", None)
                else:
                    # Set default value for missing follower count
                    platform_data["followers"] = "N/A"
                
                # Additional fallback follower count extraction for specific platforms
                if platform_data.get("followers") in ["N/A", "0", "", None]:
                    # Try more aggressive follower extraction for specific platforms
                    if platform_name in ["twitter", "x"]:
                        # Extra aggressive Twitter follower extraction
                        twitter_follower_patterns = [
                            r"(?:has|with)\s+([\d,.]+[kKmM]?)\s+followers",
                            r"([\d,.]+[kKmM]?)\s+people\s+follow",
                            r"Followers\s*:\s*([\d,.]+[kKmM]?)",
                            r"([\d,.]+[kKmM]?)\s+Followers"
                        ]
                        page_text = soup.get_text()
                        for pattern in twitter_follower_patterns:
                            match = re.search(pattern, page_text, re.IGNORECASE)
                            if match:
                                platform_data["followers"] = normalize_follower_count(match.group(1))
                                break
                    
                    elif platform_name == "youtube":
                        # Extra aggressive YouTube subscriber extraction
                        youtube_sub_patterns = [
                            r"([\d,.]+[kKmM]?)\s*subscribers",
                            r"([\d,.]+[kKmM]?)\s*Subscribers",
                            r"has\s+([\d,.]+[kKmM]?)\s+subscribers",
                            r"([\d,.]+[kKmM]?)\s+subscribed"
                        ]
                        page_text = soup.get_text()
                        for pattern in youtube_sub_patterns:
                            match = re.search(pattern, page_text, re.IGNORECASE)
                            if match:
                                platform_data["followers"] = normalize_follower_count(match.group(1))
                                break
                                
                    elif platform_name == "instagram" and platform_data.get("followers") in ["0", ""]:
                        # Try additional Instagram patterns
                        insta_follower_patterns = [
                            r"([\d,.]+[kKmM]?)\s*followers",
                            r"([\d,.]+[kKmM]?)\s*Followers",
                            r"([0-9,.]+[kKmM]?)\s+follower",
                        ]
                        page_text = soup.get_text()
                        for pattern in insta_follower_patterns:
                            match = re.search(pattern, page_text, re.IGNORECASE)
                            if match:
                                platform_data["followers"] = normalize_follower_count(match.group(1))
                                break
                                
                    # If we still have no follower count, use "N/A" for consistency
                    if not platform_data.get("followers") or platform_data.get("followers") in ["0", ""]:
                        platform_data["followers"] = "N/A"

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

            else:
                pass  # Silently ignore if no content extracted

        except Exception as e:
            pass  # Silently ignore errors

    # Sort social content by platform name for consistency
    social_content.sort(key=lambda x: x.get("platform", ""))

    return social_content


def extract_from_facebook(url, soup):
    """Extract content from a Facebook page"""
    # Get platform config
    platform_config = PLATFORMS["facebook"]
    
    # Extract bio/about information
    bio_texts = extract_text_from_selectors(soup, platform_config["bio_selectors"])
    bio = bio_texts[0] if bio_texts else ""
    
    # Extract posts
    posts = extract_post_texts(soup, platform_config["post_selectors"])
    
    # Extract follower count from page text
    page_text = soup.get_text()
    follower_count = extract_count_from_text(page_text, platform_config["follower_patterns"])
    
    # Extract like count (specific to Facebook)
    like_patterns = [r"([\d,.]+[kKmM]?)\s*people\s*like\s*this", r"([\d,.]+[kKmM]?)\s*likes"]
    like_count = extract_count_from_text(page_text, like_patterns)
    
    return {
        "platform": "Facebook",
        "type": platform_config["type"],
        "bio": bio,
        "posts": posts,
        "followers": follower_count if follower_count else "N/A",
        "likes": like_count if like_count else "N/A",
        "content": bio,
        "engagement": "Medium",
        "frequency": "Weekly",
        "real_data": bool(bio or posts),
        "url": url
    }

def extract_from_twitter(url, soup):
    """Extract content from a Twitter profile"""
    # Get platform config
    platform_config = PLATFORMS["twitter"]
    
    # Extract bio information
    bio_texts = extract_text_from_selectors(soup, platform_config["bio_selectors"])
    bio = bio_texts[0] if bio_texts else ""
    
    # Extract tweets
    tweets = extract_post_texts(soup, platform_config["post_selectors"])
    
    # Extract follower count
    page_text = soup.get_text()
    follower_count = extract_count_from_text(page_text, platform_config["follower_patterns"])
    
    # Extract following count (specific to Twitter)
    following_patterns = [
        r"(\d+[\d,.]*[kKmM]?)\s*(?:Following|following)",
        r"Following\s*(\d+[\d,.]*[kKmM]?)",
    ]
    following_count = extract_count_from_text(page_text, following_patterns)
    
    return {
        "platform": "Twitter",
        "type": platform_config["type"],
        "bio": bio,
        "posts": tweets,
        "followers": follower_count if follower_count else "N/A",
        "following": following_count if following_count else "N/A",
        "content": bio,
        "engagement": "High",
        "frequency": "Daily",
        "real_data": bool(bio or tweets),
        "url": url
    }

def extract_from_instagram(url, soup):
    """Extract content from an Instagram profile"""
    # Get platform config
    platform_config = PLATFORMS["instagram"]
    
    # Extract bio information
    bio_texts = extract_text_from_selectors(soup, platform_config["bio_selectors"])
    bio = bio_texts[0] if bio_texts else ""
    
    # Extract posts
    posts = extract_post_texts(soup, platform_config["post_selectors"], max_posts=3)
    
    # Extract follower count
    page_text = soup.get_text()
    follower_count = extract_count_from_text(page_text, platform_config["follower_patterns"])
    
    # Try to extract post count (specific to Instagram)
    post_count_patterns = [
        r"([\d,.]+[kKmM]?)\s*posts",
        r"([\d,.]+[kKmM]?)\s*publications",
        r"([\d,.]+)\s*post"
    ]
    post_count = extract_count_from_text(page_text, post_count_patterns)
    
    return {
        "platform": "Instagram",
        "type": platform_config["type"],
        "bio": bio,
        "posts": posts,
        "followers": follower_count if follower_count else "N/A",
        "post_count": post_count if post_count else "N/A",
        "content": bio,
        "engagement": "High",
        "frequency": "Weekly",
        "real_data": bool(bio or posts),
        "url": url
    }

def extract_from_linkedin(url, soup):
    """Extract content from a LinkedIn company page"""
    # Get platform config
    platform_config = PLATFORMS["linkedin"]
    
    # Extract bio/about information
    bio_texts = extract_text_from_selectors(soup, platform_config["bio_selectors"])
    bio = bio_texts[0] if bio_texts else ""
    
    # Extract posts
    posts = extract_post_texts(soup, platform_config["post_selectors"])
    
    # Extract follower count
    page_text = soup.get_text()
    follower_count = extract_count_from_text(page_text, platform_config["follower_patterns"])
    
    # Try to extract employee count (specific to LinkedIn)
    employee_patterns = [
        r"([\d,.]+[kKmM]?)\s*employees",
        r"([\d,.]+[kKmM]?)\s*employee"
    ]
    employee_count = extract_count_from_text(page_text, employee_patterns)
    
    return {
        "platform": "LinkedIn",
        "type": platform_config["type"],
        "bio": bio,
        "posts": posts,
        "followers": follower_count if follower_count else "N/A",
        "employees": employee_count if employee_count else "N/A",
        "content": bio,
        "engagement": "Medium",
        "frequency": "Weekly",
        "real_data": bool(bio or posts),
        "url": url
    }

def extract_from_youtube(url, soup):
    """Extract content from a YouTube channel"""
    # Get platform config
    platform_config = PLATFORMS["youtube"]
    
    # Extract channel description
    bio_texts = extract_text_from_selectors(soup, platform_config["bio_selectors"])
    bio = bio_texts[0] if bio_texts else ""
    
    # Extract video titles as "posts"
    videos = extract_post_texts(soup, platform_config["post_selectors"])
    
    # Extract subscriber count
    page_text = soup.get_text()
    subscriber_count = extract_count_from_text(page_text, platform_config["follower_patterns"])
    
    # Try to extract view count (specific to YouTube)
    view_patterns = [
        r"([\d,.]+[kKmM]?)\s*views",
        r"([\d,.]+[kKmM]?)\s*total\s*views"
    ]
    view_count = extract_count_from_text(page_text, view_patterns)
    
    return {
        "platform": "YouTube",
        "type": platform_config["type"],
        "bio": bio,
        "posts": videos,
        "subscribers": subscriber_count if subscriber_count else "N/A",
        "views": view_count if view_count else "N/A",
        "content": bio,
        "engagement": "High",
        "frequency": "Weekly",
        "real_data": bool(bio or videos),
        "url": url
    }
