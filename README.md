
# Prothom Alo News Scraper Backend

A robust Django REST Framework backend for scraping news articles from Prothom Alo with Celery task queue, Redis, and Elasticsearch integration.

## Features

- **REST API**: Complete API for managing scraping tasks and accessing data
- **Async Processing**: Celery task queue for non-blocking scraping operations
- **Search Engine**: Elasticsearch integration for full-text search
- **Task Monitoring**: Real-time task status tracking
- **Multi-Category Support**: Scrape different news categories
- **Data Storage**: Dual storage in Django database and Elasticsearch
- **Admin Interface**: Django admin for data management

## Quick Start

### Prerequisites

- Python 3.8+
- Docker and Docker Compose (for Redis and Elasticsearch)

### Installation

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Start Services**
```bash
# Start Redis and Elasticsearch
docker-compose up -d

# Wait for services to be ready (about 30 seconds)
```

3. **Django Setup**
```bash
# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Start Django development server
python manage.py runserver
```

4. **Start Celery Worker**
```bash
# In a new terminal
celery -A prothomalo_scraper worker --loglevel=info
```

## API Endpoints

### Start Scraping
```http
POST /api/scrape/start/
Content-Type: application/json

{
    "category": "politics",
    "max_pages": 2
}
```

**Supported Categories**: politics, bangladesh, world, sports, entertainment, business, science-technology, lifestyle, opinion

### Monitor Task Status
```http
GET /api/tasks/{task_id}/status/
```

### List All Tasks
```http
GET /api/tasks/
GET /api/tasks/?category=politics&status=SUCCESS
```

### List Articles
```http
GET /api/articles/
GET /api/articles/?category=politics
```

### Search Articles (Elasticsearch)
```http
GET /api/articles/search/?q=আওয়ামী&category=politics&page=1&size=20
```

### Get Statistics
```http
GET /api/stats/
```

## Usage Examples

### 1. Start a Scraping Task
```bash
curl -X POST http://localhost:8000/api/scrape/start/ \
  -H "Content-Type: application/json" \
  -d '{"category": "politics", "max_pages": 3}'
```

Response:
```json
{
    "success": true,
    "task_id": "abc123-def456-ghi789",
    "category": "politics",
    "max_pages": 3,
    "status": "PENDING",
    "message": "Scraping task started for category \"politics\""
}
```

### 2. Check Task Status
```bash
curl http://localhost:8000/api/tasks/abc123-def456-ghi789/status/
```

Response:
```json
{
    "task_id": "abc123-def456-ghi789",
    "category": "politics",
    "status": "SUCCESS",
    "total_articles_found": 36,
    "articles_scraped": 34,
    "articles_indexed": 34,
    "created_at": "2025-01-20T10:00:00Z",
    "completed_at": "2025-01-20T10:05:30Z"
}
```

### 3. Search Articles
```bash
curl "http://localhost:8000/api/articles/search/?q=নির্বাচন&category=politics"
```

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Django API    │    │  Celery Worker  │    │ Elasticsearch   │
│                 │    │                 │    │                 │
│ • REST endpoints│    │ • Scraping tasks│    │ • Article search│
│ • Task tracking │    │ • Data processing│   │ • Full-text idx │
│ • Admin interface│   │ • Error handling│    │ • Analytics     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │     Redis       │
                    │                 │
                    │ • Task queue    │
                    │ • Result store  │
                    │ • Caching       │
                    └─────────────────┘
```

## Development

### Running Tests
```bash
python manage.py test
```

### Monitoring Celery
```bash
# Monitor Celery tasks
celery -A prothomalo_scraper flower
# Access at http://localhost:5555
```

### Django Admin
Access the admin interface at `http://localhost:8000/admin/` to:
- View and manage scraping tasks
- Browse scraped articles
- Monitor system status

## Configuration

Key settings in `settings.py`:
- `CELERY_BROKER_URL`: Redis connection for Celery
- `ELASTICSEARCH_DSL`: Elasticsearch connection settings
- `LOGGING`: Configure logging levels and outputs

## Troubleshooting

1. **Elasticsearch Connection Issues**
   - Ensure Elasticsearch is running: `curl localhost:9200`
   - Check credentials in settings

2. **Celery Worker Not Processing Tasks**
   - Verify Redis is running: `redis-cli ping`
   - Check Celery worker logs

3. **Scraping Failures**
   - Check network connectivity
   - Verify Prothom Alo site structure hasn't changed
   - Review scraper logs

## Production Deployment

For production deployment:
1. Use environment variables for sensitive settings
2. Configure proper logging
3. Set up monitoring and alerting
4. Use production-grade message broker
5. Implement proper error handling and retries
