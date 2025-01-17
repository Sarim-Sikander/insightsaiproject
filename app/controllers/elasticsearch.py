from typing import List, Optional

from elasticsearch.helpers import bulk

from app.controllers.base import BaseController
from app.integrations.es import INDEX_NAME, es, model
from app.models.documents import Documents
from app.repositories import DocumentRepository


class ESController(BaseController[Documents]):
    def __init__(self, document_repository: DocumentRepository):
        super().__init__(model=Documents, repository=document_repository)
        self.document_repository = document_repository

    def generate_embedding(self, text):
        """
        Generate an embedding vector for the given text using Sentence Transformers.
        """
        return model.encode(text).tolist()

    def index_documents_in_elasticsearch(self, documents):
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
                    "embedding": self.generate_embedding(
                        f"{doc.title} {doc.content} {doc.conclusion}"
                    ),
                },
            }
            for doc in documents
        ]
        bulk(es, actions)

    def search_elasticsearch(self, query: str, limit: int) -> list:
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

    def create_filters(
        self,
        min_revenue: Optional[float] = None,
        max_revenue: Optional[float] = None,
        min_net_profit: Optional[float] = None,
        max_net_profit: Optional[float] = None,
        min_revenue_growth_rate: Optional[float] = None,
        max_revenue_growth_rate: Optional[float] = None,
        min_operational_cost_reduction: Optional[float] = None,
        max_operational_cost_reduction: Optional[float] = None,
    ) -> List[dict]:
        """
        Create a list of range filters for Elasticsearch queries.
        - Builds range filters for numerical fields such as revenue and net profit.
        """
        filters = []

        if min_revenue is not None: 
            filters.append({"range": {"revenue": {"gte": min_revenue}}})
        if max_revenue is not None: 
            filters.append({"range": {"revenue": {"lte": max_revenue}}})

        if min_net_profit is not None: 
            filters.append({"range": {"net_profit": {"gte": min_net_profit}}})
        if max_net_profit is not None: 
            filters.append({"range": {"net_profit": {"lte": max_net_profit}}})

        if (
            min_revenue_growth_rate is not None
        ): 
            filters.append(
                {"range": {"revenue_growth_rate": {"gte": min_revenue_growth_rate}}}
            )
        if (
            max_revenue_growth_rate is not None
        ): 
            filters.append(
                {"range": {"revenue_growth_rate": {"lte": max_revenue_growth_rate}}}
            )

        if (
            min_operational_cost_reduction is not None
        ): 
            filters.append(
                {
                    "range": {
                        "operational_cost_reduction": {
                            "gte": min_operational_cost_reduction
                        }
                    }
                }
            )
        if (
            max_operational_cost_reduction is not None
        ): 
            filters.append(
                {
                    "range": {
                        "operational_cost_reduction": {
                            "lte": max_operational_cost_reduction
                        }
                    }
                }
            )

        return filters  
