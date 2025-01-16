from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query

from app.controllers.documents import DocumentController
from app.core.factory.factory import Factory
from app.integrations.es import (
    INDEX_NAME,
    es,
    generate_embedding,
    index_documents_in_elasticsearch,
)
from app.schemas.responses.efilter import FilterResponseSchema
from app.schemas.responses.esearch import ESearchResponseSchema
from app.schemas.responses.semantic_search import SemanticSearchResponseSchema

router = APIRouter()


def create_filters(
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

    if min_revenue_growth_rate is not None:
        filters.append({"range": {"revenue_growth_rate": {"gte": min_revenue_growth_rate}}})
    if max_revenue_growth_rate is not None:
        filters.append({"range": {"revenue_growth_rate": {"lte": max_revenue_growth_rate}}})

    if min_operational_cost_reduction is not None:
        filters.append(
            {"range": {"operational_cost_reduction": {"gte": min_operational_cost_reduction}}}
        )
    if max_operational_cost_reduction is not None:
        filters.append(
            {"range": {"operational_cost_reduction": {"lte": max_operational_cost_reduction}}}
        )

    return filters


@router.get("/edocuments")
async def load_documents_to_elasticsearch(
    limit: int = 100,
    document_controller: DocumentController = Depends(Factory().get_document_controller),
):
    """
    Load documents from MySQL to Elasticsearch.
    """
    if es.indices.exists(index=INDEX_NAME):
        es.indices.delete(index=INDEX_NAME)
        print(f"Index {INDEX_NAME} deleted successfully.")
    documents = await document_controller.get_all(limit=limit)
    if not documents:
        raise HTTPException(status_code=404, detail="No documents found.")

    index_documents_in_elasticsearch(documents)
    return {"status": "Documents indexed successfully"}


@router.post("/esearch", response_model=ESearchResponseSchema)
async def esearch_documents(
    query: str = Query(..., description="Keyword-based search query"),
    limit: int = Query(10, description="Maximum number of results to return"),
):
    """
    Perform a keyword-based search in Elasticsearch.
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
    return {"results": [hit["_source"] for hit in response["hits"]["hits"]]}


@router.post("/efilter", response_model=FilterResponseSchema)
async def filter_documents(
    min_revenue: Optional[float] = Query(None, description="Minimum revenue filter"),
    max_revenue: Optional[float] = Query(None, description="Maximum revenue filter"),
    min_net_profit: Optional[float] = Query(None, description="Minimum net profit filter"),
    max_net_profit: Optional[float] = Query(None, description="Maximum net profit filter"),
    min_revenue_growth_rate: Optional[float] = Query(None, description="Minimum revenue growth rate filter"),
    max_revenue_growth_rate: Optional[float] = Query(None, description="Maximum revenue growth rate filter"),
    min_operational_cost_reduction: Optional[float] = Query(None, description="Minimum operational cost reduction filter"),
    max_operational_cost_reduction: Optional[float] = Query(None, description="Maximum operational cost reduction filter"),
    limit: int = Query(10, description="Maximum number of results to return"),
):
    """
    Filter documents based on numerical fields.
    """
    filters = create_filters(
        min_revenue=min_revenue,
        max_revenue=max_revenue,
        min_net_profit=min_net_profit,
        max_net_profit=max_net_profit,
        min_revenue_growth_rate=min_revenue_growth_rate,
        max_revenue_growth_rate=max_revenue_growth_rate,
        min_operational_cost_reduction=min_operational_cost_reduction,
        max_operational_cost_reduction=max_operational_cost_reduction,
    )

    if not filters:
        raise HTTPException(
            status_code=400, detail="At least one filter parameter must be provided."
        )

    query_body = {"query": {"bool": {"filter": filters}}, "size": limit}

    response = es.search(index=INDEX_NAME, body=query_body)
    return {"results": [hit["_source"] for hit in response["hits"]["hits"]]}


@router.post("/semantic-search", response_model=SemanticSearchResponseSchema)
async def semantic_search(
    query: Optional[str] = Query(None, description="Query for semantic search"),
    min_revenue: Optional[float] = Query(None, description="Minimum revenue filter"),
    max_revenue: Optional[float] = Query(None, description="Maximum revenue filter"),
    min_net_profit: Optional[float] = Query(None, description="Minimum net profit filter"),
    max_net_profit: Optional[float] = Query(None, description="Maximum net profit filter"),
    min_revenue_growth_rate: Optional[float] = Query(None, description="Minimum revenue growth rate filter"),
    max_revenue_growth_rate: Optional[float] = Query(None, description="Maximum revenue growth rate filter"),
    min_operational_cost_reduction: Optional[float] = Query(None, description="Minimum operational cost reduction filter"),
    max_operational_cost_reduction: Optional[float] = Query(None, description="Maximum operational cost reduction filter"),
    limit: int = Query(10, description="Maximum number of results to return"),
):
    """
    Perform semantic search with optional numerical filters.
    """
    filters = create_filters(
        min_revenue=min_revenue,
        max_revenue=max_revenue,
        min_net_profit=min_net_profit,
        max_net_profit=max_net_profit,
        min_revenue_growth_rate=min_revenue_growth_rate,
        max_revenue_growth_rate=max_revenue_growth_rate,
        min_operational_cost_reduction=min_operational_cost_reduction,
        max_operational_cost_reduction=max_operational_cost_reduction,
    )

    if not query and not filters:
        raise HTTPException(
            status_code=400, detail="At least one filter or a query must be provided."
        )

    if query:
        query_vector = generate_embedding(query)
        semantic_query = {
            "script_score": {
                "query": {"bool": {"filter": filters}} if filters else {"match_all": {}},
                "script": {
                    "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                    "params": {"query_vector": query_vector},
                },
            }
        }
        query_body = {"query": semantic_query, "size": limit}
    else:
        query_body = {"query": {"bool": {"filter": filters}}, "size": limit}

    response = es.search(index=INDEX_NAME, body=query_body)
    return {"results": [hit["_source"] for hit in response["hits"]["hits"]]}
