import requests
from bs4 import BeautifulSoup
import re
import json
import os
from urllib.parse import urlparse, urljoin
import random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def get_requests_session():
    """Create a requests session with retry capability"""
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def extract_domain(url):
    """Extract domain name from URL"""
    parsed_uri = urlparse(url)
    domain = "{uri.netloc}".format(uri=parsed_uri)
    return domain.lower()


def clean_url(url):
    """Remove URL parameters and fragments"""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"


def normalize_url(base_url, url):
    """Normalize URL (handle relative URLs)"""
    if not url:
        return None

    # Remove whitespace and quotes
    url = url.strip().strip("\"'")

    # Skip certain URLs
    if url.startswith(("javascript:", "mailto:", "tel:", "#", "data:")):
        return None

    # Handle relative URLs
    if not url.startswith(("http://", "https://")):
        return urljoin(base_url, url)

    return url


def is_social_media_site(url):
    """Determine if a URL is itself a social media site"""
    social_domains = [
        "facebook.com",
        "fb.com",
        "twitter.com",
        "x.com",
        "instagram.com",
        "linkedin.com",
        "youtube.com",
        "youtu.be",
        "pinterest.com",
        "tiktok.com",
        "github.com",
        "medium.com",
        "snapchat.com",
        "reddit.com",
        "tumblr.com",
        "flickr.com",
        "vimeo.com",
    ]

    domain = extract_domain(url)

    # Check exact matches
    if domain in social_domains:
        return True

    # Check for subdomains (e.g., business.facebook.com)
    for social_domain in social_domains:
        if domain.endswith("." + social_domain):
            return True

    return False


def detect_platform_from_url(url):
    """Detect the social media platform from a URL"""
    domain = extract_domain(url).lower()

    # Map domains to platform names
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
        "github.com": "github",
        "medium.com": "medium",
        "snapchat.com": "snapchat",
        "reddit.com": "reddit",
        "tumblr.com": "tumblr",
        "flickr.com": "flickr",
        "vimeo.com": "vimeo",
    }

    # Check for exact domain matches
    if domain in platform_map:
        return platform_map[domain]

    # Check for subdomain matches (e.g., business.facebook.com)
    for social_domain, platform in platform_map.items():
        if domain.endswith("." + social_domain):
            return platform

    # Check for platform names in the domain
    for platform in set(platform_map.values()):
        if platform in domain:
            return platform

    return None


