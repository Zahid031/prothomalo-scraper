# scraper/serializers.py
from rest_framework import serializers
from .models import ScrapingTask

class ScrapingTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScrapingTask
        fields = '__all__'
        read_only_fields = ['task_id', 'status', 'total_articles', 'scraped_articles', 'error_message', 'created_at', 'updated_at']

class StartScrapingSerializer(serializers.Serializer):
    category = serializers.ChoiceField(choices=ScrapingTask.CATEGORY_CHOICES)
    max_pages = serializers.IntegerField(min_value=1, max_value=10, default=2)

class ArticleSearchSerializer(serializers.Serializer):
    category = serializers.ChoiceField(choices=ScrapingTask.CATEGORY_CHOICES)
    query = serializers.CharField(required=False, allow_blank=True)
    page = serializers.IntegerField(min_value=1, default=1)
    size = serializers.IntegerField(min_value=1, max_value=100, default=20)
    author = serializers.CharField(required=False, allow_blank=True)
    location = serializers.CharField(required=False, allow_blank=True)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)

class ArticleSerializer(serializers.Serializer):
    url = serializers.URLField()
    headline = serializers.CharField()
    author = serializers.CharField()
    location = serializers.CharField()
    published_at = serializers.CharField()
    content = serializers.CharField()
    scraped_at = serializers.CharField()
    word_count = serializers.IntegerField()
    category = serializers.CharField()