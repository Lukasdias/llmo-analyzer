"""
LLMO Analyzer - Web Scraper Module
Extracts content and metadata from URLs using trafilatura and BeautifulSoup.
"""

import json
import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from trafilatura import fetch_url, extract


@dataclass
class ScrapedContent:
    """Container for scraped website content."""
    url: str
    title: str
    content: str
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    json_ld: list[dict] = None
    headings: dict[str, list[str]] = None
    has_bullet_points: bool = False
    word_count: int = 0
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.json_ld is None:
            self.json_ld = []
        if self.headings is None:
            self.headings = {"h1": [], "h2": [], "h3": [], "h4": [], "h5": [], "h6": []}


class WebScraper:
    """Scrapes web pages and extracts content with metadata."""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        })
    
    def scrape(self, url: str) -> ScrapedContent:
        """
        Scrape a URL and extract content, metadata, and structure.
        
        Args:
            url: The URL to scrape
            
        Returns:
            ScrapedContent object with all extracted data
        """
        # Validate URL
        if not self._is_valid_url(url):
            return ScrapedContent(
                url=url,
                title="",
                content="",
                error="Invalid URL format. Please provide a valid HTTP or HTTPS URL."
            )
        
        try:
            # First, fetch with trafilatura for main content extraction
            downloaded = fetch_url(url)
            
            if downloaded is None:
                return ScrapedContent(
                    url=url,
                    title="",
                    content="",
                    error=f"Could not fetch content from {url}. The site may block scraping."
                )
            
            # Extract main content with trafilatura
            main_content = extract(
                downloaded,
                include_comments=False,
                include_tables=True,
                no_fallback=False,
                output_format="txt"
            )
            
            # Also fetch with requests for metadata and structure analysis
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Extract metadata
            title = self._extract_title(soup)
            meta_description = self._extract_meta_description(soup)
            meta_keywords = self._extract_meta_keywords(soup)
            
            # Extract JSON-LD schema
            json_ld = self._extract_json_ld(soup)
            
            # Extract headings hierarchy
            headings = self._extract_headings(soup)
            
            # Check for bullet points
            has_bullet_points = self._has_bullet_points(soup)
            
            # Calculate word count
            content_to_use = main_content if main_content else soup.get_text(separator=' ', strip=True)
            word_count = len(content_to_use.split())
            
            return ScrapedContent(
                url=url,
                title=title,
                content=content_to_use,
                meta_description=meta_description,
                meta_keywords=meta_keywords,
                json_ld=json_ld,
                headings=headings,
                has_bullet_points=has_bullet_points,
                word_count=word_count
            )
            
        except requests.exceptions.HTTPError as e:
            return ScrapedContent(
                url=url,
                title="",
                content="",
                error=f"HTTP Error {e.response.status_code}: {e.response.reason}"
            )
        except requests.exceptions.ConnectionError:
            return ScrapedContent(
                url=url,
                title="",
                content="",
                error=f"Connection error. Could not connect to {url}."
            )
        except requests.exceptions.Timeout:
            return ScrapedContent(
                url=url,
                title="",
                content="",
                error=f"Request timeout. The server at {url} took too long to respond."
            )
        except Exception as e:
            return ScrapedContent(
                url=url,
                title="",
                content="",
                error=f"Error scraping {url}: {str(e)}"
            )
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid."""
        try:
            result = urlparse(url)
            return all([result.scheme in ['http', 'https'], result.netloc])
        except:
            return False
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title."""
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text(strip=True)
        
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text(strip=True)
        
        return "Untitled"
    
    def _extract_meta_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract meta description."""
        meta = soup.find('meta', attrs={'name': 'description'})
        if meta:
            return meta.get('content')
        
        meta = soup.find('meta', attrs={'property': 'og:description'})
        if meta:
            return meta.get('content')
        
        return None
    
    def _extract_meta_keywords(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract meta keywords."""
        meta = soup.find('meta', attrs={'name': 'keywords'})
        if meta:
            return meta.get('content')
        return None
    
    def _extract_json_ld(self, soup: BeautifulSoup) -> list[dict]:
        """Extract JSON-LD structured data."""
        json_ld_data = []
        
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                json_ld_data.append(data)
            except (json.JSONDecodeError, TypeError):
                continue
        
        return json_ld_data
    
    def _extract_headings(self, soup: BeautifulSoup) -> dict[str, list[str]]:
        """Extract all headings (H1-H6)."""
        headings = {"h1": [], "h2": [], "h3": [], "h4": [], "h5": [], "h6": []}
        
        for level in range(1, 7):
            tag = f"h{level}"
            elements = soup.find_all(tag)
            headings[tag] = [h.get_text(strip=True) for h in elements if h.get_text(strip=True)]
        
        return headings
    
    def _has_bullet_points(self, soup: BeautifulSoup) -> bool:
        """Check if page contains bullet points (ul/li elements)."""
        return bool(soup.find(['ul', 'ol']))
