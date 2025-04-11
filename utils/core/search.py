import re
import time
import logging
from urllib.parse import urlparse, quote_plus
from bs4 import BeautifulSoup

from utils.core.session import get_requests_session, fetch_page
from utils.core.platforms import PLATFORMS
from utils.core.extraction import normalize_follower_count

logger = logging.getLogger(__name__)

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
