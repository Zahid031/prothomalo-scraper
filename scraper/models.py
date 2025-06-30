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

    s3_url = models.URLField(blank=True, null=True, help_text="S3 URL where the zip file is stored")
    s3_key = models.CharField(max_length=500, blank=True, null=True, help_text="S3 key/path for the zip file")
    s3_uploaded_at = models.DateTimeField(blank=True, null=True, auto_now_add=False)

    def save(self, *args, **kwargs):
        # Update s3_uploaded_at when s3_url is first set
        if self.s3_url and not self.s3_uploaded_at:
            self.s3_uploaded_at = timezone.now()
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.category} - {self.status}"