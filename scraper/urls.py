from django.urls import path
from . import views

urlpatterns = [
    path('start/', views.start_scraping, name='start_scraping'),
    path('tasks/', views.list_tasks, name='list_tasks'),
    path('tasks/<str:task_id>/', views.task_status, name='task_status'),
    
    path('articles/', views.list_all_articles, name='list_all_articles'),
    path('articles/search/', views.search_articles, name='search_articles'),
    
    path('categories/', views.available_categories, name='available_categories'),
    path('categories/<str:category>/stats/', views.category_stats, name='category_stats'),
    
    path('tasks/<str:task_id>/download/', views.download_s3_data, name='download_s3_data'),
    path('s3/status/', views.s3_backup_status, name='s3_backup_status'),
]