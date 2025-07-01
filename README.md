# Prothomalo Newspaper Scraper & API (Beautifulsoup4+Requests+Elasticsearch+AWS S3+React)

This project is a full-stack application featuring a Django-based web scraper and RESTful API, complemented by a React frontend. It fetches and searches news articles from the Prothomalo newspaper website, using Celery for asynchronous task management, Elasticsearch for article storage and search, and provides an S3 backup solution for scraped data.

## Features

*   **React Frontend:** A user-friendly interface to interact with the scraper, view tasks, and search articles.
*   **Web Scraper:** Scrapes news articles from different categories of the Prothomalo website.
*   **RESTful API:** Provides endpoints to start scraping tasks, check task status, and search for articles.
*   **Asynchronous Task Processing:** Uses Celery with Redis to handle long-running scraping tasks in the background.
*   **Full-Text Search:** Integrates with Elasticsearch to provide powerful full-text search capabilities for the scraped articles.
*   **Data Backup:** Backs up scraped data to an AWS S3 bucket as a zip file.
*   **Scalable Architecture:** Designed to be scalable for handling a large volume of articles and scraping tasks.

## Technologies Used

*   **Backend:** Django, Django REST Framework
*   **Frontend:** React, Vite
*   **Web Scraping:** `requests`, `BeautifulSoup4`
*   **Asynchronous Tasks:** `Celery`, `Redis`
*   **Database:** `SQLite` (for task management), `Elasticsearch` (for article storage and search)
*   **API Documentation:** `drf-spectacular` for generating OpenAPI 3 schema.
*   **Deployment:** `Docker`, `docker-compose`, `python-dotenv` for managing environment variables.

## Setup and Installation

### Prerequisites

*   **Docker:** Ensure you have Docker installed and running on your system. You can download it from [https://www.docker.com/get-started](https://www.docker.com/get-started).

### Running the Application with Docker

1.  **Clone the repository:**
    ```bash
    git clone git@github.com:Zahid031/prothomalo-scraper.git
    cd prothomalo-api
    ```

2.  **Set up environment variables:**
    Create a `.env` file in the project root and add the following variables:
    ```
    REDIS_URL=redis://redis:6379/0
    ELASTICSEARCH_HOST=http://elasticsearch:9200
    ELASTICSEARCH_USER=elastic
    ELASTICSEARCH_PASSWORD=<your-password>
    AWS_ACCESS_KEY_ID=<your-aws-access-key-id>
    AWS_SECRET_ACCESS_KEY=<your-aws-secret-access-key>
    AWS_STORAGE_BUCKET_NAME=<your-s3-bucket-name>
    AWS_S3_REGION_NAME=<your-s3-bucket-region>
    ```

3.  **Build and run the application using Docker Compose:**
    ```bash
    docker compose up --build
    ```

    This command will build the Docker images for the frontend and backend services and start the containers.

    *   The **React frontend** will be available at `http://localhost:5173`.
    *   The **Django backend** will be available at `http://localhost:8000`.

## API Documentation

The API documentation is automatically generated using `drf-spectacular`. Once the server is running, you can access the documentation at the following endpoints:

*   **Swagger UI:** `http://localhost:8000/api/docs/`
*   **ReDoc:** `http://localhost:8000/api/redoc/`
*   **Schema:** `http://localhost:8000/api/schema/`

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

## Future Improvements

*   **Add tests:** Unit and integration tests should be added to improve code quality and maintainability.
*   **CI/CD:** A CI/CD pipeline could be set up to automate testing and deployment.
*   **Improve Frontend:** Enhance the user interface and add more features to the frontend.




