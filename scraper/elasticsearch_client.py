
from elasticsearch import Elasticsearch
from django.conf import settings
import logging

logger = logging.getLogger('scraper')


class ElasticsearchClient:
    """Elasticsearch client wrapper for article operations"""
    
    def __init__(self):
        self.client = None
        self.index_name = 'prothomalo_articles'
        self.connect()
    
    def connect(self):
        """Establish connection to Elasticsearch"""
        try:
            es_config = settings.ELASTICSEARCH_DSL['default']
            self.client = Elasticsearch(
                hosts=[es_config['hosts']],
                basic_auth=es_config['basic_auth'],
                verify_certs=es_config['verify_certs']
            )
            
            if self.client.ping():
                logger.info("Successfully connected to Elasticsearch")
                self.create_index_if_not_exists()
            else:
                logger.error("Elasticsearch ping failed")
                
        except Exception as e:
            logger.error(f"Failed to connect to Elasticsearch: {e}")
            self.client = None
    
    def create_index_if_not_exists(self):
        """Create the articles index with proper mapping"""
        try:
            if self.client.indices.exists(index=self.index_name):
                logger.info(f"Index '{self.index_name}' already exists")
                return
            
            index_mapping = {
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
                            "fields": {
                                "raw": {"type": "keyword"}
                            }
                        },
                        "author": {"type": "text"},
                        "location": {"type": "keyword"},
                        "published_at": {"type": "date", "format": "yyyy-MM-dd HH:mm"},
                        "content": {
                            "type": "text",
                            "analyzer": "bengali_analyzer"
                        },
                        "scraped_at": {"type": "date"},
                        "word_count": {"type": "integer"},
                        "category": {"type": "keyword"}
                    }
                }
            }
            
            self.client.indices.create(index=self.index_name, body=index_mapping)
            logger.info(f"Created index '{self.index_name}'")
            
        except Exception as e:
            logger.error(f"Failed to create index: {e}")
    
    def bulk_index_articles(self, articles):
        """Bulk index articles to Elasticsearch"""
        if not self.client or not articles:
            return False
        
        try:
            from elasticsearch.helpers import bulk
            from urllib.parse import quote
            
            actions = []
            for article in articles:
                doc_id = quote(article['url'], safe='')
                action = {
                    "_index": self.index_name,
                    "_id": doc_id,
                    "_source": article
                }
                actions.append(action)
            
            success, failed = bulk(
                self.client,
                actions,
                chunk_size=100,
                request_timeout=60,
                raise_on_error=False
            )
            
            logger.info(f"Successfully indexed {success} articles to Elasticsearch")
            if failed:
                logger.warning(f"Failed to index {len(failed)} articles")
            
            return success
            
        except Exception as e:
            logger.error(f"Bulk indexing failed: {e}")
            return False
    
    def search_articles(self, query=None, category=None, size=20, from_=0):
        """Search articles in Elasticsearch"""
        if not self.client:
            return {"hits": {"total": {"value": 0}, "hits": []}}
        
        try:
            search_body = {
                "query": {
                    "bool": {
                        "must": []
                    }
                },
                "sort": [
                    {"published_at": {"order": "desc", "missing": "_last"}},
                    {"scraped_at": {"order": "desc"}}
                ],
                "size": size,
                "from": from_
            }
            
            if query:
                search_body["query"]["bool"]["must"].append({
                    "multi_match": {
                        "query": query,
                        "fields": ["headline^2", "content", "author"]
                    }
                })
            
            if category:
                search_body["query"]["bool"]["must"].append({
                    "term": {"category": category}
                })
            
            if not search_body["query"]["bool"]["must"]:
                search_body["query"] = {"match_all": {}}
            
            response = self.client.search(index=self.index_name, body=search_body)
            return response
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {"hits": {"total": {"value": 0}, "hits": []}}


# Global instance
es_client = ElasticsearchClient()
