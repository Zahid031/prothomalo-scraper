# Prothomalo Newspaper Scraper & API

This project is a Django-based web scraper and RESTful API for fetching and searching news articles from the Prothomalo newspaper website. It uses Celery for asynchronous task management, Elasticsearch for storing and searching articles, and provides an S3 backup solution for the scraped data.

## Features

*   **Web Scraper:** Scrapes news articles from different categories of the Prothomalo website.
*   **RESTful API:** Provides endpoints to start scraping tasks, check task status, and search for articles.
*   **Asynchronous Task Processing:** Uses Celery with Redis to handle long-running scraping tasks in the background.
*   **Full-Text Search:** Integrates with Elasticsearch to provide powerful full-text search capabilities for the scraped articles.
*   **Data Backup:** Backs up scraped data to an AWS S3 bucket as a zip file.
*   **Scalable Architecture:** Designed to be scalable for handling a large volume of articles and scraping tasks.

## Technologies Used

*   **Backend:** Django, Django REST Framework
*   **Web Scraping:** `requests`, `BeautifulSoup4`
*   **Asynchronous Tasks:** `Celery`, `Redis`
*   **Database:** `SQLite` (for task management), `Elasticsearch` (for article storage and search)
*   **API Documentation:** `drf-spectacular` for generating OpenAPI 3 schema.
*   **Deployment:** `python-dotenv` for managing environment variables.

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd prothomalo-api
    ```

2.  **Create a virtual environment and activate it:**
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    Create a `.env` file in the project root and add the following variables:
    ```
    REDIS_URL=redis://localhost:6379/0
    ELASTICSEARCH_HOST=http://localhost:9200
    ELASTICSEARCH_USER=elastic
    ELASTICSEARCH_PASSWORD=<your-password>
    AWS_ACCESS_KEY_ID=<your-aws-access-key-id>
    AWS_SECRET_ACCESS_KEY=<your-aws-secret-access-key>
    AWS_STORAGE_BUCKET_NAME=<your-s3-bucket-name>
    AWS_S3_REGION_NAME=<your-s3-bucket-region>
    ```

5.  **Run database migrations:**
    ```bash
    python manage.py migrate
    ```

## API Documentation

The API documentation is automatically generated using `drf-spectacular`. Once the server is running, you can access the documentation at the following endpoints:

*   **Swagger UI:** `http://127.0.0.1:8000/api/docs/`
*   **ReDoc:** `http://127.0.0.1:8000/api/redoc/`
*   **Schema:** `http://127.0.0.1:8000/api/schema/`

### API Endpoints

*   `POST /api/start/`: Start a new scraping task.
*   `GET /api/tasks/`: Get a list of all scraping tasks.
*   `GET /api/tasks/<task_id>/`: Get the status of a specific task.
*   `GET /api/articles/`: Get a paginated list of all articles.
*   `GET /api/articles/search/`: Search for articles with various filters.
*   `GET /api/categories/`: Get a list of available categories to scrape.
*   `GET /api/categories/<category>/stats/`: Get statistics for a specific category.
*   `GET /api/tasks/<task_id>/download/`: Get a pre-signed URL to download the S3 backup for a task.
*   `GET /api/s3/status/`: Get the status of S3 backups.

## Running the Application

1.  **Start the Django development server:**
    ```bash
    python manage.py runserver
    ```

2.  **Start the Celery worker:**
    ```bash
    celery -A prothomalo_api.celery_app worker -l info
    ```

3.  **Start the Celery beat scheduler (optional):**
    ```bash
    celery -A prothomalo_api.celery_app beat -l info
    ```

Now you can access the API at `http://127.0.0.1:8000/api/`.

## Future Improvements

*   **Add a frontend:** A simple frontend could be added to provide a user-friendly interface for interacting with the scraper.
*   **Add tests:** Unit and integration tests should be added to improve code quality and maintainability.
*   **Containerization:** The application could be containerized using Docker for easier deployment.
*   **CI/CD:** A CI/CD pipeline could be set up to automate testing and deployment.
