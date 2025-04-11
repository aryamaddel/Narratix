import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, urljoin


def extract_domain(url):
    """Extract domain name from URL"""
    parsed_uri = urlparse(url)
    return parsed_uri.netloc.lower()


def extract_social_links(url):
    """Extract social media links from website - simplified"""
    try:
        platform_patterns = {
            "facebook": r"facebook\.com|fb\.com",
            "twitter": r"twitter\.com|x\.com",
            "instagram": r"instagram\.com",
            "linkedin": r"linkedin\.com",
            "youtube": r"youtube\.com|youtu\.be",
            "pinterest": r"pinterest\.com",
            "tiktok": r"tiktok\.com",
        }

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        }

        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.content, "html.parser")
        social_links = []
        found_platforms = set()

        # Check all links
        for link in soup.find_all("a", href=True):
            href = link.get("href", "").strip()
            if not href or href.startswith(("javascript:", "mailto:", "#")):
                continue

            # Make absolute URL
            if not href.startswith(("http://", "https://")):
                href = urljoin(url, href)

            # Check for social media platforms
            for platform, pattern in platform_patterns.items():
                if platform in found_platforms:
                    continue

                if re.search(pattern, href, re.IGNORECASE):
                    social_links.append({"platform": platform, "url": href})
                    found_platforms.add(platform)

        return social_links
    except Exception:
        return []


def extract_website_content(url):
    """Extract basic website content"""
    try:
        domain = extract_domain(url)
        default_name = domain.replace("www.", "").split(".")[0].capitalize()

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        }

        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return {
                "brand_name": default_name,
                "description": f"Website for {default_name}",
                "content": "",
            }

        soup = BeautifulSoup(response.content, "html.parser")

        # Get title for brand name
        title_tag = soup.find("title")
        brand_name = default_name
        if title_tag:
            title = title_tag.get_text().strip()
            brand_name = re.sub(r"\s*[-|]\s*.*$", "", title).strip() or default_name

        # Get description
        meta_desc = soup.find("meta", {"name": "description"}) or soup.find(
            "meta", property="og:description"
        )
        description = meta_desc.get("content", "").strip() if meta_desc else ""

        # Get content text
        paragraphs = []
        for p in soup.find_all("p"):
            text = p.get_text().strip()
            if text and len(text) > 20:
                paragraphs.append(text)

        content = " ".join(paragraphs[:5])  # First 5 paragraphs

        # Fallbacks
        if not description:
            description = content[:150] + "..." if len(content) > 150 else content
        if not description:
            description = f"Website for {brand_name}"

        return {
            "brand_name": brand_name,
            "description": description,
            "content": content,
        }
    except Exception:
        domain = extract_domain(url)
        default_name = domain.replace("www.", "").split(".")[0].capitalize()
        return {
            "brand_name": default_name,
            "description": f"Website for {default_name}",
            "content": "",
        }
