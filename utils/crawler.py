# --- START OF FILE crawler.py ---

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
    """Extract content from website for analysis"""
    try:
        headers = {
            "User-Agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(90, 110)}.0.{random.randint(4000, 5000)}.{random.randint(100, 200)} Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,/;q=0.8",
            "Cache-Control": "max-age=0",
        }

        # Default values in case of failure
        domain = extract_domain(url)
        default_brand_name = domain.replace("www.", "")
        default_brand_name = re.sub(
            r"\.com$|\.org$|\.net$|\.io$|\.co$", "", default_brand_name
        ).capitalize()

        # Handle special case for social media platforms
        platform = detect_platform_from_url(url)
        if platform:
            default_brand_name = platform.capitalize()

        session = get_requests_session()

        # Try with a timeout
        try:
            response = session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
        except Exception as e:
            return {
                "brand_name": default_brand_name,
                "description": f"Website for {default_brand_name}",
                "content": "",
            }

        # Try to parse the HTML
        try:
            soup = BeautifulSoup(response.content, "html.parser")
        except Exception as e:
            return {
                "brand_name": default_brand_name,
                "description": f"Website for {default_brand_name}",
                "content": "",
            }

        # Remove unwanted tags
        for tag in soup(
            ["script", "style", "noscript", "iframe", "svg", "nav", "footer"]
        ):
            try:
                tag.decompose()
            except Exception:
                pass

        # Extract brand name using multiple strategies
        brand_name = ""

        # If it's a social media site, use the platform name
        if platform:
            brand_name = platform.capitalize()
        else:
            # STRATEGY 1: Get from title tag
            try:
                title_tag = soup.find("title")
                if title_tag:
                    title = title_tag.get_text().strip()
                    # Remove common suffixes like "- Home" or "| Official Website"
                    brand_name = re.sub(r"\s*[-|]\s*.*$", "", title).strip()
            except Exception as e:
                pass

            # STRATEGY 2: Get from meta tags
            if not brand_name or brand_name.lower() in ["home", "welcome", "index"]:
                try:
                    meta_title_tags = [
                        soup.find("meta", property="og:title"),
                        soup.find("meta", property="twitter:title"),
                        soup.find("meta", name="title"),
                    ]

                    for meta_tag in meta_title_tags:
                        if meta_tag and meta_tag.get("content"):
                            content = meta_tag["content"].strip()
                            # Remove common suffixes
                            brand_name = re.sub(r"\s*[-|]\s*.*$", "", content).strip()
                            if brand_name and brand_name.lower() not in [
                                "home",
                                "welcome",
                                "index",
                            ]:
                                break
                except Exception as e:
                    pass

            # STRATEGY 3: Get from logo alt text or image filename
            if not brand_name or brand_name.lower() in ["home", "welcome", "index"]:
                try:
                    logo_selectors = [
                        "a.logo img",
                        ".logo img",
                        "#logo img",
                        "header img",
                        ".header img",
                        ".brand img",
                        'img[alt*="logo"]',
                        'img[src*="logo"]',
                    ]

                    for selector in logo_selectors:
                        logo_img = soup.select_one(selector)
                        if (
                            logo_img
                            and logo_img.has_attr("alt")
                            and logo_img["alt"].strip()
                        ):
                            brand_name = logo_img["alt"].strip()
                            break
                        elif logo_img and logo_img.has_attr("src"):
                            # Try to extract brand name from logo filename
                            src = logo_img["src"]
                            filename = os.path.basename(urlparse(src).path)
                            if "logo" in filename.lower():
                                # Remove extension and common prefixes
                                name = os.path.splitext(filename)[0]
                                name = re.sub(
                                    r"^(logo[-]?|header[-]?|brand[-_]?)",
                                    "",
                                    name,
                                    flags=re.IGNORECASE,
                                )
                                # Convert kebab/snake case to title case
                                if "-" in name or "_" in name:
                                    name = re.sub(r"[-_]", " ", name).title()
                                if name:
                                    brand_name = name
                                    break
                except Exception as e:
                    pass

            # STRATEGY 4: Get from structured data
            if not brand_name or brand_name.lower() in ["home", "welcome", "index"]:
                try:
                    for script in soup.find_all("script", type="application/ld+json"):
                        try:
                            data = json.loads(script.string)
                            if isinstance(data, dict):
                                if data.get("@type") in [
                                    "Organization",
                                    "Corporation",
                                    "LocalBusiness",
                                ] and data.get("name"):
                                    brand_name = data["name"]
                                    break
                        except:
                            pass
                except Exception as e:
                    pass

        # Fallback to domain name or platform name
        if not brand_name or brand_name.lower() in ["home", "welcome", "index"]:
            brand_name = default_brand_name

        # Extract description using multiple strategies
        description = ""

        # STRATEGY 1: Get from meta description
        try:
            meta_desc = soup.find("meta", {"name": "description"})
            if meta_desc and meta_desc.get("content"):
                description = meta_desc["content"].strip()
        except Exception as e:
            pass

        # STRATEGY 2: Get from Open Graph description
        if not description:
            try:
                og_desc = soup.find("meta", property="og:description")
                if og_desc and og_desc.get("content"):
                    description = og_desc["content"].strip()
            except Exception as e:
                pass

        # STRATEGY 3: Get from Twitter description
        if not description:
            try:
                twitter_desc = soup.find("meta", name="twitter:description")
                if twitter_desc and twitter_desc.get("content"):
                    description = twitter_desc["content"].strip()
            except Exception as e:
                pass

        # Extract main content using multiple strategies
        main_content = ""

        # STRATEGY 1: Find main content containers
        try:
            main_selectors = [
                "main",
                "article",
                "section",
                "#content",
                ".content",
                "#main",
                ".main",
                '[role="main"]',
                ".post-content",
                ".entry-content",
            ]

            for selector in main_selectors:
                elements = soup.select(selector)
                for element in elements:
                    try:
                        content = element.get_text(separator=" ", strip=True)
                        if len(content) > len(main_content):
                            main_content = content
                    except Exception:
                        continue
        except Exception as e:
            pass

        # STRATEGY 2: Get text from paragraphs
        if not main_content or len(main_content) < 200:
            try:
                paragraphs = []
                for p in soup.find_all("p"):
                    try:
                        text = p.get_text().strip()
                        if text and len(text) > 10:  # Ignore very short paragraphs
                            paragraphs.append(text)
                    except Exception:
                        continue

                # Join paragraphs, but exclude navigation or footer paragraphs
                # by focusing on the middle of the document
                if paragraphs:
                    if len(paragraphs) > 4:
                        # Use middle paragraphs, more likely to be main content
                        start = max(0, len(paragraphs) // 4)
                        end = min(len(paragraphs), len(paragraphs) * 3 // 4)
                        main_content = " ".join(paragraphs[start:end])
                    else:
                        main_content = " ".join(paragraphs)
            except Exception as e:
                pass

        # STRATEGY 3: Get all text from body if still insufficient
        if not main_content or len(main_content) < 200:
            try:
                body = soup.find("body")
                if body:
                    main_content = body.get_text(separator=" ", strip=True)
            except Exception as e:
                pass

        # Clean up the content
        try:
            # Remove excess whitespace
            main_content = re.sub(r"\s+", " ", main_content).strip()

            # Remove very short content blocks (likely navigation or footer items)
            if len(main_content.split()) < 10:
                main_content = (
                    f"Website for {brand_name} focused on providing services."
                )
        except Exception:
            if not main_content:
                main_content = (
                    f"Website for {brand_name} focused on providing services."
                )

        # Generate description if still empty
        if not description:
            # Use first ~200 characters of main content as description
            if main_content:
                # Extract a complete sentence if possible
                sentences = re.split(r"(?<=[.!?])\s+", main_content)
                if sentences:
                    description = sentences[0]
                    if len(description) < 50 and len(sentences) > 1:
                        description += " " + sentences[1]

                # Trim if too long
                if len(description) > 200:
                    description = description[:197] + "..."
            else:
                description = f"Official website for {brand_name}"

        # Try to find and extract content from about page
        try:
            about_links = []
            about_patterns = [
                r"/about",
                r"/about-us",
                r"/company",
                r"/who-we-are",
                r"/mission",
                r"/values",
                r"/our-story",
                r"/story",
                r"/team",
                r"/history",
            ]

            for link in soup.find_all("a", href=True):
                try:
                    href = normalize_url(url, link["href"])
                    if not href:
                        continue

                    path = urlparse(href).path.lower()
                    if any(re.search(pattern, path) for pattern in about_patterns):
                        about_links.append(href)
                except Exception:
                    continue

            # If we found about page links, try to get content from the first one
            if about_links:
                try:
                    about_response = session.get(
                        about_links[0], headers=headers, timeout=8
                    )
                    about_response.raise_for_status()

                    about_soup = BeautifulSoup(about_response.content, "html.parser")

                    # Remove unwanted tags
                    for tag in about_soup(
                        [
                            "script",
                            "style",
                            "noscript",
                            "iframe",
                            "svg",
                            "nav",
                            "footer",
                        ]
                    ):
                        try:
                            tag.decompose()
                        except Exception:
                            pass

                    # Get paragraphs from about page
                    about_paragraphs = []
                    for p in about_soup.find_all("p"):
                        try:
                            text = p.get_text().strip()
                            if text and len(text) > 10:
                                about_paragraphs.append(text)
                        except Exception:
                            continue

                    # Only use about page content if we found enough text
                    if about_paragraphs and sum(len(p) for p in about_paragraphs) > 100:
                        about_content = " ".join(about_paragraphs)
                        about_content = re.sub(r"\s+", " ", about_content).strip()

                        # Add about page content to main content
                        if about_content:
                            if main_content:
                                main_content = main_content + " " + about_content
                            else:
                                main_content = about_content
                except Exception as e:
                    pass
        except Exception as e:
            pass

        # Handle social media platform sites specially
        if platform and (not main_content or len(main_content) < 200):
            platform_descriptions = {
                "facebook": f"{brand_name} is a global social networking platform that connects people with friends, family, businesses, and organizations. It allows users to share updates, photos, videos, and engage with content through likes, comments, and shares.",
                "twitter": f"{brand_name} is a microblogging and social networking platform where users post and interact with short messages called tweets. It's known for real-time information sharing, news updates, and public conversations.",
                "instagram": f"{brand_name} is a photo and video sharing social networking service owned by Meta Platforms. The app allows users to upload media that can be edited with filters and organized by hashtags and geographical tagging.",
                "linkedin": f"{brand_name} is a business and employment-focused social media platform that works through websites and mobile apps. It's primarily used for professional networking and career development.",
                "youtube": f"{brand_name} is a video sharing platform where users can upload, view, rate, share, comment on videos, and subscribe to other users. It offers a wide variety of user-generated and corporate media videos.",
                "pinterest": f"{brand_name} is an image sharing and social media service designed to enable saving and discovery of information on the internet using images, GIFs, and videos in the form of pinboards.",
                "tiktok": f"{brand_name} is a video-focused social networking service that hosts a variety of short-form user videos, from genres like pranks, stunts, tricks, jokes, dance, and entertainment.",
            }

            if platform.lower() in platform_descriptions:
                main_content = platform_descriptions[platform.lower()]

                # If no description was found, use a portion of the platform description
                if not description:
                    description = main_content.split(".")[0] + "."

        # Ensure minimum content length
        if len(main_content) < 100:
            main_content = f"{brand_name} is a professional organization that provides services and solutions to customers. {description} Our focus is on quality, innovation, and excellence in everything we do."

        return {
            "brand_name": brand_name,
            "description": description,
            "content": main_content,
        }

    except Exception as e:
        domain = extract_domain(url)
        default_brand_name = domain.replace("www.", "")
        default_brand_name = re.sub(
            r"\.com$|\.org$|\.net$|\.io$|\.co$", "", default_brand_name
        ).capitalize()

        return {
            "brand_name": default_brand_name,
            "description": f"Website for {default_brand_name}",
            "content": f"{default_brand_name} is a professional organization providing high-quality services and solutions to customers. Our focus is on quality, innovation, and excellence in everything we do.",
        }


# --- END OF FILE crawler.py ---
