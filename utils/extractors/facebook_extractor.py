import re
import logging
from utils.core.platforms import PLATFORMS
from utils.core.extraction import extract_text_from_selectors, extract_post_texts, extract_count_from_text
from utils.extractors.generic_extractor import estimate_posting_frequency

logger = logging.getLogger(__name__)

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
