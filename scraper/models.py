
from django.db import models
from django.utils import timezone


class ScrapingTask(models.Model):
    """Model to track scraping tasks"""
    TASK_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('STARTED', 'Started'),
        ('SUCCESS', 'Success'),
        ('FAILURE', 'Failure'),
        ('RETRY', 'Retry'),
        ('REVOKED', 'Revoked'),
    ]
    
    task_id = models.CharField(max_length=255, unique=True, db_index=True)
    category = models.CharField(max_length=100)
    max_pages = models.IntegerField(default=2)
    status = models.CharField(max_length=20, choices=TASK_STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(default=timezone.now)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    total_articles_found = models.IntegerField(default=0)
    articles_scraped = models.IntegerField(default=0)
    articles_indexed = models.IntegerField(default=0)
    error_message = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Task {self.task_id} - {self.category} ({self.status})"


class Article(models.Model):
    """Model to store basic article metadata in Django database"""
    url = models.URLField(unique=True, db_index=True)
    headline = models.TextField()
    author = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    scraped_at = models.DateTimeField(default=timezone.now)
    content = models.TextField(blank=True)  # Added content field
    word_count = models.IntegerField(default=0)
    category = models.CharField(max_length=100, db_index=True)
    elasticsearch_indexed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-published_at', '-scraped_at']
    
    def __str__(self):
        return self.headline[:100]
