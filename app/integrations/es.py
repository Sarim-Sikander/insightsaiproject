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
            "revenue": {"type": "float"},
            "net_profit": {"type": "float"},
            "revenue_growth_rate": {"type": "float"},
            "operational_cost_reduction": {"type": "float"},
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
                "revenue": doc.revenue,
                "net_profit": doc.net_profit,
                "revenue_growth_rate": doc.revenue_growth_rate,
                "operational_cost_reduction": doc.operational_cost_reduction,
                "embedding": generate_embedding(
                    f"{doc.title} {doc.content} {doc.conclusion}"
                ),  # Add embedding
            },
        }
        for doc in documents
    ]
    bulk(es, actions)
