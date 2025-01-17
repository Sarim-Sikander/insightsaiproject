from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
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
            },  # Vector field for semantic search
        }
    }
}

# Create the index if it does not exist
if not es.indices.exists(index=INDEX_NAME):
    es.indices.create(index=INDEX_NAME, body=index_schema)


def generate_embedding(text):
    """
    Generate an embedding vector for the given text using Sentence Transformers.
    """
    return model.encode(text).tolist()


def index_documents_in_elasticsearch(documents):
    """
    Index documents into Elasticsearch with embeddings for semantic search.
    """
    actions = [
        {
            "_index": INDEX_NAME,
            "_id": doc.document_id,
            "_source": {
                "document_id": doc.document_id,
                "title": doc.title,
                "company": doc.company,
                "date": doc.date.isoformat() if doc.date else None,
                "topics": doc.topics,
                "content": doc.content,
                "conclusion": doc.conclusion,
                "embedding": generate_embedding(
                    f"{doc.title} {doc.content} {doc.conclusion}"
                ),
            },
        }
        for doc in documents
    ]
    bulk(es, actions)


def search_elasticsearch(query: str, limit: int) -> list:
    """
    Perform an Elasticsearch query and return the results.
    """
    response = es.search(
        index=INDEX_NAME,
        body={
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["title", "topics", "content", "conclusion"],
                }
            },
            "size": limit,
        },
    )
    return [hit["_source"] for hit in response["hits"]["hits"]]
