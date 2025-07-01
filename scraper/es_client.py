
from elasticsearch import Elasticsearch
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class ElasticsearchClient:
    INDEX_NAME = "prothomalo_articles"

    def __init__(self):
        self.client = None
        self.connect()

    def connect(self):
        try:
            self.client = Elasticsearch(
                hosts=[settings.ELASTICSEARCH_HOST],
                basic_auth=(settings.ELASTICSEARCH_USER, settings.ELASTICSEARCH_PASSWORD),
                verify_certs=False
            )
            if self.client.ping():
                logger.info("Connected to Elasticsearch")
            else:
                logger.error("Failed to ping Elasticsearch")
        except Exception as e:
            logger.error(f"Elasticsearch connection error: {e}")

    def create_index_if_not_exists(self):
        if self.client.indices.exists(index=self.INDEX_NAME):
            return True

        mapping = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 1,
                "analysis": {
                    "analyzer": {
                        "bengali_analyzer": {
                            "type": "standard",
                            "stopwords": "_none_"
                        }
                    }
                }
            },
            "mappings": {
                "properties": {
                    "url": {"type": "keyword"},
                    "headline": {
                        "type": "text", 
                        "analyzer": "bengali_analyzer",
                        "fields": {"raw": {"type": "keyword"}}
                    },
                    "author": {"type": "text"},
                    "location": {"type": "keyword"},
                    "published_at": {"type": "date", "format": "yyyy-MM-dd HH:mm"},
                    "content": {"type": "text", "analyzer": "bengali_analyzer"},
                    "scraped_at": {"type": "date"},
                    "word_count": {"type": "integer"},
                    "category": {"type": "keyword"}
                }
            }
        }

        try:
            self.client.indices.create(index=self.INDEX_NAME, body=mapping)
            return True
        except Exception as e:
            logger.error(f"Failed to create index {self.INDEX_NAME}: {e}")
            return False

    def search_articles(self, query=None, page=1, size=20, filters=None):
        if not self.client.indices.exists(index=self.INDEX_NAME):
            return {"hits": {"hits": [], "total": {"value": 0}}}

        body = {
            "query": {"bool": {"must": [], "filter": []}},
            "sort": [{"published_at": {"order": "desc"}}],
            "from": (page - 1) * size,
            "size": size
        }

        if query:
            body["query"]["bool"]["must"].append({
                "multi_match": {
                    "query": query,
                    "fields": ["headline^2", "content", "author"]
                }
            })
        else:
            body["query"]["bool"]["must"].append({"match_all": {}})

        if filters:
            if filters.get('author'):
                body["query"]["bool"]["filter"].append({"match": {"author": filters['author']}})
            if filters.get('location'):
                body["query"]["bool"]["filter"].append({"term": {"location": filters['location']}})
            if filters.get('category'):
                body["query"]["bool"]["filter"].append({"term": {"category": filters['category']}})
            if filters.get('date_from'):
                body["query"]["bool"]["filter"].append({"range": {"published_at": {"gte": filters['date_from']}}})
            if filters.get('date_to'):
                body["query"]["bool"]["filter"].append({"range": {"published_at": {"lte": filters['date_to']}}})

        try:
            result = self.client.search(index=self.INDEX_NAME, body=body)
            return result
        except Exception as e:
            logger.error(f"Search error: {e}")
            return {"hits": {"hits": [], "total": {"value": 0}}}

    def get_article_stats(self, category=None):
        if not self.client.indices.exists(index=self.INDEX_NAME):
            return {"total_articles": 0}

        body = {"query": {"match_all": {}}}
        if category:
            body = {"query": {"term": {"category": category}}}

        try:
            result = self.client.count(index=self.INDEX_NAME, body=body)
            return {"total_articles": result["count"]}
        except Exception as e:
            logger.error(f"Stats error: {e}")
            return {"total_articles": 0}

# Global instance
es_client = ElasticsearchClient()
