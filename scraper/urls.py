# scraper/urls.py
from django.urls import path
from . import views
from scraper.views import list_all_articles


urlpatterns = [
    path('scrape/', views.start_scraping, name='start_scraping'),
    path('task/<str:task_id>/', views.task_status, name='task_status'),
    path('tasks/', views.list_tasks, name='list_tasks'),
    path('articles/', views.search_articles, name='search_articles'),
    path('stats/<str:category>/', views.category_stats, name='category_stats'),
    path('categories/', views.available_categories, name='available_categories'),
    path('api/articles/', list_all_articles, name='list-all-articles'),

]

