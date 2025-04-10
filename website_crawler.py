import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse

class WebsiteCrawler:
    def __init__(self, base_url):
        self.base_url = base_url
        self.visited_urls = set()
        self.social_patterns = {
            'twitter': r'(twitter\.com/[A-Za-z0-9_]+)',
            'facebook': r'(facebook\.com/[A-Za-z0-9\.]+)',
            'instagram': r'(instagram\.com/[A-Za-z0-9_\.]+)',
            'linkedin': r'(linkedin\.com/(?:company|in)/[A-Za-z0-9_\-\.]+)',
            'youtube': r'(youtube\.com/(?:user|channel|c)/[A-Za-z0-9_\-\.]+)',
            'tiktok': r'(tiktok\.com/@[A-Za-z0-9_\.]+)',
            'pinterest': r'(pinterest\.com/[A-Za-z0-9_\.]+)'
        }
        
    def crawl(self, max_pages=10):
        """
        Crawl the website to extract content and find social media links
        """
        pages_crawled = 0
        queue = [self.base_url]
        website_content = []
        social_links = {}
        
        # First, try to get social links directly from the homepage
        homepage_links = self._get_social_links_from_homepage()
        if homepage_links:
            social_links.update(homepage_links)
            print(f"Found {len(homepage_links)} social links from homepage")
        
        while queue and pages_crawled < max_pages:
            url = queue.pop(0)
            
            # Skip if already visited
            if url in self.visited_urls:
                continue
                
            try:
                print(f"Crawling: {url}")
                response = requests.get(url, timeout=10)
                if response.status_code != 200:
                    continue
                    
                self.visited_urls.add(url)
                pages_crawled += 1
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract content
                text_content = self._extract_content(soup)
                website_content.append({
                    'url': url,
                    'content': text_content
                })
                
                # Find social media links
                found_socials = self._find_social_links(soup, url)
                for platform, link in found_socials.items():
                    if platform not in social_links:
                        social_links[platform] = link
                
                # Add new URLs to the queue if they're part of the same domain
                if pages_crawled < max_pages:
                    new_urls = self._extract_same_domain_links(soup, url)
                    queue.extend([u for u in new_urls if u not in self.visited_urls])
            
            except Exception as e:
                print(f"Error crawling {url}: {e}")
                
        return website_content, social_links
    
    def _get_social_links_from_homepage(self):
        """
        Specifically extract social media links from the homepage.
        This function prioritizes finding social links in common locations.
        """
        try:
            print(f"Checking homepage for social links: {self.base_url}")
            response = requests.get(self.base_url, timeout=10)
            if response.status_code != 200:
                return {}
                
            soup = BeautifulSoup(response.text, 'html.parser')
            social_links = {}
            
            # Check common social link locations
            # 1. Look for elements with common social media classes/ids in header/footer
            social_selectors = [
                'footer a', '.footer a', '#footer a',  # Footer links
                '.social a', '.social-media a', '.social-links a', '.socials a',  # Common social container classes
                'header a', '.header a', '#header a',  # Header links
                '.contact a', '#contact a',  # Contact section
                'a[aria-label*="social"]', 'a[aria-label*="twitter"]', 'a[aria-label*="facebook"]',  # Aria labels
                'a[aria-label*="instagram"]', 'a[aria-label*="linkedin"]', 'a[aria-label*="youtube"]',
                'a[title*="social"]', 'a[title*="twitter"]', 'a[title*="facebook"]',  # Title attributes
                'a[title*="instagram"]', 'a[title*="linkedin"]', 'a[title*="youtube"]',
            ]
            
            for selector in social_selectors:
                for link in soup.select(selector):
                    href = link.get('href')
                    if not href:
                        continue
                        
                    full_url = urljoin(self.base_url, href)
                    
                    for platform, pattern in self.social_patterns.items():
                        if re.search(pattern, full_url, re.IGNORECASE):
                            social_links[platform] = full_url
                            break
            
            return social_links
            
        except Exception as e:
            print(f"Error extracting social links from homepage: {e}")
            return {}

    def _extract_content(self, soup):
        """Extract meaningful content from the page"""
        # Remove script and style elements
        for script_or_style in soup(['script', 'style', 'nav', 'footer']):
            script_or_style.decompose()
            
        # Get text and clean it
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # Try to get specific important elements
        title = soup.title.string if soup.title else ""
        meta_desc = ""
        meta_tag = soup.find("meta", attrs={"name": "description"})
        if meta_tag:
            meta_desc = meta_tag.get("content", "")
        
        h1s = [h1.get_text() for h1 in soup.find_all('h1')]
        
        return {
            "title": title,
            "meta_description": meta_desc,
            "headings": h1s,
            "full_text": text
        }
    
    def _find_social_links(self, soup, current_url):
        """Find social media links in the page"""
        social_links = {}
        
        # Check all links
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            full_url = urljoin(current_url, href)
            
            # Check if it matches any social media pattern
            for platform, pattern in self.social_patterns.items():
                match = re.search(pattern, full_url, re.IGNORECASE)
                if match:
                    social_links[platform] = full_url
                    break
                    
        return social_links
    
    def _extract_same_domain_links(self, soup, current_url):
        """Extract links that are on the same domain as the base URL"""
        base_domain = urlparse(self.base_url).netloc
        links = []
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            
            # Convert relative URLs to absolute
            full_url = urljoin(current_url, href)
            
            # Check if it's the same domain and not an anchor
            parsed = urlparse(full_url)
            if parsed.netloc == base_domain and not parsed.fragment and '#' not in href:
                links.append(full_url)
                
        return links
