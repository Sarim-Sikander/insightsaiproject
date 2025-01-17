import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.controllers.documents import DocumentController
from app.core.factory.factory import Factory
from app.integrations.es import (
    INDEX_NAME,
    es,
    generate_embedding,
    index_documents_in_elasticsearch,
)
from app.integrations.llm import generate_llm_response, parse_kpis_from_response
from app.schemas.responses.esearch import ESearchResponseSchema

router = APIRouter()  # Initialize the API router for defining endpoints.


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
    - Builds range filters for numerical fields such as revenue and net profit.
    """
    filters = []

    if min_revenue is not None:  # Add a filter for minimum revenue.
        filters.append({"range": {"revenue": {"gte": min_revenue}}})
    if max_revenue is not None:  # Add a filter for maximum revenue.
        filters.append({"range": {"revenue": {"lte": max_revenue}}})

    if min_net_profit is not None:  # Add a filter for minimum net profit.
        filters.append({"range": {"net_profit": {"gte": min_net_profit}}})
    if max_net_profit is not None:  # Add a filter for maximum net profit.
        filters.append({"range": {"net_profit": {"lte": max_net_profit}}})

    if (
        min_revenue_growth_rate is not None
    ):  # Add a filter for minimum revenue growth rate.
        filters.append(
            {"range": {"revenue_growth_rate": {"gte": min_revenue_growth_rate}}}
        )
    if (
        max_revenue_growth_rate is not None
    ):  # Add a filter for maximum revenue growth rate.
        filters.append(
            {"range": {"revenue_growth_rate": {"lte": max_revenue_growth_rate}}}
        )

    if (
        min_operational_cost_reduction is not None
    ):  # Add a filter for minimum cost reduction.
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
    ):  # Add a filter for maximum cost reduction.
        filters.append(
            {
                "range": {
                    "operational_cost_reduction": {
                        "lte": max_operational_cost_reduction
                    }
                }
            }
        )

    return filters  # Return the list of filters.


@router.get("/edocuments")
async def load_documents_to_elasticsearch(
    limit: int = 100,
    document_controller: DocumentController = Depends(
        Factory().get_document_controller
    ),
):
    """
    Load documents from MySQL to Elasticsearch.
    - Deletes the existing Elasticsearch index, if present.
    - Fetches documents from MySQL and indexes them in Elasticsearch.
    """
    if es.indices.exists(
        index=INDEX_NAME
    ):  # Check if the index exists in Elasticsearch.
        es.indices.delete(index=INDEX_NAME)  # Delete the index.
        print(f"Index {INDEX_NAME} deleted successfully.")
    documents = await document_controller.get_all(
        limit=limit
    )  # Fetch documents from MySQL.
    if not documents:  # Raise an error if no documents are found.
        raise HTTPException(status_code=404, detail="No documents found.")

    index_documents_in_elasticsearch(documents)  # Index the documents in Elasticsearch.
    return {"status": "Documents indexed successfully"}  # Return a success response.


@router.post("/esearch", response_model=ESearchResponseSchema)
async def esearch_documents(
    query: str = Query(..., description="Keyword-based search query"),
    limit: int = Query(10, description="Maximum number of results to return"),
):
    """
    Perform a keyword-based search in Elasticsearch.
    - Searches for the query in multiple fields (title, topics, content, conclusion).
    """
    response = es.search(
        index=INDEX_NAME,
        body={
            "query": {
                "multi_match": {
                    "query": query,  # Search query string.
                    "fields": [
                        "title",
                        "topics",
                        "content",
                        "conclusion",
                    ],  # Fields to search in.
                }
            },
            "size": limit,  # Limit the number of results returned.
        },
    )
    return {
        "results": [hit["_source"] for hit in response["hits"]["hits"]]
    }  # Return the results.


@router.post("/efilter")
async def filter_documents(
    min_revenue: Optional[float] = Query(None, description="Minimum revenue filter"),
    max_revenue: Optional[float] = Query(None, description="Maximum revenue filter"),
    min_net_profit: Optional[float] = Query(
        None, description="Minimum net profit filter"
    ),
    max_net_profit: Optional[float] = Query(
        None, description="Maximum net profit filter"
    ),
    min_revenue_growth_rate: Optional[float] = Query(
        None, description="Minimum revenue growth rate filter"
    ),
    max_revenue_growth_rate: Optional[float] = Query(
        None, description="Maximum revenue growth rate filter"
    ),
    min_operational_cost_reduction: Optional[float] = Query(
        None, description="Minimum operational cost reduction filter"
    ),
    max_operational_cost_reduction: Optional[float] = Query(
        None, description="Maximum operational cost reduction filter"
    ),
    limit: int = Query(10, description="Maximum number of results to return"),
):
    """
    Filter documents by extracting KPIs from content and applying range filters.
    - Uses NLP to extract numeric KPIs from the 'content' field.
    - Filters results based on user-provided min and max ranges.
    """
    if not any(
        [
            min_revenue,
            max_revenue,
            min_net_profit,
            max_net_profit,
            min_revenue_growth_rate,
            max_revenue_growth_rate,
            min_operational_cost_reduction,
            max_operational_cost_reduction,
        ]
    ):
        raise HTTPException(
            status_code=400, detail="At least one filter must be provided."
        )

    response = es.search(
        index=INDEX_NAME,
        body={"query": {"match_all": {}}, "size": limit},
    )

    documents = [hit["_source"] for hit in response["hits"]["hits"]]
    if not documents:
        raise HTTPException(status_code=404, detail="No documents found.")

    filtered_results = []
    for doc in documents:
        content = doc.get("content", "")
        if not content:
            continue

        query_prompt = (
            "Extract the following KPIs from the content: revenue, net profit, "
            "revenue growth rate, and operational cost reduction.\n"
            f"Content:\n{content}"
        )
        try:
            llm_response = generate_llm_response(context=content, query=query_prompt)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error extracting KPIs: {e}")
        try:
            extracted_kpis = parse_kpis_from_response(llm_response)
        except Exception:
            continue  # Skip if parsing fails

        # Apply filters
        if (
            (min_revenue is None or extracted_kpis.get("revenue", 0) >= min_revenue)
            and (
                max_revenue is None
                or extracted_kpis.get("revenue", float("inf")) <= max_revenue
            )
            and (
                min_net_profit is None
                or extracted_kpis.get("net_profit", 0) >= min_net_profit
            )
            and (
                max_net_profit is None
                or extracted_kpis.get("net_profit", float("inf")) <= max_net_profit
            )
            and (
                min_revenue_growth_rate is None
                or extracted_kpis.get("revenue_growth_rate", 0)
                >= min_revenue_growth_rate
            )
            and (
                max_revenue_growth_rate is None
                or extracted_kpis.get("revenue_growth_rate", float("inf"))
                <= max_revenue_growth_rate
            )
            and (
                min_operational_cost_reduction is None
                or extracted_kpis.get("operational_cost_reduction", 0)
                >= min_operational_cost_reduction
            )
            and (
                max_operational_cost_reduction is None
                or extracted_kpis.get("operational_cost_reduction", float("inf"))
                <= max_operational_cost_reduction
            )
        ):
            filtered_results.append(
                {
                    "title": doc.get("title"),
                    "content": content,
                    "extracted_kpis": extracted_kpis,
                }
            )

    if not filtered_results:
        raise HTTPException(
            status_code=404, detail="No documents matched the filter criteria."
        )

    return {"results": filtered_results}


@router.post("/semantic-search")
async def semantic_search(
    query: Optional[str] = Query(None, description="Query for semantic search"),
    min_revenue: Optional[float] = Query(None, description="Minimum revenue filter"),
    max_revenue: Optional[float] = Query(None, description="Maximum revenue filter"),
    min_net_profit: Optional[float] = Query(
        None, description="Minimum net profit filter"
    ),
    max_net_profit: Optional[float] = Query(
        None, description="Maximum net profit filter"
    ),
    min_revenue_growth_rate: Optional[float] = Query(
        None, description="Minimum revenue growth rate filter"
    ),
    max_revenue_growth_rate: Optional[float] = Query(
        None, description="Maximum revenue growth rate filter"
    ),
    min_operational_cost_reduction: Optional[float] = Query(
        None, description="Minimum operational cost reduction filter"
    ),
    max_operational_cost_reduction: Optional[float] = Query(
        None, description="Maximum operational cost reduction filter"
    ),
    limit: int = Query(10, description="Maximum number of results to return"),
):
    """
    Perform semantic search with optional numerical filters.
    - Uses vector embeddings for semantic matching if a query is provided.
    - Applies range filters for additional filtering of results.
    """
    # Ensure that either a query or filters are provided
    if not query and not any(
        [
            min_revenue,
            max_revenue,
            min_net_profit,
            max_net_profit,
            min_revenue_growth_rate,
            max_revenue_growth_rate,
            min_operational_cost_reduction,
            max_operational_cost_reduction,
        ]
    ):
        raise HTTPException(
            status_code=400, detail="At least one filter or a query must be provided."
        )

    # Initialize Elasticsearch query
    filters = []
    if query:
        query_vector = generate_embedding(query)  # Generate embedding for the query
        semantic_query = {
            "script_score": {
                "query": (
                    {"bool": {"filter": filters}} if filters else {"match_all": {}}
                ),
                "script": {
                    "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                    "params": {"query_vector": query_vector},
                },
            }
        }
        query_body = {"query": semantic_query, "size": limit}
    else:
        query_body = {"query": {"bool": {"filter": filters}}, "size": limit}

    # Search in Elasticsearch
    response = es.search(index=INDEX_NAME, body=query_body)
    documents = [hit["_source"] for hit in response["hits"]["hits"]]
    if not documents:
        raise HTTPException(status_code=404, detail="No documents found.")

    # LLM-based KPI extraction and filtering
    filtered_results = []
    for doc in documents:
        content = doc.get("content", "")
        if not content:
            continue

        # Use LLM to extract KPIs
        query_prompt = (
            "Extract the following KPIs from the content: revenue, net profit, "
            "revenue growth rate, and operational cost reduction.\n"
            f"Content:\n{content}"
        )
        try:
            llm_response = generate_llm_response(context=content, query=query_prompt)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error extracting KPIs: {e}")

        # Parse KPIs from the response
        try:
            extracted_kpis = parse_kpis_from_response(llm_response)
        except Exception:
            continue

        # Apply filters
        if (
            (min_revenue is None or extracted_kpis.get("revenue", 0) >= min_revenue)
            and (
                max_revenue is None
                or extracted_kpis.get("revenue", float("inf")) <= max_revenue
            )
            and (
                min_net_profit is None
                or extracted_kpis.get("net_profit", 0) >= min_net_profit
            )
            and (
                max_net_profit is None
                or extracted_kpis.get("net_profit", float("inf")) <= max_net_profit
            )
            and (
                min_revenue_growth_rate is None
                or extracted_kpis.get("revenue_growth_rate", 0)
                >= min_revenue_growth_rate
            )
            and (
                max_revenue_growth_rate is None
                or extracted_kpis.get("revenue_growth_rate", float("inf"))
                <= max_revenue_growth_rate
            )
            and (
                min_operational_cost_reduction is None
                or extracted_kpis.get("operational_cost_reduction", 0)
                >= min_operational_cost_reduction
            )
            and (
                max_operational_cost_reduction is None
                or extracted_kpis.get("operational_cost_reduction", float("inf"))
                <= max_operational_cost_reduction
            )
        ):
            filtered_results.append(
                {
                    "title": doc.get("title"),
                    "content": content,
                    "extracted_kpis": extracted_kpis,
                }
            )

    if not filtered_results:
        raise HTTPException(
            status_code=404, detail="No documents matched the filter criteria."
        )

    return {"results": filtered_results}
