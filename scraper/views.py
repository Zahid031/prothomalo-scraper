from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
import uuid
import logging
import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from .models import ScrapingTask
from .serializers import (
    ScrapingTaskSerializer, 
    StartScrapingSerializer, 
    ArticleSearchSerializer,
    ArticleSerializer,
    S3DownloadSerializer
)
from .tasks import scrape_category_task
from .es_client import es_client

logger = logging.getLogger(__name__)

class CustomPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'size'
    max_page_size = 100

@api_view(['POST'])
def start_scraping(request):
    serializer = StartScrapingSerializer(data=request.data)
    if serializer.is_valid():
        category = serializer.validated_data['category']
        max_pages = serializer.validated_data['max_pages']

        task_id = str(uuid.uuid4())
        task = ScrapingTask.objects.create(
            task_id=task_id,
            category=category,
            max_pages=max_pages
        )

        logger.info(f"Starting scraping task: {task_id} for category: {category}")
        scrape_category_task.delay(task_id, category, max_pages)

        return Response({
            'task_id': task_id,
            'category': category,
            'max_pages': max_pages,
            'status': 'PENDING',
            'message': 'Scraping task started successfully'
        }, status=status.HTTP_201_CREATED)

    logger.warning(f"Invalid scraping request: {serializer.errors}")
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def task_status(request, task_id):
    task = get_object_or_404(ScrapingTask, task_id=task_id)
    serializer = ScrapingTaskSerializer(task)
    return Response(serializer.data)

@api_view(['GET'])
def list_tasks(request):
    tasks = ScrapingTask.objects.all()
    serializer = ScrapingTaskSerializer(tasks, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def search_articles(request):
    serializer = ArticleSearchSerializer(data=request.GET)
    if not serializer.is_valid():
        logger.warning(f"Invalid search query: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    query = data.get('query', '')
    page = data.get('page', 1)
    size = data.get('size', 20)

    filters = {}
    if data.get('author'):
        filters['author'] = data['author']
    if data.get('location'):
        filters['location'] = data['location']
    if data.get('category'):
        filters['category'] = data['category']
    if data.get('date_from'):
        filters['date_from'] = data['date_from'].strftime('%Y-%m-%d')
    if data.get('date_to'):
        filters['date_to'] = data['date_to'].strftime('%Y-%m-%d')

    logger.info(f"Searching articles with filters: {filters} and query: {query}")
    result = es_client.search_articles(
        query=query if query else None,
        page=page,
        size=size,
        filters=filters if filters else None
    )

    articles = [hit['_source'] for hit in result['hits']['hits']]
    total = result['hits']['total']['value']

    logger.info(f"Search result count: {total} articles")
    return Response({
        'count': total,
        'page': page,
        'size': size,
        'total_pages': (total + size - 1) // size,
        'results': articles
    })

@api_view(['GET'])
def list_all_articles(request):
    """Return all articles with pagination"""
    page = int(request.GET.get('page', 1))
    size = int(request.GET.get('size', 20))

    logger.info("Fetching all articles from Elasticsearch")
    result = es_client.search_articles(query=None, page=page, size=size)

    articles = [hit['_source'] for hit in result['hits']['hits']]
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
    valid_categories = [choice[0] for choice in ScrapingTask.CATEGORY_CHOICES]
    if category not in valid_categories:
        logger.warning(f"Invalid category stats request: {category}")
        return Response(
            {'error': 'Invalid category'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

    stats = es_client.get_article_stats(category)
    recent_tasks = ScrapingTask.objects.filter(category=category)[:5]
    task_serializer = ScrapingTaskSerializer(recent_tasks, many=True)

    logger.info(f"Stats for category '{category}': {stats['total_articles']} articles")
    return Response({
        'category': category,
        'total_articles': stats['total_articles'],
        'recent_tasks': task_serializer.data
    })

@api_view(['GET'])
def available_categories(request):
    categories = [
        {'value': choice[0], 'label': choice[1]} 
        for choice in ScrapingTask.CATEGORY_CHOICES
    ]
    logger.debug("Returning available categories list")
    return Response({'categories': categories})

@api_view(['GET'])
def download_s3_data(request, task_id):
    """Generate a pre-signed URL for downloading S3 data"""
    task = get_object_or_404(ScrapingTask, task_id=task_id)
    
    if not task.s3_key:
        return Response(
            {'error': 'No S3 backup available for this task'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        # Create S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1')
        )
        
        # Generate pre-signed URL (valid for 1 hour)
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                'Key': task.s3_key
            },
            ExpiresIn=3600  # 1 hour
        )
        
        logger.info(f"Generated pre-signed URL for task {task_id}")
        return Response({
            'download_url': presigned_url,
            'expires_in': 3600,
            'filename': f'{task_id}.zip',
            'task_info': {
                'task_id': task.task_id,
                'category': task.category,
                'scraped_articles': task.scraped_articles,
                'created_at': task.created_at,
                's3_uploaded_at': task.s3_uploaded_at
            }
        })
        
    except ClientError as e:
        logger.error(f"Failed to generate pre-signed URL: {e}")
        return Response(
            {'error': 'Failed to generate download URL'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def s3_backup_status(request):
    """Get status of S3 backups for all tasks"""
    tasks_with_s3 = ScrapingTask.objects.filter(s3_url__isnull=False).order_by('-created_at')
    tasks_without_s3 = ScrapingTask.objects.filter(
        status='SUCCESS', 
        s3_url__isnull=True
    ).order_by('-created_at')
    
    return Response({
        'total_tasks': ScrapingTask.objects.count(),
        'tasks_with_s3_backup': tasks_with_s3.count(),
        'tasks_without_s3_backup': tasks_without_s3.count(),
        'recent_s3_backups': ScrapingTaskSerializer(tasks_with_s3[:10], many=True).data,
        'failed_s3_backups': ScrapingTaskSerializer(tasks_without_s3[:10], many=True).data
    })