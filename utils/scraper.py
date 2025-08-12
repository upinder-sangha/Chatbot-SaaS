# utils/scraper.py
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, urldefrag
from urllib.robotparser import RobotFileParser
import time
import logging
from typing import Set, Dict, Tuple
from collections import deque

logger = logging.getLogger(__name__)

def scrape_site(url: str, max_depth: int = 2, max_pages: int = 20, max_char: int = 50000) -> str:
    """
    Scrape a website starting from the given URL, following links within the same domain.
    
    Args:
        url: Starting URL to scrape
        max_depth: Maximum depth of links to follow (0 = only starting page)
        max_pages: Maximum number of pages to scrape
        max_char: Maximum number of characters to store
        
    Returns:
        Concatenated text from all scraped pages (truncated at 50,000 chars)
    """
    try:
        # Parse the starting URL to get domain
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # Check robots.txt
        if not _is_allowed_by_robots(url, base_url):
            logger.warning(f"Scraping disallowed by robots.txt for URL: {url}")
            return ""
        
        # Initialize crawling
        visited_urls: Set[str] = set()
        queue: deque = deque()
        queue.append((url, 0))  # (url, depth)
        visited_urls.add(url)
        extracted_text = ""
        pages_scraped = 0
        
        # Set headers to identify our bot
        headers = {
            "User-Agent": "DocativeBot/1.0 (https://docative.com; info@docative.com)"
        }
        
        while queue and pages_scraped < max_pages:
            current_url, depth = queue.popleft()
            
            # Skip if we've exceeded max depth
            if depth > max_depth:
                continue
                
            try:
                # Fetch the page with a timeout
                response = requests.get(current_url, headers=headers, timeout=10)
                
                # Skip non-HTML content
                content_type = response.headers.get("Content-Type", "")
                if "text/html" not in content_type:
                    continue
                    
                # Parse the page
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Extract clean text
                page_text = _extract_text(soup)
                if page_text:
                    extracted_text += page_text + " "
                    pages_scraped += 1
                    logger.info(f"Scraped {current_url} ({pages_scraped}/{max_pages} pages)")
                
                # If we haven't reached max_pages and haven't exceeded max_depth, find links
                if pages_scraped < max_pages and depth < max_depth:
                    links = _find_links(soup, current_url, base_url)
                    for link in links:
                        # Skip if already visited or not allowed by robots
                        if link not in visited_urls and _is_allowed_by_robots(link, base_url):
                            visited_urls.add(link)
                            queue.append((link, depth + 1))
                
                # Be polite - add a small delay
                time.sleep(0.5)
                
            except Exception as e:
                logger.warning(f"Failed to scrape {current_url}: {str(e)}")
                continue
        
        # Truncate if needed
        if len(extracted_text) > max_char:
            extracted_text = extracted_text[:max_char]
            logger.info(f"Extracted text truncated to {max_char} characters.")
            
        return extracted_text.strip()
    
    except Exception as e:
        logger.error(f"Error in scrape_site: {str(e)}")
        return ""

def _is_allowed_by_robots(url: str, base_url: str) -> bool:
    """Check if URL is allowed by robots.txt"""
    try:
        rp = RobotFileParser()
        robots_url = f"{base_url}/robots.txt"
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch("*", url)
    except Exception as e:
        logger.warning(f"Could not check robots.txt for {base_url}: {str(e)}")
        # If we can't check robots.txt, we'll proceed with caution
        return True

def _extract_text(soup: BeautifulSoup) -> str:
    """Extract clean text from BeautifulSoup object"""
    # Remove script, style, and other non-content elements
    for element in soup(["script", "style", "noscript", "iframe", "svg"]):
        element.decompose()
    
    # Get text and clean up whitespace
    text = soup.get_text(separator=' ', strip=True)
    return text

def _find_links(soup: BeautifulSoup, current_url: str, base_url: str) -> Set[str]:
    """Find all valid links within the same domain"""
    links = set()
    parsed_base = urlparse(base_url)
    
    for a_tag in soup.find_all("a", href=True):
        href = a_tag.get("href")
        if not href:
            continue
            
        # Convert to absolute URL
        absolute_url = urljoin(current_url, href)
        
        # Remove fragments (#)
        absolute_url = urldefrag(absolute_url).url
        
        # Parse to check domain
        parsed_url = urlparse(absolute_url)
        
        # Only include URLs from the same domain
        if parsed_url.netloc == parsed_base.netloc:
            links.add(absolute_url)
    
    return links