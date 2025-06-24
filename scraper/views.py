
from rest_framework import status, generics
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from celery.result import AsyncResult
from django.shortcuts import get_object_or_404

from .models import ScrapingTask, Article
from .serializers import (
    ScrapingTaskSerializer, 
    ArticleSerializer, 
    StartScrapingSerializer
)
from .tasks import scrape_prothomalo_articles
from .elasticsearch_client import es_client

import logging

logger = logging.getLogger('scraper')


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['POST'])
def start_scraping(request):
    """
    Start a new scraping task
    
    POST /api/scrape/start/
    {
        "category": "politics",
        "max_pages": 2
    }
    """
    serializer = StartScrapingSerializer(data=request.data)
    
    if serializer.is_valid():
        category = serializer.validated_data['category']
        max_pages = serializer.validated_data['max_pages']
        
        # Start the Celery task
        task = scrape_prothomalo_articles.delay(category, max_pages)
        
        # Create task record
        task_record = ScrapingTask.objects.create(
            task_id=task.id,
            category=category,
            max_pages=max_pages,
            status='PENDING'
        )
        
        logger.info(f"Started scraping task {task.id} for category '{category}'")
        
        return Response({
            'success': True,
            'task_id': task.id,
            'category': category,
            'max_pages': max_pages,
            'status': 'PENDING',
            'message': f'Scraping task started for category "{category}"'
        }, status=status.HTTP_202_ACCEPTED)
    
    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def task_status(request, task_id):
    """
    Get the status of a specific scraping task
    
    GET /api/tasks/{task_id}/status/
    """
    try:
        # Get task from database
        task_record = get_object_or_404(ScrapingTask, task_id=task_id)
        
        # Get Celery task result
        celery_result = AsyncResult(task_id)
        
        # Sync status with Celery if needed
        if celery_result.state != task_record.status:
            task_record.status = celery_result.state
            task_record.save()
        
        serializer = ScrapingTaskSerializer(task_record)
        response_data = serializer.data
        
        # Add additional info from Celery
        if celery_result.state == 'PENDING':
            response_data['message'] = 'Task is waiting to be processed'
        elif celery_result.state == 'PROGRESS':
            response_data['message'] = 'Task is currently running'
        elif celery_result.state == 'SUCCESS':
            response_data['message'] = 'Task completed successfully'
            response_data['result'] = celery_result.result
        elif celery_result.state == 'FAILURE':
            response_data['message'] = 'Task failed'
            response_data['error'] = str(celery_result.info)
        
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"Error getting task status for {task_id}: {e}")
        return Response({
            'error': f'Failed to get task status: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TaskListView(generics.ListAPIView):
    """
    List all scraping tasks with pagination
    
    GET /api/tasks/
    """
    queryset = ScrapingTask.objects.all()
    serializer_class = ScrapingTaskSerializer
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        queryset = ScrapingTask.objects.all()
        
        # Filter by category if provided
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)
        
        # Filter by status if provided
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset


class ArticleListView(generics.ListAPIView):
    """
    List articles from Django database with pagination
    
    GET /api/articles/
    """
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        queryset = Article.objects.all()
        
        # Filter by category if provided
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)
        
        # Filter by elasticsearch indexing status
        es_indexed = self.request.query_params.get('elasticsearch_indexed', None)
        if es_indexed is not None:
            queryset = queryset.filter(elasticsearch_indexed=es_indexed.lower() == 'true')
        
        return queryset


@api_view(['GET'])
def search_articles(request):
    """
    Search articles in Elasticsearch
    
    GET /api/articles/search/?q=query&category=politics&page=1&size=20
    """
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    page = int(request.GET.get('page', 1))
    size = int(request.GET.get('size', 20))
    
    # Calculate from parameter for pagination
    from_ = (page - 1) * size
    
    try:
        # Search in Elasticsearch
        search_results = es_client.search_articles(
            query=query if query else None,
            category=category if category else None,
            size=size,
            from_=from_
        )
        
        # Format response
        hits = search_results['hits']['hits']
        total = search_results['hits']['total']['value']
        
        articles = []
        for hit in hits:
            article = hit['_source']
            article['id'] = hit['_id']
            article['score'] = hit['_score']
            articles.append(article)
        
        # Calculate pagination info
        total_pages = (total + size - 1) // size
        has_next = page < total_pages
        has_previous = page > 1
        
        response_data = {
            'success': True,
            'total': total,
            'page': page,
            'size': size,
            'total_pages': total_pages,
            'has_next': has_next,
            'has_previous': has_previous,
            'articles': articles
        }
        
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return Response({
            'success': False,
            'error': f'Search failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def scraper_stats(request):
    """
    Get overall scraping statistics
    
    GET /api/stats/
    """
    try:
        # Database stats
        total_tasks = ScrapingTask.objects.count()
        successful_tasks = ScrapingTask.objects.filter(status='SUCCESS').count()
        failed_tasks = ScrapingTask.objects.filter(status='FAILURE').count()
        pending_tasks = ScrapingTask.objects.filter(status__in=['PENDING', 'STARTED']).count()
        
        total_articles = Article.objects.count()
        es_indexed_articles = Article.objects.filter(elasticsearch_indexed=True).count()
        
        # Category breakdown
        category_stats = {}
        for task in ScrapingTask.objects.values('category').distinct():
            cat = task['category']
            category_stats[cat] = {
                'total_tasks': ScrapingTask.objects.filter(category=cat).count(),
                'successful_tasks': ScrapingTask.objects.filter(category=cat, status='SUCCESS').count(),
                'total_articles': Article.objects.filter(category=cat).count()
            }
        
        return Response({
            'success': True,
            'stats': {
                'tasks': {
                    'total': total_tasks,
                    'successful': successful_tasks,
                    'failed': failed_tasks,
                    'pending': pending_tasks
                },
                'articles': {
                    'total': total_articles,
                    'elasticsearch_indexed': es_indexed_articles
                },
                'categories': category_stats
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        return Response({
            'success': False,
            'error': f'Failed to get stats: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
