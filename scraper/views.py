# scraper/views.py
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
import uuid
from .models import ScrapingTask
from .serializers import (
    ScrapingTaskSerializer, 
    StartScrapingSerializer, 
    ArticleSearchSerializer,
    ArticleSerializer
)
from .tasks import scrape_category_task
from .es_client import es_client

class CustomPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'size'
    max_page_size = 100

@api_view(['POST'])
def start_scraping(request):
    """Start scraping task for a category"""
    serializer = StartScrapingSerializer(data=request.data)
    if serializer.is_valid():
        category = serializer.validated_data['category']
        max_pages = serializer.validated_data['max_pages']
        
        # Create task record
        task_id = str(uuid.uuid4())
        task = ScrapingTask.objects.create(
            task_id=task_id,
            category=category,
            max_pages=max_pages
        )
        
        # Start celery task
        scrape_category_task.delay(task_id, category, max_pages)
        
        return Response({
            'task_id': task_id,
            'category': category,
            'max_pages': max_pages,
            'status': 'PENDING',
            'message': 'Scraping task started successfully'
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def task_status(request, task_id):
    """Get status of a scraping task"""
    task = get_object_or_404(ScrapingTask, task_id=task_id)
    serializer = ScrapingTaskSerializer(task)
    return Response(serializer.data)

@api_view(['GET'])
def list_tasks(request):
    """List all scraping tasks"""
    tasks = ScrapingTask.objects.all()
    serializer = ScrapingTaskSerializer(tasks, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def search_articles(request):
    """Search articles with Elasticsearch"""
    serializer = ArticleSearchSerializer(data=request.GET)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    category = data['category']
    query = data.get('query', '')
    page = data.get('page', 1)
    size = data.get('size', 20)
    
    # Build filters
    filters = {}
    if data.get('author'):
        filters['author'] = data['author']
    if data.get('location'):
        filters['location'] = data['location']
    if data.get('date_from'):
        filters['date_from'] = data['date_from'].strftime('%Y-%m-%d')
    if data.get('date_to'):
        filters['date_to'] = data['date_to'].strftime('%Y-%m-%d')
    
    # Search with Elasticsearch
    result = es_client.search_articles(
        category=category,
        query=query if query else None,
        page=page,
        size=size,
        filters=filters if filters else None
    )
    
    # Format response
    articles = []
    for hit in result['hits']['hits']:
        source = hit['_source']
        articles.append(source)
    
    total = result['hits']['total']['value']
    
    return Response({
        'count': total,
        'page': page,
        'size': size,
        'total_pages': (total + size - 1) // size,
        'results': articles
    })

@api_view(['GET'])
def category_stats(request, category):
    """Get statistics for a category"""
    # Validate category
    valid_categories = [choice[0] for choice in ScrapingTask.CATEGORY_CHOICES]
    if category not in valid_categories:
        return Response(
            {'error': 'Invalid category'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    stats = es_client.get_article_stats(category)
    
    # Get recent tasks for this category
    recent_tasks = ScrapingTask.objects.filter(category=category)[:5]
    task_serializer = ScrapingTaskSerializer(recent_tasks, many=True)
    
    return Response({
        'category': category,
        'total_articles': stats['total_articles'],
        'recent_tasks': task_serializer.data
    })

@api_view(['GET'])
def available_categories(request):
    """List all available categories"""
    categories = [
        {'value': choice[0], 'label': choice[1]} 
        for choice in ScrapingTask.CATEGORY_CHOICES
    ]
    return Response({'categories': categories})