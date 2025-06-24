
from django.contrib import admin
from .models import ScrapingTask, Article


@admin.register(ScrapingTask)
class ScrapingTaskAdmin(admin.ModelAdmin):
    list_display = [
        'task_id', 'category', 'status', 'created_at', 
        'articles_scraped', 'articles_indexed'
    ]
    list_filter = ['status', 'category', 'created_at']
    search_fields = ['task_id', 'category']
    readonly_fields = [
        'task_id', 'created_at', 'started_at', 'completed_at'
    ]
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ['category', 'max_pages']
        return self.readonly_fields


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = [
        'headline', 'author', 'category', 'published_at', 
        'word_count', 'elasticsearch_indexed'
    ]
    list_filter = ['category', 'elasticsearch_indexed', 'scraped_at']
    search_fields = ['headline', 'author', 'url']
    readonly_fields = ['url', 'scraped_at']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related()
