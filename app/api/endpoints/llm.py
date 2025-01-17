from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.integrations.es import es, search_elasticsearch
from app.integrations.llm import (
    compute_numerical_score,
    extract_and_enrich_documents,
    generate_llm_response,
)
from app.schemas.responses.llm import NQueryResponseSchema, QueryResponseSchema

router = APIRouter()  # Initialize the API router for endpoints.


@router.post("/query", response_model=QueryResponseSchema)
async def query_documents(
    query: str = Query(..., description="The user query for RAG"),
    limit: int = Query(5, description="Number of documents to retrieve"),
):
    documents = search_elasticsearch(query, limit)

    if not documents:
        raise HTTPException(status_code=404, detail="No relevant documents found.")

    enriched_documents = extract_and_enrich_documents(documents)

    context = "\n\n".join(
        f"Document {i+1}:\n{doc['content']}\nMetrics: Revenue: {doc['revenue']}, "
        f"Net Profit: {doc['net_profit']}, Growth Rate: {doc['revenue_growth_rate']}%, "
        f"Cost Reduction: {doc['operational_cost_reduction']}%"
        for i, doc in enumerate(enriched_documents)
    )

    try:
        llm_response = generate_llm_response(context=context, query=query)
    except RuntimeError as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating LLM response: {e}"
        )

    return {"query": query, "response": llm_response, "documents": enriched_documents}


@router.post("/numeric-query", response_model=NQueryResponseSchema)
async def query_numeric_documents(
    query: str = Query(..., description="The user query for RAG"),
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
    limit: int = Query(5, description="Number of documents to retrieve"),
):
    """
    Query Elasticsearch with a focus on numerical filtering and scoring.
    - Extract KPIs using LLM and parse them.
    - Apply range filters for the KPIs after extraction.
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
            status_code=400,
            detail="At least one numerical filter (min and max) must be provided.",
        )

    # Perform the Elasticsearch query
    response = search_elasticsearch(query, limit)
    if not response:
        raise HTTPException(status_code=404, detail="No relevant documents found.")

    documents = response
    scores = response

    if not documents:
        raise HTTPException(status_code=404, detail="No relevant documents found.")

    enriched_documents = extract_and_enrich_documents(documents)

    # Apply numeric filtering based on extracted KPIs
    filtered_documents = [
        doc
        for doc in enriched_documents
        if (
            not min_revenue
            or (doc["revenue"] is not None and doc["revenue"] >= min_revenue)
        )
        and (
            not max_revenue
            or (doc["revenue"] is not None and doc["revenue"] <= max_revenue)
        )
        and (
            not min_net_profit
            or (doc["net_profit"] is not None and doc["net_profit"] >= min_net_profit)
        )
        and (
            not max_net_profit
            or (doc["net_profit"] is not None and doc["net_profit"] <= max_net_profit)
        )
        and (
            not min_revenue_growth_rate
            or (
                doc["revenue_growth_rate"] is not None
                and doc["revenue_growth_rate"] >= min_revenue_growth_rate
            )
        )
        and (
            not max_revenue_growth_rate
            or (
                doc["revenue_growth_rate"] is not None
                and doc["revenue_growth_rate"] <= max_revenue_growth_rate
            )
        )
        and (
            not min_operational_cost_reduction
            or (
                doc["operational_cost_reduction"] is not None
                and doc["operational_cost_reduction"] >= min_operational_cost_reduction
            )
        )
        and (
            not max_operational_cost_reduction
            or (
                doc["operational_cost_reduction"] is not None
                and doc["operational_cost_reduction"] <= max_operational_cost_reduction
            )
        )
    ]

    # Compute scores for ranking
    query_params = {
        "revenue": (
            (min_revenue + max_revenue) / 2 if min_revenue and max_revenue else None
        ),
        "net_profit": (
            (min_net_profit + max_net_profit) / 2
            if min_net_profit and max_net_profit
            else None
        ),
        "revenue_growth_rate": (
            (min_revenue_growth_rate + max_revenue_growth_rate) / 2
            if min_revenue_growth_rate and max_revenue_growth_rate
            else None
        ),
        "operational_cost_reduction": (
            (min_operational_cost_reduction + max_operational_cost_reduction) / 2
            if min_operational_cost_reduction and max_operational_cost_reduction
            else None
        ),
    }

    ranked_documents = []
    for doc in filtered_documents:
        relevance_score = scores[documents.index(doc)] if doc in documents else 0
        numerical_score = compute_numerical_score(doc, query_params)
        final_score = 0.7 * relevance_score + 0.3 * numerical_score
        ranked_documents.append((final_score, relevance_score, numerical_score, doc))

    ranked_documents.sort(key=lambda x: x[0], reverse=True)

    context = "\n\n".join(
        f"Document {idx+1}:\n{doc['content']}\n"
        for idx, (_, _, _, doc) in enumerate(ranked_documents[:limit])
    )
    llm_response = generate_llm_response(context=context, query=query)

    return {
        "query": query,
        "response": llm_response,
        "ranked_documents": [
            {
                "title": doc.get("title"),
                "content": doc.get("content"),
                "relevance_score": relevance_score,
                "numerical_score": numerical_score,
                "revenue": doc.get("revenue"),
                "net_profit": doc.get("net_profit"),
                "revenue_growth_rate": doc.get("revenue_growth_rate"),
                "operational_cost_reduction": doc.get("operational_cost_reduction"),
            }
            for _, relevance_score, numerical_score, doc in ranked_documents[:limit]
        ],
    }


@router.get("/health-check")
async def health_check():
    """
    Verifies service availability.
    - Checks the health of the Elasticsearch cluster.
    - Returns the status of the LLM integration.
    """
    es_health = es.cluster.health()  # Get the health status of Elasticsearch.
    llm_status = {"status": "available"}  # Assume the LLM is available.

    return {
        "elasticsearch": {
            "status": es_health.get(
                "status"
            ),  # The status of the Elasticsearch cluster.
            "cluster_name": es_health.get(
                "cluster_name"
            ),  # The name of the Elasticsearch cluster.
            "number_of_nodes": es_health.get(
                "number_of_nodes"
            ),  # The number of nodes in the cluster.
        },
        "llm": llm_status,  # The status of the LLM.
    }
