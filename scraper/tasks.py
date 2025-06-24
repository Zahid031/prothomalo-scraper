
from celery import shared_task
from celery.utils.log import get_task_logger
from .models import ScrapingTask, Article
from .prothomalo_scraper_service import ProthomAloScraperService
from .elasticsearch_client import es_client
from django.utils import timezone
from datetime import datetime

logger = get_task_logger(__name__)


@shared_task(bind=True)
def scrape_prothomalo_articles(self, category, max_pages=2):
    """
    Celery task to scrape articles from Prothom Alo
    """
    task_id = self.request.id
    logger.info(f"Starting scraping task {task_id} for category '{category}'")
    
    # Create or get the task record
    try:
        task_record, created = ScrapingTask.objects.get_or_create(
            task_id=task_id,
            defaults={
                'category': category,
                'max_pages': max_pages,
                'status': 'STARTED',
                'started_at': timezone.now()
            }
        )
        
        if not created:
            task_record.status = 'STARTED'
            task_record.started_at = timezone.now()
            task_record.save()
        
    except Exception as e:
        logger.error(f"Failed to create/update task record: {e}")
        return {
            'success': False,
            'error': f'Database error: {str(e)}'
        }
    
    try:
        # Check Elasticsearch connection first
        if not es_client.is_connected():
            logger.error("Elasticsearch is not connected - attempting to reconnect...")
            es_client.connect()
            if not es_client.is_connected():
                raise Exception("Could not establish Elasticsearch connection")
        
        # Initialize scraper
        scraper = ProthomAloScraperService(category=category)
        
        # Perform scraping
        scraping_results = scraper.scrape_articles(max_pages)
        
        if not scraping_results['success']:
            task_record.status = 'FAILURE'
            task_record.error_message = scraping_results.get('error', 'Unknown error')
            task_record.completed_at = timezone.now()
            task_record.save()
            
            return {
                'success': False,
                'error': scraping_results.get('error', 'Scraping failed'),
                'task_id': task_id
            }
        
        # Update task record with scraping results
        task_record.total_articles_found = scraping_results['total_articles_found']
        task_record.articles_scraped = scraping_results['articles_scraped']
        task_record.save()
        
        # Save articles to Django database and prepare for Elasticsearch
        articles_saved = 0
        articles_for_es = []
        
        for article_data in scraping_results['articles']:
            try:
                # Parse published_at
                published_at = None
                if article_data.get('published_at'):
                    try:
                        published_at = datetime.strptime(
                            article_data['published_at'], 
                            '%Y-%m-%d %H:%M'
                        )
                    except ValueError:
                        logger.warning(f"Invalid date format: {article_data['published_at']}")
                
                # Save to Django database with content
                article, created = Article.objects.get_or_create(
                    url=article_data['url'],
                    defaults={
                        'headline': article_data['headline'],
                        'author': article_data['author'],
                        'location': article_data['location'],
                        'published_at': published_at,
                        'content': article_data.get('content', ''),  # Include content
                        'word_count': article_data['word_count'],
                        'category': category,
                        'elasticsearch_indexed': False
                    }
                )
                
                if created:
                    articles_saved += 1
                    articles_for_es.append(article_data)  # Add to ES indexing list
                    logger.info(f"Saved new article: {article_data['headline'][:50]}...")
                else:
                    logger.info(f"Article already exists: {article_data['headline'][:50]}...")
                
            except Exception as e:
                logger.error(f"Failed to save article {article_data['url']}: {e}")
        
        # Bulk index to Elasticsearch
        articles_indexed = 0
        if articles_for_es:
            logger.info(f"Attempting to index {len(articles_for_es)} new articles to Elasticsearch...")
            articles_indexed = es_client.bulk_index_articles(articles_for_es)
            
            if articles_indexed > 0:
                # Update Django records to mark as indexed
                Article.objects.filter(
                    url__in=[a['url'] for a in articles_for_es]
                ).update(elasticsearch_indexed=True)
                logger.info(f"Marked {articles_indexed} articles as indexed in Django")
            else:
                logger.error("Failed to index any articles to Elasticsearch")
        
        # Update final task status
        task_record.articles_indexed = articles_indexed
        task_record.status = 'SUCCESS'
        task_record.completed_at = timezone.now()
        task_record.save()
        
        # Get index stats for verification
        index_stats = es_client.get_index_stats()
        logger.info(f"Elasticsearch index stats: {index_stats}")
        
        result = {
            'success': True,
            'task_id': task_id,
            'category': category,
            'total_articles_found': scraping_results['total_articles_found'],
            'articles_scraped': scraping_results['articles_scraped'],
            'articles_saved_to_db': articles_saved,
            'articles_indexed_to_es': articles_indexed,
            'elasticsearch_stats': index_stats,
            'message': f'Successfully scraped {articles_saved} new articles for category "{category}"'
        }
        
        logger.info(f"Task {task_id} completed successfully: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Task {task_id} failed with error: {e}")
        
        # Update task status to failure
        task_record.status = 'FAILURE'
        task_record.error_message = str(e)
        task_record.completed_at = timezone.now()
        task_record.save()
        
        return {
            'success': False,
            'error': str(e),
            'task_id': task_id
        }


@shared_task
def cleanup_old_tasks():
    """
    Periodic task to clean up old completed tasks
    """
    from django.utils import timezone
    from datetime import timedelta
    
    # Delete tasks older than 30 days
    cutoff_date = timezone.now() - timedelta(days=30)
    deleted_count = ScrapingTask.objects.filter(
        completed_at__lt=cutoff_date
    ).delete()[0]
    
    logger.info(f"Cleaned up {deleted_count} old tasks")
    return f"Cleaned up {deleted_count} old tasks"
