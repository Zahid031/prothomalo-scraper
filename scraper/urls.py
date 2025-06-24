
from django.urls import path
from . import views

urlpatterns = [
    # Scraping endpoints
    path('scrape/start/', views.start_scraping, name='start_scraping'),
    
    # Task management endpoints
    path('tasks/', views.TaskListView.as_view(), name='task_list'),
    path('tasks/<str:task_id>/status/', views.task_status, name='task_status'),
    
    # Article endpoints
    path('articles/', views.ArticleListView.as_view(), name='article_list'),
    path('articles/search/', views.search_articles, name='search_articles'),
    
    # Statistics endpoint
    path('stats/', views.scraper_stats, name='scraper_stats'),
]
