# Updated version: unified index for all categories
# Filename: scraper/tasks.py

from celery import shared_task
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote
import time
from datetime import datetime
from elasticsearch import helpers
import logging
from .models import ScrapingTask
from .es_client import es_client

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def scrape_category_task(self, task_id, category, max_pages=2):
    try:
        task = ScrapingTask.objects.get(task_id=task_id)
        task.status = 'RUNNING'
        task.save()

        scraper = CategoryScraper(category)
        result = scraper.run_scraping_pipeline(max_pages)

        task.status = 'SUCCESS' if result['success'] else 'FAILURE'
        task.total_articles = result.get('total_articles', 0)
        task.scraped_articles = result.get('scraped_articles', 0)
        task.error_message = result.get('error_message')
        task.save()

        return result

    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        try:
            task = ScrapingTask.objects.get(task_id=task_id)
            task.status = 'FAILURE'
            task.error_message = str(e)
            task.save()
        except:
            pass
        raise


class CategoryScraper:
    def __init__(self, category):
        self.category = category
        self.base_url = "https://www.prothomalo.com/"
        self.api_url = f"https://www.prothomalo.com/api/v1/collections/{category}"
        self.bengali_to_english_digits = str.maketrans('০১২৩৪৫৬৭৮৯', '0123456789')
        self.bengali_months = {
            'জানুয়ারি': '01', 'ফেব্রুয়ারি': '02', 'মার্চ': '03', 'এপ্রিল': '04',
            'মে': '05', 'জুন': '06', 'জুলাই': '07', 'আগস্ট': '08',
            'সেপ্টেম্বর': '09', 'অক্টোবর': '10', 'নভেম্বর': '11', 'ডিসেম্বর': '12'
        }

    def parse_bengali_date(self, date_str):
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

    def scrape_article(self, url):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

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

            content_paragraphs = soup.select("div.story-content p")
            content = "\n".join([p.get_text(strip=True) for p in content_paragraphs])
            word_count = len(content.split()) if content else 0

            return {
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

        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None

    def get_article_urls(self, max_pages):
        article_urls = []
        stories_per_page = 12

        for page_num in range(max_pages):
            skip = page_num * stories_per_page
            params = {'skip': skip, 'limit': stories_per_page}

            try:
                response = requests.get(self.api_url, params=params, timeout=10)
                response.raise_for_status()

                stories = response.json().get('items', [])
                if not stories:
                    break

                for story in stories:
                    slug = story.get('story', {}).get('slug')
                    if slug:
                        url = urljoin(self.base_url, slug)
                        article_urls.append(url)

                time.sleep(1)

            except Exception as e:
                logger.error(f"Error fetching API page {page_num + 1}: {e}")
                break

        return article_urls

    def bulk_index_articles(self, articles):
        if not articles:
            return False

        try:
            es_client.create_index_if_not_exists()

            actions = []
            for article in articles:
                doc_id = quote(article['url'], safe='')
                action = {
                    "_index": es_client.INDEX_NAME,
                    "_id": doc_id,
                    "_source": article
                }
                actions.append(action)

            success, failed = helpers.bulk(
                es_client.client,
                actions,
                chunk_size=100,
                request_timeout=60,
                raise_on_error=False
            )

            logger.info(f"Indexed {success} documents for {self.category}")
            return True

        except Exception as e:
            logger.error(f"Bulk indexing failed: {e}")
            return False

    def run_scraping_pipeline(self, max_pages):
        try:
            article_urls = self.get_article_urls(max_pages)
            if not article_urls:
                return {
                    'success': False,
                    'error_message': 'No article URLs found',
                    'total_articles': 0,
                    'scraped_articles': 0
                }

            scraped_articles = []
            for url in article_urls:
                article_data = self.scrape_article(url)
                if article_data:
                    scraped_articles.append(article_data)
                time.sleep(1)

            if scraped_articles:
                self.bulk_index_articles(scraped_articles)

            return {
                'success': True,
                'total_articles': len(article_urls),
                'scraped_articles': len(scraped_articles)
            }

        except Exception as e:
            return {
                'success': False,
                'error_message': str(e),
                'total_articles': 0,
                'scraped_articles': 0
            }
