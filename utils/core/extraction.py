import re
import logging

logger = logging.getLogger(__name__)

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
