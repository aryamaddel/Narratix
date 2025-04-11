import re
import logging
from utils.core.platforms import PLATFORMS, identify_platform
from utils.core.extraction import extract_text_from_selectors, extract_post_texts, extract_count_from_text

logger = logging.getLogger(__name__)

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
