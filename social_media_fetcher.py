import re
import random
import time
import json
from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta
import logging

class SocialMediaFetcher:
    def __init__(self):
        # No API keys needed for scraping
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
        ]
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger('SocialMediaFetcher')

    def fetch_all(self, social_links):
        """Fetch content from all found social media platforms"""
        results = {}
        for platform, url in social_links.items():
            self.logger.info(f"Fetching content from {platform}: {url}")
            try:
                # Try to scrape data from the actual page
                if platform == 'twitter':
                    username = self._extract_username(url, r'twitter\.com/([A-Za-z0-9_]+)')
                    results[platform] = self._try_scrape_twitter(username, url)
                elif platform == 'facebook':
                    page_id = self._extract_username(url, r'facebook\.com/([A-Za-z0-9\.]+)')
                    results[platform] = self._try_scrape_facebook(page_id, url)
                elif platform == 'instagram':
                    username = self._extract_username(url, r'instagram\.com/([A-Za-z0-9_\.]+)')
                    results[platform] = self._try_scrape_instagram(username, url)
                elif platform == 'linkedin':
                    company = self._extract_username(url, r'linkedin\.com/company/([A-Za-z0-9_\-\.]+)')
                    if company:
                        results[platform] = self._try_scrape_linkedin_company(company, url)
                    else:
                        person = self._extract_username(url, r'linkedin\.com/in/([A-Za-z0-9_\-\.]+)')
                        results[platform] = self._try_scrape_linkedin_person(person, url)
                elif platform == 'youtube':
                    if 'user' in url:
                        channel = self._extract_username(url, r'youtube\.com/user/([A-Za-z0-9_\-\.]+)')
                    else:
                        channel = self._extract_username(url, r'youtube\.com/(?:channel|c)/([A-Za-z0-9_\-\.]+)')
                    results[platform] = self._try_scrape_youtube(channel, url)
                elif platform == 'tiktok':
                    username = self._extract_username(url, r'tiktok\.com/@([A-Za-z0-9_\.]+)')
                    results[platform] = self._try_scrape_tiktok(username, url)
            except Exception as e:
                self.logger.error(f"Error fetching content from {platform}: {e}")
                # Return error information
                results[platform] = {
                    "profile": {},
                    "posts": [],
                    "error": f"Failed to fetch data: {str(e)}",
                    "is_real_data": False
                }
        return results

    def _extract_username(self, url, pattern):
        """Extract username from social media URL using regex"""
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            return match.group(1)
        return ""

    def _get_random_headers(self):
        """Get random user agent and headers to avoid detection"""
        user_agent = random.choice(self.user_agents)
        
        # Create more browser-like headers to avoid detection
        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': random.choice([
                'https://www.google.com/',
                'https://www.bing.com/',
                'https://www.yahoo.com/',
                'https://duckduckgo.com/'
            ]),
            'DNT': '1',
            'Cache-Control': 'max-age=0',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'cross-site',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Add some randomization to the headers
        if random.random() > 0.5:
            headers['Pragma'] = 'no-cache'
        
        return headers

    def _try_request(self, url):
        """Try to make a request with retries and random headers"""
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            headers = self._get_random_headers()
            
            # Add more variation to appear like a real browser
            if random.random() > 0.5:
                headers['Accept-Encoding'] = 'gzip, deflate, br'
            if random.random() > 0.7:
                headers['Connection'] = 'keep-alive'
                
            # Randomize the User-Agent more extensively
            headers['User-Agent'] = random.choice(self.user_agents)
            
            try:
                # Add a random delay between requests to avoid rate limiting
                time.sleep(random.uniform(1.0, 3.0))  # Increased delay to reduce rate limiting
                
                # Use session to maintain cookies
                session = requests.Session()
                
                # First make a request to the homepage to get cookies
                try:
                    base_url = url.split('://')[0] + '://' + url.split('://')[1].split('/')[0]
                    session.get(base_url, headers=headers, timeout=15)  # Increased timeout
                except Exception as e:
                    self.logger.warning(f"Failed to get base URL {base_url}: {e}")
                
                # Then make the actual request
                response = session.get(url, headers=headers, timeout=15)  # Increased timeout
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 999:  # Custom error for anti-scraping
                    self.logger.warning(f"Anti-scraping protection (999) for {url}. Trying with more delay...")
                    # More extensive delay for anti-scraping
                    time.sleep(retry_delay * 3 * (attempt + 1))  # Increased delay multiplier
                elif response.status_code == 403:  # Forbidden
                    self.logger.warning(f"Access forbidden (403) for {url}. Possibly blocked.")
                    # Try with a different approach
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * 4)  # Increased delay
                elif response.status_code == 429:  # Too many requests
                    self.logger.warning(f"Rate limited (429) for {url}. Waiting before retry...")
                    time.sleep(retry_delay * (attempt + 3))  # Increased exponential backoff
                else:
                    self.logger.warning(f"HTTP error {response.status_code} for {url}")
                    time.sleep(retry_delay * 2)  # Increased delay
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Request failed: {e}")
                time.sleep(retry_delay * 2)  # Increased delay
        
        return None

    def _try_scrape_twitter(self, username, url):
        """Try to scrape Twitter data"""
        try:
            # Try to use Nitter as a Twitter frontend that's more scraping-friendly
            nitter_instances = [
                f"https://nitter.net/{username}",
                f"https://nitter.cz/{username}",
                f"https://nitter.it/{username}",
                f"https://nitter.poast.org/{username}"
            ]
            
            for nitter_url in nitter_instances:
                self.logger.info(f"Attempting to scrape from {nitter_url}")
                response = self._try_request(nitter_url)
                if response:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Extract profile info
                    profile_name_elem = soup.select_one('.profile-card-fullname')
                    bio_elem = soup.select_one('.profile-bio')
                    followers_elem = soup.select_one('.profile-statlist .followers .profile-stat-num')
                    following_elem = soup.select_one('.profile-statlist .following .profile-stat-num')
                    
                    if profile_name_elem:  # We have valid data
                        profile = {
                            "username": username,
                            "name": profile_name_elem.text.strip() if profile_name_elem else username,
                            "bio": bio_elem.text.strip() if bio_elem else "",
                            "followers_count": self._extract_follower_count(followers_elem.text.strip() if followers_elem else "0"),
                            "following_count": self._extract_follower_count(following_elem.text.strip() if following_elem else "0"),
                            "is_real_data": True
                        }
                        
                        # Extract tweets
                        posts = []
                        tweet_items = soup.select('.timeline-item')
                        
                        if tweet_items:
                            for tweet in tweet_items[:5]:  # Get first 5 tweets
                                text_elem = tweet.select_one('.tweet-content')
                                likes_elem = tweet.select_one('.tweet-stats .icon-heart')
                                retweets_elem = tweet.select_one('.tweet-stats .icon-retweet')
                                date_elem = tweet.select_one('.tweet-date a')
                                
                                if text_elem:
                                    likes_text = likes_elem.parent.text.strip() if likes_elem else "0"
                                    retweets_text = retweets_elem.parent.text.strip() if retweets_elem else "0"
                                    
                                    posts.append({
                                        "text": text_elem.text.strip(),
                                        "likes": self._extract_count(likes_text),
                                        "retweets": self._extract_count(retweets_text),
                                        "date": date_elem.text.strip() if date_elem else "",
                                        "is_real_data": True
                                    })
                            
                            if posts:
                                result = {"profile": profile, "posts": posts, "is_real_data": True}
                                self.logger.info(f"Successfully scraped Twitter data for {username}")
                                return result
            
            self.logger.warning(f"Could not scrape Twitter data for {username}")
            return {
                "error": "No Twitter data available. Twitter restricts access to their data.",
                "profile": {},
                "posts": []
            }
            
        except Exception as e:
            self.logger.error(f"Error scraping Twitter: {e}")
            return {
                "error": f"Failed to scrape Twitter data: {str(e)}",
                "profile": {},
                "posts": []
            }
    
    def _extract_count(self, count_str):
        """Extract numeric count from string like '1.5K' or '12,000'"""
        if not count_str:
            return 0
        try:
            count_str = count_str.replace(',', '')
            if 'K' in count_str:
                return int(float(count_str.replace('K', '')) * 1000)
            elif 'M' in count_str:
                return int(float(count_str.replace('M', '')) * 1000000)
            else:
                return int(float(count_str))
        except:
            return 0
    
    def _extract_follower_count(self, count_str):
        """Extract follower count from string"""
        return self._extract_count(count_str)
    
    def _try_scrape_facebook(self, page_id, url):
        """Try to scrape Facebook data"""
        try:
            response = self._try_request(url)
            if response:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Attempt to extract meta information
                meta_name = soup.find('meta', property='og:title')
                meta_description = soup.find('meta', property='og:description')
                meta_image = soup.find('meta', property='og:image')
                
                # If we have some meta data, we can return partial real information
                if meta_name or meta_description:
                    profile = {
                        "name": meta_name['content'] if meta_name else page_id,
                        "about": meta_description['content'] if meta_description else "",
                        "image_url": meta_image['content'] if meta_image else "",
                        "is_real_data": "partial"
                    }
                    
                    # Try to find posts
                    posts = []
                    # Facebook actively blocks scraping, so getting posts is difficult
                    # This would require more advanced techniques
                    
                    self.logger.info(f"Partially scraped Facebook data for {page_id}")
                    return {
                        "profile": profile,
                        "posts": posts,
                        "is_real_data": "partial"
                    }
            
            self.logger.warning(f"Could not scrape Facebook data for {page_id}")
            return {
                "error": "No Facebook data available. Facebook restricts access to their data.",
                "profile": {},
                "posts": []
            }
        except Exception as e:
            self.logger.error(f"Error scraping Facebook: {e}")
            return {
                "error": f"Failed to scrape Facebook data: {str(e)}",
                "profile": {},
                "posts": []
            }
    
    def _try_scrape_instagram(self, username, url):
        """Try to scrape Instagram, use direct scraping approach"""
        try:
            # Bibliogram is no longer reliable, trying direct Instagram approach
            response = self._try_request(url)
            
            if response and response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Try to extract from meta tags
                meta_name = soup.find('meta', property='og:title')
                meta_description = soup.find('meta', property='og:description')
                meta_image = soup.find('meta', property='og:image')
                
                # Look for JSON data in script tags
                profile_data = None
                for script in soup.find_all('script'):
                    if script.string and 'window._sharedData' in script.string:
                        try:
                            json_text = script.string.replace('window._sharedData = ', '').rstrip(';')
                            data = json.loads(json_text)
                            if 'entry_data' in data and 'ProfilePage' in data['entry_data']:
                                profile_data = data['entry_data']['ProfilePage'][0]['graphql']['user']
                                break
                        except:
                            continue
                
                if meta_name or meta_description or profile_data:
                    # Create profile data from available information
                    if profile_data:
                        # We got JSON data - use it
                        profile = {
                            "username": username,
                            "name": profile_data.get('full_name', username),
                            "bio": profile_data.get('biography', ''),
                            "followers_count": profile_data.get('edge_followed_by', {}).get('count', 0),
                            "following_count": profile_data.get('edge_follow', {}).get('count', 0),
                            "posts_count": profile_data.get('edge_owner_to_timeline_media', {}).get('count', 0),
                            "is_real_data": True
                        }
                        
                        # Extract posts from JSON data
                        posts = []
                        if 'edge_owner_to_timeline_media' in profile_data and 'edges' in profile_data['edge_owner_to_timeline_media']:
                            post_edges = profile_data['edge_owner_to_timeline_media']['edges']
                            for edge in post_edges[:5]:
                                node = edge['node']
                                posts.append({
                                    "caption": node.get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {}).get('text', '') if node.get('edge_media_to_caption', {}).get('edges') else '',
                                    "likes": node.get('edge_liked_by', {}).get('count', 0) or node.get('edge_media_preview_like', {}).get('count', 0),
                                    "date": datetime.fromtimestamp(node.get('taken_at_timestamp', 0)).strftime('%Y-%m-%d') if node.get('taken_at_timestamp') else '',
                                    "is_real_data": True
                                })
                    else:
                        # Fall back to meta data
                        title = meta_name['content'] if meta_name else username
                        # Clean up the title which is usually in format "Username (@username) • Instagram"
                        name = title.split('(')[0].strip() if '(' in title else title.replace('• Instagram', '').strip()
                        
                        profile = {
                            "username": username,
                            "name": name,
                            "bio": meta_description['content'] if meta_description else "",
                            "image": meta_image['content'] if meta_image else "",
                            "is_real_data": "partial"  # Only meta data available
                        }
                        posts = []
                    
                    self.logger.info(f"Successfully scraped Instagram data for {username}")
                    return {"profile": profile, "posts": posts, "is_real_data": True if profile_data else "partial"}
            
            # If direct scraping failed, try alternate public page that might have some info
            alt_url = f"https://greatfon.com/v/{username}"
            response = self._try_request(alt_url)
            
            if response and response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract basic profile info
                name_elem = soup.select_one('.user-info-full .user-name')
                bio_elem = soup.select_one('.user-info-full .user-biography')
                stats = soup.select('.user-info-full .user-stats .count')
                
                if name_elem:
                    followers = self._extract_count(stats[1].text.strip()) if len(stats) > 1 else 0
                    following = self._extract_count(stats[2].text.strip()) if len(stats) > 2 else 0
                    
                    profile = {
                        "username": username,
                        "name": name_elem.text.strip(),
                        "bio": bio_elem.text.strip() if bio_elem else "",
                        "followers_count": followers,
                        "following_count": following,
                        "is_real_data": "partial"  # Third-party source
                    }
                    
                    # Try to extract posts
                    posts = []
                    post_elems = soup.select('.user-media-list .media-item')
                    
                    for post in post_elems[:5]:
                        caption_elem = post.select_one('.media-item-caption')
                        
                        if caption_elem:
                            posts.append({
                                "caption": caption_elem.text.strip(),
                                "is_real_data": "partial"
                            })
                    
                    self.logger.info(f"Partially scraped Instagram data for {username} from alternative source")
                    return {"profile": profile, "posts": posts, "is_real_data": "partial"}
            
            # If all else fails, provide a generic profile
            self.logger.warning(f"Could not scrape Instagram data for {username}")
            return {
                "profile": {
                    "username": username,
                    "name": username.replace('_', ' ').title(),
                    "is_real_data": False
                },
                "posts": [],
                "error": "Unable to retrieve Instagram data. Instagram restricts access to their data.",
                "is_real_data": False
            }
        except Exception as e:
            self.logger.error(f"Error scraping Instagram: {e}")
            return {
                "profile": {
                    "username": username,
                    "name": username.replace('_', ' ').title(),
                    "is_real_data": False
                },
                "posts": [],
                "error": f"Failed to scrape Instagram data: {str(e)}",
                "is_real_data": False
            }
    
    def _try_scrape_linkedin_company(self, company, url):
        """Try to scrape LinkedIn company data"""
        try:
            response = self._try_request(url)
            if response:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Try to extract some basic info from meta tags
                meta_name = soup.find('meta', property='og:title')
                meta_description = soup.find('meta', property='og:description')
                
                if meta_name or meta_description:
                    profile = {
                        "name": meta_name['content'].split('|')[0].strip() if meta_name else company.capitalize(),
                        "about": meta_description['content'] if meta_description else "",
                        "is_real_data": "partial"  # LinkedIn blocks most scraping
                    }
                    
                    self.logger.info(f"Partially scraped LinkedIn company data for {company}")
                    return {
                        "profile": profile,
                        "posts": [],
                        "is_real_data": "partial"
                    }
                
            self.logger.warning(f"Could not scrape LinkedIn company data for {company}")
            return {
                "error": "No LinkedIn company data available. LinkedIn restricts access to their data.",
                "profile": {},
                "posts": []
            }
        except Exception as e:
            self.logger.error(f"Error scraping LinkedIn company: {e}")
            return {
                "error": f"Failed to scrape LinkedIn company data: {str(e)}",
                "profile": {},
                "posts": []
            }
    
    def _try_scrape_linkedin_person(self, person, url):
        """Try to scrape LinkedIn person data with improved handling"""
        try:
            # Using more sophisticated approach to avoid detection
            time.sleep(random.uniform(2.0, 5.0))  # More delay before LinkedIn requests
            
            headers = self._get_random_headers()
            # Add more LinkedIn-specific headers
            headers['Referer'] = 'https://www.google.com/'
            headers['Accept-Language'] = 'en-US,en;q=0.9'
            
            session = requests.Session()
            # Visit LinkedIn homepage first to get cookies
            try:
                session.get('https://www.linkedin.com/', headers=headers, timeout=20)
                time.sleep(random.uniform(1.5, 3.0))
            except Exception as e:
                self.logger.warning(f"Failed to get LinkedIn homepage: {e}")
            
            # Try to get public data without logging in
            response = session.get(url, headers=headers, timeout=20)
            
            if response and response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Try to extract data from meta tags first
                meta_name = soup.find('meta', property='og:title')
                meta_description = soup.find('meta', property='og:description')
                meta_image = soup.find('meta', property='og:image')
                
                if meta_name or meta_description:
                    # Clean up the title which is usually in format "Name - Position - Company | LinkedIn"
                    title = meta_name['content'] if meta_name else ""
                    name = title.split('-')[0].strip() if '-' in title else title.split('|')[0].strip()
                    
                    # Try to extract headline
                    headline = ""
                    if '-' in title and len(title.split('-')) > 1:
                        headline = title.split('-')[1].strip()
                    
                    # If we have a description, use it for headline if not already set
                    if not headline and meta_description:
                        headline = meta_description['content']
                    
                    profile = {
                        "name": name if name else person.replace('-', ' ').title(),
                        "headline": headline,
                        "image": meta_image['content'] if meta_image else "",
                        "is_real_data": "partial"  # LinkedIn blocks most scraping
                    }
                    
                    self.logger.info(f"Partially scraped LinkedIn person data for {person}")
                    return {
                        "profile": profile,
                        "posts": [],
                        "is_real_data": "partial"
                    }
                
                # If meta tags didn't work, try direct page parsing for public data
                name_elem = soup.select_one('.top-card-layout__title')
                headline_elem = soup.select_one('.top-card-layout__headline')
                
                if name_elem:
                    profile = {
                        "name": name_elem.text.strip(),
                        "headline": headline_elem.text.strip() if headline_elem else "",
                        "is_real_data": "partial"
                    }
                    
                    self.logger.info(f"Partially scraped LinkedIn person data for {person}")
                    return {
                        "profile": profile,
                        "posts": [],
                        "is_real_data": "partial"
                    }
            
            # If direct scraping failed, provide a formatted name as fallback
            formatted_name = person.replace('-', ' ').title()
            self.logger.warning(f"Could not scrape LinkedIn person data for {person}")
            return {
                "profile": {
                    "name": formatted_name,
                    "headline": f"Professional on LinkedIn",
                    "is_real_data": False
                },
                "posts": [],
                "error": "LinkedIn restricts access to profile data without authentication."
            }
        except Exception as e:
            self.logger.error(f"Error scraping LinkedIn person: {e}")
            formatted_name = person.replace('-', ' ').title()
            return {
                "profile": {
                    "name": formatted_name,
                    "headline": f"Professional on LinkedIn",
                    "is_real_data": False
                },
                "posts": [],
                "error": f"Failed to scrape LinkedIn person data: {str(e)}"
            }
    
    def _try_scrape_youtube(self, channel, url):
        """Try to scrape YouTube data"""
        try:
            response = self._try_request(url)
            if response:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Try to extract channel info from meta tags
                meta_title = soup.find('meta', property='og:title')
                meta_description = soup.find('meta', property='og:description')
                
                if meta_title:
                    # Try to extract subscriber count from page content
                    subscriber_text = None
                    script_tags = soup.find_all('script')
                    for script in script_tags:
                        if script.string and '"subscriberCountText"' in script.string:
                            subscriber_match = re.search(r'"subscriberCountText":\{"runs":\[\{"text":"([\d\.,M\sK]+)"', script.string)
                            if subscriber_match:
                                subscriber_text = subscriber_match.group(1)
                                break
                    
                    profile = {
                        "name": meta_title['content'] if meta_title else channel,
                        "description": meta_description['content'] if meta_description else "",
                        "subscribers": self._extract_count(subscriber_text) if subscriber_text else 0,
                        "is_real_data": "partial" 
                    }
                    
                    # Try to extract video data
                    videos = []
                    video_sections = soup.select("ytd-grid-video-renderer")
                    
                    for video in video_sections[:5]:
                        title_elem = video.select_one("#video-title")
                        views_elem = video.select_one("#metadata-line span:first-child")
                        date_elem = video.select_one("#metadata-line span:last-child")
                        
                        if title_elem:
                            videos.append({
                                "title": title_elem.text.strip(),
                                "views": views_elem.text.strip() if views_elem else "Unknown views",
                                "date": date_elem.text.strip() if date_elem else "",
                                "is_real_data": True
                            })
                    
                    self.logger.info(f"Partially scraped YouTube data for {channel}")
                    return {
                        "profile": profile,
                        "posts": videos,
                        "is_real_data": "partial" if not videos else True
                    }
                
            self.logger.warning(f"Could not scrape YouTube data for {channel}")
            return {
                "error": "No YouTube data available. YouTube may have restricted access.",
                "profile": {},
                "posts": []
            }
        except Exception as e:
            self.logger.error(f"Error scraping YouTube: {e}")
            return {
                "error": f"Failed to scrape YouTube data: {str(e)}",
                "profile": {},
                "posts": []
            }
    
    def _try_scrape_tiktok(self, username, url):
        """Try to scrape TikTok data"""
        try:
            response = self._try_request(url)
            if response:
                # Look for JSON data in the page
                json_data_match = re.search(r'<script id="SIGI_STATE" type="application/json">(.*?)</script>', response.text)
                if json_data_match:
                    try:
                        json_data = json.loads(json_data_match.group(1))
                        user_data = json_data.get('UserModule', {}).get('users', {}).get(username, {})
                        
                        if user_data:
                            stats = user_data.get('stats', {})
                            profile = {
                                "username": username,
                                "name": user_data.get('nickname', username),
                                "bio": user_data.get('signature', ''),
                                "followers_count": stats.get('followerCount', 0),
                                "following_count": stats.get('followingCount', 0),
                                "likes": stats.get('heartCount', 0),
                                "is_real_data": True
                            }
                            
                            # Try to get video information
                            videos = []
                            item_list = json_data.get('ItemModule', {})
                            if item_list:
                                count = 0
                                for item_id, item in item_list.items():
                                    if count >= 5:  # Limit to 5 videos
                                        break
                                        
                                    videos.append({
                                        "description": item.get('desc', ''),
                                        "likes": item.get('stats', {}).get('diggCount', 0),
                                        "comments": item.get('stats', {}).get('commentCount', 0),
                                        "shares": item.get('stats', {}).get('shareCount', 0),
                                        "date": datetime.fromtimestamp(item.get('createTime', 0)).strftime('%Y-%m-%d'),
                                        "is_real_data": True
                                    })
                                    count += 1
                            
                            self.logger.info(f"Successfully scraped TikTok data for {username}")
                            return {
                                "profile": profile,
                                "posts": videos,
                                "is_real_data": True
                            }
                    except Exception as e:
                        self.logger.error(f"Error parsing TikTok JSON data: {e}")
                
            self.logger.warning(f"Could not scrape TikTok data for {username}")
            return {
                "error": "No TikTok data available. TikTok may have restricted access.",
                "profile": {},
                "posts": []
            }
        except Exception as e:
            self.logger.error(f"Error scraping TikTok: {e}")
            return {
                "error": f"Failed to scrape TikTok data: {str(e)}",
                "profile": {},
                "posts": []
            }
