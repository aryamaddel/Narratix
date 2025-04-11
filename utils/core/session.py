import time
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

# Constants for HTTP requests
DEFAULT_TIMEOUT = 12
MAX_RETRIES = 3
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Connection": "keep-alive",
    "Cache-Control": "max-age=0",
    "Upgrade-Insecure-Requests": "1",
}

def get_requests_session():
    """Create a requests session with retry capability"""
    logger.debug("Creating new requests session with retry capability")
    session = requests.Session()
    retry_strategy = Retry(
        total=MAX_RETRIES,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def fetch_page(url, session=None):
    """Fetch a web page with error handling"""
    logger.debug(f"Fetching page: {url}")
    if session is None:
        session = get_requests_session()

    try:
        # Add jitter to avoid rate limiting
        time.sleep(0.5 + (time.time() % 1))

        response = session.get(url, headers=HEADERS, timeout=DEFAULT_TIMEOUT)
        if response.status_code != 200:
            logger.warning(f"Failed to fetch {url}: Status code {response.status_code}")
            return None

        logger.debug(f"Successfully fetched page: {url}")
        return response.content
    except Exception as e:
        logger.error(f"Error fetching {url}: {str(e)}")
        return None
