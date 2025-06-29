# scraper/models.py
from django.db import models
from django.utils import timezone

class ScrapingTask(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('RUNNING', 'Running'),
        ('SUCCESS', 'Success'),
        ('FAILURE', 'Failure'),
    ]
    
    CATEGORY_CHOICES = [
        ('politics', 'Politics'),
        ('world-all', 'World'),
        ('opinion-all', 'Opinion'),
        ('crime-bangladesh', 'Crime Bangladesh'),
        ('business-all', 'Business'),
        ('sports-all', 'Sports'),
        ('entertainment-all', 'Entertainment'),
        ('chakri-all', 'Jobs'),
        ('lifestyle-all', 'Lifestyle'),
    ]
    
    task_id = models.CharField(max_length=255, unique=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    max_pages = models.IntegerField(default=2)
    total_articles = models.IntegerField(default=0)
    scraped_articles = models.IntegerField(default=0)
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.category} - {self.status}"