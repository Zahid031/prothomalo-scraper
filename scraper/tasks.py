from celery import shared_task
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote
import time
from datetime import datetime
from elasticsearch import helpers
import logging
import json
import zipfile
import io
import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from .models import ScrapingTask
from .es_client import es_client

logger = logging.getLogger(__name__)

class S3Handler:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1')
        )
        self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    
    def create_zip_file(self, articles, task_id, category):
        """Create a zip file containing the scraped articles data"""
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            articles_json = json.dumps(articles, indent=2, ensure_ascii=False)
            zip_file.writestr(f'{task_id}_articles.json', articles_json.encode('utf-8'))
            
            metadata = {
                'task_id': task_id,
                'category': category,
                'total_articles': len(articles),
                'scraped_at': datetime.now().isoformat(),
                'file_format': 'json',
                'encoding': 'utf-8'
            }
            metadata_json = json.dumps(metadata, indent=2, ensure_ascii=False)
            zip_file.writestr(f'{task_id}_metadata.json', metadata_json.encode('utf-8'))
            
            for i, article in enumerate(articles):
                article_json = json.dumps(article, indent=2, ensure_ascii=False)
                zip_file.writestr(
                    f'articles/article_{i+1:04d}.json', 
                    article_json.encode('utf-8')
                )
        
        zip_buffer.seek(0)
        return zip_buffer
    
    def upload_to_s3(self, zip_buffer, task_id, category):
        """Upload the zip file to S3"""
        try:
            timestamp = datetime.now().strftime('%Y/%m/%d')
            s3_key = f'scraped-data/{category}/{timestamp}/{task_id}.zip'
            
            self.s3_client.upload_fileobj(
                zip_buffer,
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'ContentType': 'application/zip',
                    'Metadata': {
                        'task-id': task_id,
                        'category': category,
                        'upload-timestamp': datetime.now().isoformat()
                    }
                }
            )
            
            s3_url = f'https://{self.bucket_name}.s3.amazonaws.com/{s3_key}'
            logger.info(f"Successfully uploaded zip file to S3: {s3_url}")
            return s3_url, s3_key
            
        except ClientError as e:
            logger.error(f"Failed to upload to S3: {e}")
            raise
    
    def save_articles_to_s3(self, articles, task_id, category):
        """Main method to save articles to S3 as zip file"""
        if not articles:
            logger.warning(f"No articles to save for task {task_id}")
            return None, None
        
        try:
            zip_buffer = self.create_zip_file(articles, task_id, category)
            
            # Upload to S3
            s3_url, s3_key = self.upload_to_s3(zip_buffer, task_id, category)
            
            return s3_url, s3_key
            
        except Exception as e:
            logger.error(f"Failed to save articles to S3: {e}")
            raise

@shared_task(bind=True)
def scrape_category_task(self, task_id, category, max_pages=2):
    try:
        task = ScrapingTask.objects.get(task_id=task_id)
        task.status = 'RUNNING'
        task.save()
        logger.info(f"[Task {task_id}] Starting scrape for category: {category}")

        scraper = CategoryScraper(category)
        result = scraper.run_scraping_pipeline(max_pages, task_id)

        task.status = 'SUCCESS' if result['success'] else 'FAILURE'
        task.total_articles = result.get('total_articles', 0)
        task.scraped_articles = result.get('scraped_articles', 0)
        task.error_message = result.get('error_message')
        
        # Save S3 information if successful
        if result['success'] and result.get('s3_url'):
            task.s3_url = result['s3_url']
            task.s3_key = result['s3_key']
        
        task.save()

        logger.info(f"[Task {task_id}] Completed with status: {task.status}")
        return result

    except Exception as e:
        logger.error(f"[Task {task_id}] Failed: {e}")
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

            logger.debug(f"Scraped article: {headline[:50]}...")
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

        logger.info(f"Collected {len(article_urls)} article URLs from API")
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

            logger.info(f"Indexed {success} articles to unified index")
            return True

        except Exception as e:
            logger.error(f"Bulk indexing failed: {e}")
            return False

    def run_scraping_pipeline(self, max_pages, task_id):
        article_urls = []
        s3_url = None
        s3_key = None
        
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
                # Index to Elasticsearch
                es_success = self.bulk_index_articles(scraped_articles)
                
                # Save to S3 if ES indexing was successful
                if es_success:
                    try:
                        s3_handler = S3Handler()
                        s3_url, s3_key = s3_handler.save_articles_to_s3(
                            scraped_articles, task_id, self.category
                        )
                        logger.info(f"Articles saved to S3: {s3_url}")
                    except Exception as s3_error:
                        logger.error(f"S3 upload failed but ES indexing succeeded: {s3_error}")
                        # Continue with success since ES indexing worked

            return {
                'success': True,
                'total_articles': len(article_urls),
                'scraped_articles': len(scraped_articles),
                's3_url': s3_url,
                's3_key': s3_key
            }

        except Exception as e:
            return {
                'success': False,
                'error_message': str(e),
                'total_articles': len(article_urls),
                'scraped_articles': 0,
                's3_url': None,
                's3_key': None
            }