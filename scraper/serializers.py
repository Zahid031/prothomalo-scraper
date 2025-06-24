
from rest_framework import serializers
from .models import ScrapingTask, Article


class ScrapingTaskSerializer(serializers.ModelSerializer):
    """Serializer for scraping task data"""
    
    class Meta:
        model = ScrapingTask
        fields = [
            'task_id', 'category', 'max_pages', 'status',
            'created_at', 'started_at', 'completed_at',
            'total_articles_found', 'articles_scraped', 'articles_indexed',
            'error_message'
        ]
        read_only_fields = [
            'task_id', 'status', 'created_at', 'started_at', 'completed_at',
            'total_articles_found', 'articles_scraped', 'articles_indexed',
            'error_message'
        ]


class ArticleSerializer(serializers.ModelSerializer):
    """Serializer for article data"""
    
    class Meta:
        model = Article
        fields = [
            'id', 'url', 'headline', 'author', 'location',
            'published_at', 'scraped_at', 'word_count', 'category',
            'elasticsearch_indexed'
        ]


class StartScrapingSerializer(serializers.Serializer):
    """Serializer for starting a scraping task"""
    category = serializers.CharField(max_length=100)
    max_pages = serializers.IntegerField(min_value=1, max_value=10, default=2)
    
    def validate_category(self, value):
        """Validate that category is supported"""
        allowed_categories = [
            'politics', 'bangladesh', 'world', 'sports', 'entertainment',
            'business', 'science-technology', 'lifestyle', 'opinion'
        ]
        
        if value not in allowed_categories:
            raise serializers.ValidationError(
                f"Category must be one of: {', '.join(allowed_categories)}"
            )
        return value
