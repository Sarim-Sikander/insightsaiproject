from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer

es = Elasticsearch(hosts=["http://localhost:9200"])

INDEX_NAME = "documents"

model = SentenceTransformer("all-MiniLM-L6-v2")

index_schema = {
    "mappings": {
        "properties": {
            "document_id": {"type": "keyword"},
            "title": {"type": "text"},
            "company": {"type": "text"},
            "date": {"type": "date"},
            "topics": {"type": "text"},
            "content": {"type": "text"},
            "conclusion": {"type": "text"},
            "embedding": {
                "type": "dense_vector",
                "dims": 384,
            },  
        }
    }
}

if not es.indices.exists(index=INDEX_NAME):
    es.indices.create(index=INDEX_NAME, body=index_schema)