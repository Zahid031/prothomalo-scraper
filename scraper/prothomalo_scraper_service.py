
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote
import time
from datetime import datetime
import logging
from typing import Optional, Dict, List, Any

logger = logging.getLogger('scraper')


class ProthomAloScraperService:
    """Enhanced version of the original scraper for Django integration"""
    
    def __init__(self, category='politics'):
        self.category = category
        self.base_url = "https://www.prothomalo.com/"
        self.api_url = f"https://www.prothomalo.com/api/v1/collections/{category}"
        self.stories_per_page = 12
        self.request_delay = 1
        
        # Bengali date parsing utilities
        self.bengali_to_english_digits = str.maketrans('০১২৩৪৫৬৭৮৯', '0123456789')
        self.bengali_months = {
            'জানুয়ারি': '01', 'ফেব্রুয়ারি': '02', 'মার্চ': '03', 'এপ্রিল': '04',
            'মে': '05', 'জুন': '06', 'জুলাই': '07', 'আগস্ট': '08',
            'সেপ্টেম্বর': '09', 'অক্টোবর': '10', 'নভেম্বর': '11', 'ডিসেম্বর': '12'
        }
    
    def parse_bengali_date(self, date_str: str) -> Optional[str]:
        """Convert Bengali datetime string to ISO format with time"""
        if not date_str or "not found" in date_str.lower():
            return None

        try:
            parts = date_str.strip().split(",")
            if len(parts) != 2:
                return None

            date_part_bn = parts[0].strip()
            time_part_bn = parts[1].strip().replace(" ", "")

            date_en = date_part_bn.translate(self.bengali_to_english_digits)
            time_en = time_part_bn.translate(self.bengali_to_english_digits)

            day, month_bn, year = date_en.split()
            month = self.bengali_months.get(month_bn)
            if not month:
                return None

            return f"{year}-{month}-{day} {time_en}"

        except Exception as e:
            logger.warning(f"Failed to parse datetime '{date_str}': {e}")
            return None
    
    def get_article_urls_from_api(self, max_pages: int) -> List[str]:
        """Fetch article URLs from the Prothom Alo API"""
        article_urls = []
        
        for page_num in range(max_pages):
            skip = page_num * self.stories_per_page
            params = {'skip': skip, 'limit': self.stories_per_page}
            
            try:
                logger.info(f"Fetching page {page_num + 1}/{max_pages} from API for category '{self.category}'...")
                response = requests.get(self.api_url, params=params, timeout=10)
                response.raise_for_status()
                
                stories = response.json().get('items', [])
                if not stories:
                    logger.info("No more stories found, stopping pagination")
                    break
                
                for story in stories:
                    slug = story.get('story', {}).get('slug')
                    if slug:
                        url = urljoin(self.base_url, slug)
                        article_urls.append(url)
                
                time.sleep(self.request_delay)
                
            except Exception as e:
                logger.error(f"Error fetching API page {page_num + 1}: {e}")
                break
        
        logger.info(f"Found {len(article_urls)} article URLs for category '{self.category}'")
        return article_urls
    
    def scrape_single_article(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape a single article from the given URL"""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Extract article data
            headline_tag = soup.select_one("h1.IiRps")
            headline = headline_tag.get_text(strip=True) if headline_tag else "Headline not found"
            
            author_tag = soup.select_one("span.contributor-name._8TSJC")
            author = author_tag.get_text(strip=True) if author_tag else "Author not found"
            
            location_tag = soup.select_one("span.author-location._8-umj")
            location = location_tag.get_text(strip=True) if location_tag else "Location not found"
            location = location.replace("Location: ", "").strip()
            
            date_tag = soup.select_one("div.time-social-share-wrapper span:first-child")
            publication_date_raw = date_tag.get_text(strip=True) if date_tag else "Date not found"
            publication_date_cleaned = publication_date_raw.split(":", 1)[-1].strip()
            publication_date = self.parse_bengali_date(publication_date_cleaned)
            
            # Extract content
            content_paragraphs = soup.select("div.story-content p")
            content = "\n".join([p.get_text(strip=True) for p in content_paragraphs])
            word_count = len(content.split()) if content else 0
            
            article_data = {
                "url": url,
                "headline": headline,
                "author": author,
                "location": location,
                "published_at": publication_date,
                "content": content,
                "scraped_at": datetime.now().isoformat(),
                "word_count": word_count,
                "category": self.category
            }
            
            logger.info(f"Successfully scraped: {headline[:50]}...")
            return article_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP error scraping {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error scraping {url}: {e}")
            return None
    
    def scrape_articles(self, max_pages: int) -> Dict[str, Any]:
        """Main scraping method that returns comprehensive results"""
        logger.info(f"Starting scraping for category '{self.category}' with {max_pages} pages...")
        
        # Get article URLs
        article_urls = self.get_article_urls_from_api(max_pages)
        total_urls = len(article_urls)
        
        if not article_urls:
            return {
                'success': False,
                'total_articles_found': 0,
                'articles_scraped': 0,
                'articles': [],
                'error': 'No article URLs found'
            }
        
        # Scrape articles
        scraped_articles = []
        for i, url in enumerate(article_urls, 1):
            logger.info(f"Scraping article {i}/{total_urls}: {url}")
            
            article_data = self.scrape_single_article(url)
            if article_data:
                scraped_articles.append(article_data)
            
            if i < total_urls:
                time.sleep(self.request_delay)
        
        logger.info(f"Successfully scraped {len(scraped_articles)}/{total_urls} articles")
        
        return {
            'success': True,
            'total_articles_found': total_urls,
            'articles_scraped': len(scraped_articles),
            'articles': scraped_articles,
            'error': None
        }