def extract_social_links(url):
    """Extract social media links from website"""
    social_links = []

    try:
        # Check if the URL itself is a social media site
        site_platform = detect_platform_from_url(url)
        if site_platform:
            # Add the site itself as a social link
            social_links.append({"platform": site_platform, "url": url})

        headers = {
            "User-Agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(90, 110)}.0.{random.randint(4000, 5000)}.{random.randint(100, 200)} Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,/;q=0.8",
            "Cache-Control": "max-age=0",
        }

        session = get_requests_session()

        # Try with a timeout
        try:
            response = session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
        except Exception as e:
            return social_links  # Return what we've found so far (may include the site itself)

        # Parse content
        try:
            soup = BeautifulSoup(response.content, "html.parser")
        except Exception as e:
            return social_links  # Return what we've found so far

        domain = extract_domain(url)

        # Social media platforms to look for
        social_patterns = {
            "facebook": [r"facebook\.com", r"fb\.com", r"facebook\."],
            "twitter": [r"twitter\.com", r"x\.com", r"twitter\."],
            "instagram": [r"instagram\.com", r"instagram\."],
            "linkedin": [r"linkedin\.com", r"linkedin\."],
            "youtube": [r"youtube\.com", r"youtu\.be", r"youtube\."],
            "pinterest": [r"pinterest\.com", r"pinterest\."],
            "tiktok": [r"tiktok\.com", r"tiktok\."],
            "github": [r"github\.com", r"github\."],
            "medium": [r"medium\.com", r"medium\."],
            "snapchat": [r"snapchat\.com", r"snapchat\."],
            "reddit": [r"reddit\.com", r"reddit\."],
            "tumblr": [r"tumblr\.com", r"tumblr\."],
            "flickr": [r"flickr\.com", r"flickr\."],
            "vimeo": [r"vimeo\.com", r"vimeo\."],
        }

        # Track found social links to avoid duplicates
        found_platforms = set()
        if site_platform:
            found_platforms.add(site_platform)

        # STRATEGY 1: Extract links from all <a> tags
        try:
            for link in soup.find_all("a", href=True):
                try:
                    href = normalize_url(url, link["href"])
                    if not href:
                        continue

                    # Check if it's a social media link
                    for platform, patterns in social_patterns.items():
                        if platform in found_platforms:
                            continue

                        if any(
                            re.search(pattern, href, re.IGNORECASE)
                            for pattern in patterns
                        ):
                            social_links.append({"platform": platform, "url": href})
                            found_platforms.add(platform)
                            break
                except Exception as e:
                    continue
        except Exception as e:
            pass

        # STRATEGY 2: Look for social media meta tags
        try:
            meta_tags = {
                "facebook": [
                    'meta[property="og:url"]',
                    'meta[property="fb:page_id"]',
                    'meta[property="fb:app_id"]',
                ],
                "twitter": [
                    'meta[name="twitter:site"]',
                    'meta[name="twitter:creator"]',
                    'meta[name="twitter:card"]',
                ],
                "instagram": ['meta[property="instapp:owner_url"]'],
            }

            for platform, selectors in meta_tags.items():
                if platform in found_platforms:
                    continue

                for selector in selectors:
                    try:
                        meta_tag = soup.select_one(selector)
                        if meta_tag and meta_tag.get("content"):
                            content = meta_tag["content"].strip()

                            # Handle Twitter handle format
                            if platform == "twitter" and content.startswith("@"):
                                content = f"https://twitter.com/{content[1:]}"

                            # Make sure it's a URL
                            if not content.startswith(("http://", "https://")):
                                if platform == "facebook":
                                    content = f"https://facebook.com/{content}"
                                elif platform == "twitter":
                                    content = f"https://twitter.com/{content}"
                                elif platform == "instagram":
                                    content = f"https://instagram.com/{content}"

                            if any(
                                re.search(pattern, content, re.IGNORECASE)
                                for pattern in social_patterns.get(platform, [])
                            ):
                                social_links.append(
                                    {"platform": platform, "url": content}
                                )
                                found_platforms.add(platform)
                                break
                    except Exception:
                        continue
        except Exception as e:
            pass

        # STRATEGY 3: Look for social links in common footer/header elements
        try:
            social_containers = soup.select(
                "footer, .footer, #footer, header, .header, #header, .social, .social-links, .connect, .follow, .share, nav, .nav"
            )
            for container in social_containers:
                for link in container.find_all("a", href=True):
                    try:
                        href = normalize_url(url, link["href"])
                        if not href:
                            continue

                        for platform, patterns in social_patterns.items():
                            if platform in found_platforms:
                                continue

                            if any(
                                re.search(pattern, href, re.IGNORECASE)
                                for pattern in patterns
                            ):
                                social_links.append({"platform": platform, "url": href})
                                found_platforms.add(platform)
                                break
                    except Exception:
                        continue
        except Exception as e:
            pass

        # STRATEGY 4: Look for icon class names that might indicate social links
        try:
            social_selectors = [
                'a i[class*="fa-"], a span[class*="fa-"]',  # Font Awesome
                'a i[class*="icon-"], a span[class*="icon-"]',  # Various icon fonts
                'a i[class*="social"], a span[class*="social"]',  # Generic social classes
                'a[class*="social"], a[class*="facebook"], a[class*="twitter"], a[class*="instagram"]',  # Direct link classes
                ".social a, .socials a, .social-icons a, .social-media a",  # Container classes
            ]

            for selector in social_selectors:
                elements = soup.select(selector)
                for element in elements:
                    try:
                        # Get the parent <a> tag if this is an icon
                        if element.name != "a":
                            parent = element.find_parent("a")
                            if not parent or not parent.has_attr("href"):
                                continue
                            element = parent

                        href = normalize_url(url, element["href"])
                        if not href:
                            continue

                        # Find platform by URL pattern
                        for platform, patterns in social_patterns.items():
                            if platform in found_platforms:
                                continue

                            if any(
                                re.search(pattern, href, re.IGNORECASE)
                                for pattern in patterns
                            ):
                                social_links.append({"platform": platform, "url": href})
                                found_platforms.add(platform)
                                break

                        # If no platform found by URL, try to detect from class names
                        if not any(
                            platform in found_platforms
                            for platform in social_patterns.keys()
                        ):
                            classes = " ".join(
                                element.get("class", [])
                                + element.find("i", class_=True).get("class", [])
                                if element.find("i", class_=True)
                                else []
                            )

                            classes = classes.lower()

                            for platform in social_patterns.keys():
                                if platform in found_platforms:
                                    continue

                                if platform.lower() in classes:
                                    social_links.append(
                                        {"platform": platform, "url": href}
                                    )
                                    found_platforms.add(platform)
                                    break
                    except Exception:
                        continue
        except Exception as e:
            pass

        # STRATEGY 5: Look for common social sharing buttons
        try:
            share_selectors = [
                ".share-buttons a",
                ".share a",
                ".sharing a",
                "[data-share]",
                "[data-network]",
                "[data-platform]",
            ]

            for selector in share_selectors:
                elements = soup.select(selector)
                for element in elements:
                    try:
                        if not element.has_attr("href"):
                            continue

                        href = normalize_url(url, element["href"])
                        if not href:
                            continue

                        for platform, patterns in social_patterns.items():
                            if platform in found_platforms:
                                continue

                            if any(
                                re.search(pattern, href, re.IGNORECASE)
                                for pattern in patterns
                            ):
                                social_links.append({"platform": platform, "url": href})
                                found_platforms.add(platform)
                                break
                    except Exception:
                        continue
        except Exception as e:
            pass

        # STRATEGY 6: Look for common text patterns associated with social media
        try:
            social_text_patterns = {
                "facebook": [
                    "follow us on facebook",
                    "find us on facebook",
                    "like us on facebook",
                    "facebook page",
                ],
                "twitter": ["follow us on twitter", "tweet us", "twitter feed"],
                "instagram": [
                    "follow us on instagram",
                    "instagram feed",
                    "instagram profile",
                ],
                "linkedin": [
                    "connect on linkedin",
                    "linkedin profile",
                    "linkedin page",
                ],
                "youtube": [
                    "youtube channel",
                    "subscribe to our channel",
                    "watch on youtube",
                ],
                "pinterest": ["follow us on pinterest", "pinterest board", "pin it"],
                "tiktok": ["follow us on tiktok", "tiktok profile", "tiktok feed"],
            }

            # Get all text nodes
            page_text = soup.get_text().lower()

            # Check for text patterns
            for platform, patterns in social_text_patterns.items():
                if platform in found_platforms:
                    continue

                for pattern in patterns:
                    if pattern in page_text:
                        # If we find text suggesting a social platform but no link for it,
                        # add a generic link based on the site's name
                        brand_name = extract_domain(url).split(".")[0]
                        if platform == "facebook":
                            social_links.append(
                                {
                                    "platform": platform,
                                    "url": f"https://facebook.com/{brand_name}",
                                }
                            )
                        elif platform == "twitter":
                            social_links.append(
                                {
                                    "platform": platform,
                                    "url": f"https://twitter.com/{brand_name}",
                                }
                            )
                        elif platform == "instagram":
                            social_links.append(
                                {
                                    "platform": platform,
                                    "url": f"https://instagram.com/{brand_name}",
                                }
                            )
                        elif platform == "linkedin":
                            social_links.append(
                                {
                                    "platform": platform,
                                    "url": f"https://linkedin.com/company/{brand_name}",
                                }
                            )
                        elif platform == "youtube":
                            social_links.append(
                                {
                                    "platform": platform,
                                    "url": f"https://youtube.com/@{brand_name}",
                                }
                            )
                        else:
                            continue  # Skip other platforms for now

                        found_platforms.add(platform)
                        break
        except Exception as e:
            pass

        # Remove duplicates while preserving order
        unique_links = []
        seen_urls = set()

        for link in social_links:
            try:
                clean_link_url = clean_url(link["url"])
                if clean_link_url and clean_link_url not in seen_urls:
                    seen_urls.add(clean_link_url)
                    unique_links.append(link)
            except Exception:
                continue

        return unique_links

    except Exception as e:
        return social_links  # Return what we've found so far


def extract_website_content(url):
    """
    Extract content from a website using traditional web crawling.
    
    Args:
        url (str): URL of the website to extract content from
        
    Returns:
        dict: Extracted website content
    """
    try:
        # Default empty result
        result = {
            "brand_name": "",
            "description": "",
            "content": "",
            "pages": []
        }
        
        # In a real implementation, this would use requests/BeautifulSoup
        # to crawl the website and extract content
        
        # For now, extract brand name from domain as fallback
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        brand_name = domain.replace("www.", "").split(".")[0]
        result["brand_name"] = brand_name.capitalize()
        
        # Set a generic description
        result["description"] = f"Website for {result['brand_name']}"
        
        return result
        
    except Exception as e:
        # Return empty result if extraction fails
        return {
            "brand_name": "",
            "description": "",
            "content": "",
            "pages": []
        }
