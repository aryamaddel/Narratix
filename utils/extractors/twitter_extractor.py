import re
import logging
from utils.core.platforms import PLATFORMS
from utils.core.extraction import extract_text_from_selectors, extract_post_texts, extract_count_from_text
from utils.extractors.generic_extractor import estimate_posting_frequency

logger = logging.getLogger(__name__)

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
