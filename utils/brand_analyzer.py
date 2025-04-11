import os
import json
import logging
from typing import List, Dict, Any, Optional

# Import core functionality
from utils.core.session import get_requests_session, fetch_page, DEFAULT_TIMEOUT, MAX_RETRIES, HEADERS
from utils.core.platforms import PLATFORMS, identify_platform
from utils.core.extraction import extract_text_from_selectors, extract_post_texts, extract_count_from_text, normalize_follower_count, clean_text_content
from utils.core.search import search_google_for_brand_info

# Import platform-specific extractors
from utils.extractors.facebook_extractor import extract_from_facebook
from utils.extractors.twitter_extractor import extract_from_twitter
from utils.extractors.generic_extractor import extract_generic_content, estimate_posting_frequency

# Import analysis functions
from utils.analysis.content_analyzer import analyze_content, DEFAULT_ANALYSIS

# Import generation functions
from utils.generation.story_generator import generate_brand_story
from utils.generation.visual_generator import generate_visual_profile
from utils.generation.score_generator import generate_consistency_score

# Set up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# Create handler if not already configured
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Import and configure Gemini
from utils.core.gemini_setup import GEMINI_AVAILABLE, DEFAULT_MODEL

# Flag to indicate if Gemini API is available
# Set to False by default, can be changed in configuration
GEMINI_AVAILABLE = False

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
            from urllib.parse import urlparse
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
                from bs4 import BeautifulSoup
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
            # Additional platform extractors would be called here
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
        import google.generativeai as genai
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
        import google.generativeai as genai
        model = genai.GenerativeModel(DEFAULT_MODEL)
        logger.debug(f"Sending social media analysis prompt to Gemini using model {DEFAULT_MODEL}")
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

# Flag to indicate if Gemini API is available
# Set to False by default, can be changed in configuration
GEMINI_AVAILABLE = False

def search_website_content(url):
    """
    Search and extract content from a website using advanced search capabilities.
    If using Gemini, this would leverage its web search features.
    
    Args:
        url (str): URL of the website to analyze
        
    Returns:
        dict: Website content including brand name, description, etc.
    """
    try:
        # Default empty result
        result = {
            "brand_name": "",
            "description": "",
            "content": "",
            "pages": []
        }
        
        # In a real implementation, this would use Gemini API to search
        # For now, we'll provide a minimal implementation
        
        # Extract domain as fallback brand name
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        brand_name = domain.replace("www.", "").split(".")[0]
        result["brand_name"] = brand_name.capitalize()
        
        # Set a generic description
        result["description"] = f"Website for {result['brand_name']}"
        
        return result
        
    except Exception as e:
        # Return empty result if search fails
        return {
            "brand_name": "",
            "description": "",
            "content": "",
            "pages": []
        }

def search_social_media(brand_name):
    """
    Search for social media profiles related to a brand name.
    
    Args:
        brand_name (str): Name of the brand to search for
        
    Returns:
        list: Social media profiles found
    """
    try:
        # In a real implementation, this would use search APIs
        # For now, return an empty list
        return []
        
    except Exception as e:
        return []

def get_social_profiles(brand_name, website_url):
    """
    Unified method to get social media profiles for a brand.
    Tries search first, then falls back to scraping.
    
    Args:
        brand_name (str): Brand name to search for
        website_url (str): URL of the brand's website
        
    Returns:
        list: Social media profiles and data
    """
    try:
        # Try searching first
        profiles = search_social_media(brand_name)
        
        # If no profiles found, try to extract from website (would be implemented in a real system)
        if not profiles:
            # This is where profile extraction logic would go
            pass
            
        return profiles
        
    except Exception as e:
        return []
