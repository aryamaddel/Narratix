import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, urljoin
import random

def extract_domain(url):
    """Extract domain name from URL"""
    parsed_uri = urlparse(url)
    domain = "{uri.netloc}".format(uri=parsed_uri)
    return domain.lower()

def normalize_url(base_url, url):
    """Normalize URL (handle relative URLs)"""
    if not url:
        return None
    url = url.strip().strip("\"'")
    # Skip certain URLs
    if url.startswith(("javascript:", "mailto:", "tel:", "#", "data:")):
        return None
    # Handle relative URLs
    if not url.startswith(("http://", "https://")):
        return urljoin(base_url, url)
    return url

def detect_platform_from_url(url):
    """Detect the social media platform from a URL"""
    domain = extract_domain(url).lower()
    
    platform_map = {
        "facebook.com": "facebook",
        "fb.com": "facebook",
        "twitter.com": "twitter",
        "x.com": "twitter",
        "instagram.com": "instagram",
        "linkedin.com": "linkedin",
        "youtube.com": "youtube",
        "youtu.be": "youtube",
        "pinterest.com": "pinterest",
        "tiktok.com": "tiktok",
    }
    
    # Check for exact domain matches
    if domain in platform_map:
        return platform_map[domain]
    
    # Check for subdomain matches (e.g., business.facebook.com)
    for social_domain, platform in platform_map.items():
        if domain.endswith("." + social_domain):
            return platform
            
    return None

def extract_social_links(url):
    """Extract social media links from website - simplified version"""
    social_links = []
    
    try:
        # Check if the URL itself is a social media site
        site_platform = detect_platform_from_url(url)
        if site_platform:
            social_links.append({"platform": site_platform, "url": url})
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return social_links
            
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Social media patterns
        social_patterns = {
            "facebook": r"facebook\.com|fb\.com",
            "twitter": r"twitter\.com|x\.com",
            "instagram": r"instagram\.com",
            "linkedin": r"linkedin\.com",
            "youtube": r"youtube\.com|youtu\.be",
            "pinterest": r"pinterest\.com",
            "tiktok": r"tiktok\.com",
        }
        
        # Track found platforms to avoid duplicates
        found_platforms = set()
        if site_platform:
            found_platforms.add(site_platform)
            
        # Extract from all links
        for link in soup.find_all("a", href=True):
            href = normalize_url(url, link["href"])
            if not href:
                continue
                
            for platform, pattern in social_patterns.items():
                if platform in found_platforms:
                    continue
                    
                if re.search(pattern, href, re.IGNORECASE):
                    social_links.append({"platform": platform, "url": href})
                    found_platforms.add(platform)
                    break
                    
        return social_links
        
    except Exception:
        return social_links

def extract_website_content(url):
    """Extract basic website content - simplified"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        }
        
        domain = extract_domain(url)
        default_brand_name = domain.replace("www.", "").split(".")[0].capitalize()
        
        # Handle social media platforms
        platform = detect_platform_from_url(url)
        if platform:
            default_brand_name = platform.capitalize()
            
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return {
                "brand_name": default_brand_name,
                "description": f"Website for {default_brand_name}",
                "content": "",
            }
            
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Extract brand name from title
        brand_name = default_brand_name
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text().strip()
            brand_name = re.sub(r"\s*[-|]\s*.*$", "", title).strip()
            
        # Extract description from meta tags
        description = ""
        meta_desc = soup.find("meta", {"name": "description"})
        if meta_desc and meta_desc.get("content"):
            description = meta_desc["content"].strip()
        
        if not description:
            og_desc = soup.find("meta", property="og:description")
            if og_desc and og_desc.get("content"):
                description = og_desc["content"].strip()
                
        # Extract content from paragraphs
        paragraphs = []
        for p in soup.find_all("p"):
            text = p.get_text().strip()
            if text and len(text) > 20:  # Reasonably sized paragraphs
                paragraphs.append(text)
                
        content = " ".join(paragraphs[:10])  # First 10 paragraphs
        
        # If no content found, use basic body text
        if not content:
            content = soup.get_text(separator=" ", strip=True)[:1000]
            
        # If still no description
        if not description:
            description = content[:150] + "..." if len(content) > 150 else content
            
        return {
            "brand_name": brand_name or default_brand_name,
            "description": description or f"Website for {brand_name or default_brand_name}",
            "content": content or f"Content from {brand_name or default_brand_name} website",
        }
            
    except Exception:
        domain = extract_domain(url)
        default_brand_name = domain.replace("www.", "").split(".")[0].capitalize()
        
        return {
            "brand_name": default_brand_name,
            "description": f"Website for {default_brand_name}",
            "content": f"{default_brand_name} provides professional services.",
        }
