from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.controllers.elasticsearch import ESController
from app.controllers.llms import LLMDocumentController
from app.core.factory.factory import Factory
from app.integrations.es import INDEX_NAME, es
from app.integrations.llm import parse_kpis_from_response
from app.schemas.responses.esearch import ESearchResponseSchema

router = APIRouter()


@router.get("/edocuments")
async def load_documents_to_elasticsearch(
    limit: int = 100,
    es_controller: ESController = Depends(Factory().get_es_controller),
):
    """
    Load documents from MySQL to Elasticsearch.
    - Deletes the existing Elasticsearch index, if present.
    - Fetches documents from MySQL and indexes them in Elasticsearch.
    """
    if es.indices.exists(index=INDEX_NAME):
        es.indices.delete(index=INDEX_NAME)
        print(f"Index {INDEX_NAME} deleted successfully.")
    documents = await es_controller.get_all(limit=limit)
    if not documents:
        raise HTTPException(status_code=404, detail="No documents found.")

    es_controller.index_documents_in_elasticsearch(documents)
    return {"status": "Documents indexed successfully"}


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
                    "query": query,
                    "fields": [
                        "title",
                        "topics",
                        "content",
                        "conclusion",
                    ],
                }
            },
            "size": limit,
        },
    )
    return {"results": [hit["_source"] for hit in response["hits"]["hits"]]}


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
    llm_controller: LLMDocumentController = Depends(Factory().get_llm_controller),
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
            llm_response = llm_controller.generate_llm_response(
                context=content, query=query_prompt
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error extracting KPIs: {e}")
        try:
            extracted_kpis = parse_kpis_from_response(llm_response)
        except Exception:
            continue

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
    es_controller: ESController = Depends(Factory().get_es_controller),
    llm_controller: LLMDocumentController = Depends(Factory().get_llm_controller),
):
    """
    Perform semantic search with optional numerical filters.
    - Uses vector embeddings for semantic matching if a query is provided.
    - Applies range filters for additional filtering of results.
    """
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

    filters = []
    if query:
        query_vector = es_controller.generate_embedding(query)
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

    response = es.search(index=INDEX_NAME, body=query_body)
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
            llm_response = llm_controller.generate_llm_response(
                context=content, query=query_prompt
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error extracting KPIs: {e}")

        try:
            extracted_kpis = parse_kpis_from_response(llm_response)
        except Exception:
            continue

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
