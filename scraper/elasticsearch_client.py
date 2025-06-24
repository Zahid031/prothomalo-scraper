
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
            
            # Create client with explicit configuration
            self.client = Elasticsearch(
                [es_config['hosts']],  # Pass as list
                basic_auth=es_config['basic_auth'],
                verify_certs=es_config['verify_certs'],
                request_timeout=30,
                max_retries=3,
                retry_on_timeout=True
            )
            
            # Test connection
            if self.client.ping():
                info = self.client.info()
                logger.info(f"Successfully connected to Elasticsearch: {info['version']['number']}")
                self.create_index_if_not_exists()
                return True
            else:
                logger.error("Elasticsearch ping failed")
                self.client = None
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to Elasticsearch: {e}")
            self.client = None
            return False
    
    def is_connected(self):
        """Check if Elasticsearch is connected and available"""
        try:
            if self.client is None:
                return False
            return self.client.ping()
        except Exception as e:
            logger.error(f"Connection check failed: {e}")
            return False
    
    def create_index_if_not_exists(self):
        """Create the articles index with proper mapping"""
        try:
            if self.client.indices.exists(index=self.index_name):
                logger.info(f"Index '{self.index_name}' already exists")
                return True
            
            index_mapping = {
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,  # Reduced for single node
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
            return True
            
        except Exception as e:
            logger.error(f"Failed to create index: {e}")
            return False
    
    def bulk_index_articles(self, articles):
        """Bulk index articles to Elasticsearch"""
        if not self.is_connected():
            logger.error("Elasticsearch is not connected - attempting to reconnect...")
            if not self.connect():
                logger.error("Failed to reconnect to Elasticsearch")
                return 0
        
        if not articles:
            logger.warning("No articles to index")
            return 0
        
        try:
            from elasticsearch.helpers import bulk
            from urllib.parse import quote
            
            actions = []
            for article in articles:
                # Use URL as document ID to prevent duplicates
                doc_id = quote(article['url'], safe='')
                action = {
                    "_index": self.index_name,
                    "_id": doc_id,
                    "_source": article
                }
                actions.append(action)
            
            logger.info(f"Attempting to bulk index {len(actions)} articles...")
            
            # Use bulk helper with error handling
            success_count = 0
            failed_count = 0
            
            try:
                for success, info in bulk(
                    self.client,
                    actions,
                    chunk_size=50,  # Smaller chunks for reliability
                    request_timeout=60,
                    raise_on_error=False,
                    raise_on_exception=False
                ):
                    if success:
                        success_count += 1
                    else:
                        failed_count += 1
                        logger.error(f"Failed to index document: {info}")
                
                logger.info(f"Successfully indexed {success_count} articles")
                if failed_count > 0:
                    logger.error(f"Failed to index {failed_count} articles")
                
                return success_count
                
            except Exception as bulk_error:
                logger.error(f"Bulk operation failed: {bulk_error}")
                return 0
            
        except Exception as e:
            logger.error(f"Bulk indexing preparation failed: {e}")
            return 0
    
    def search_articles(self, query=None, category=None, size=20, from_=0):
        """Search articles in Elasticsearch"""
        if not self.is_connected():
            logger.error("Elasticsearch is not connected")
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

    def get_index_stats(self):
        """Get basic statistics about the index"""
        try:
            if not self.is_connected():
                return {"error": "Not connected to Elasticsearch"}
            
            # Check if index exists first
            if not self.client.indices.exists(index=self.index_name):
                return {"document_count": 0, "size_bytes": 0, "index_exists": False}
            
            stats = self.client.indices.stats(index=self.index_name)
            doc_count = stats['indices'][self.index_name]['total']['docs']['count']
            size = stats['indices'][self.index_name]['total']['store']['size_in_bytes']
            
            return {
                "document_count": doc_count,
                "size_bytes": size,
                "index_exists": True
            }
        except Exception as e:
            logger.error(f"Failed to get index stats: {e}")
            return {"error": str(e)}


# Global instance
es_client = ElasticsearchClient()
