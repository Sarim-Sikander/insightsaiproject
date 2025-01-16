from fastapi import APIRouter, HTTPException, Query

from app.integrations.es import INDEX_NAME, es
from app.integrations.llm import compute_numerical_score, generate_llm_response
from app.schemas.responses.llm import NQueryResponseSchema, QueryResponseSchema

router = APIRouter()

@router.post("/query", response_model=QueryResponseSchema)
async def query_documents(
    query: str = Query(..., description="The user query for RAG"),
    limit: int = Query(5, description="Number of documents to retrieve"),
):
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

    documents = [hit["_source"] for hit in response["hits"]["hits"]]
    if not documents:
        raise HTTPException(status_code=404, detail="No relevant documents found.")

    context = "\n\n".join(
        f"Document {i+1}:\n{doc['content']}\nMetrics: Revenue: {doc.get('revenue')}, "
        f"Net Profit: {doc.get('net_profit')}, Growth Rate: {doc.get('revenue_growth_rate')}%, "
        f"Cost Reduction: {doc.get('operational_cost_reduction')}%"
        for i, doc in enumerate(documents)
    )

    try:
        llm_response = generate_llm_response(context=context, query=query)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "query": query,
        "response": llm_response,
        "documents": [
            {
                "title": doc.get("title"),
                "content": doc.get("content"),
                "revenue": doc.get("revenue"),
                "net_profit": doc.get("net_profit"),
                "revenue_growth_rate": doc.get("revenue_growth_rate"),
                "operational_cost_reduction": doc.get("operational_cost_reduction"),
            }
            for doc in documents
        ],
    }
    
    
@router.post("/numeric-query", response_model=NQueryResponseSchema)
async def query_numeric_documents(
    query: str = Query(..., description="The user query for RAG"),
    min_revenue: float = Query(None, description="Minimum revenue filter"),
    max_revenue: float = Query(None, description="Maximum revenue filter"),
    limit: int = Query(5, description="Number of documents to retrieve"),
):
    if min_revenue is None or max_revenue is None:
        raise HTTPException(
            status_code=400,
            detail="Both 'min_revenue' and 'max_revenue' must be provided.",
        )

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
    documents = [hit["_source"] for hit in response["hits"]["hits"]]
    scores = [hit["_score"] for hit in response["hits"]["hits"]]

    if not documents:
        raise HTTPException(status_code=404, detail="No relevant documents found.")

    query_params = {
        "revenue": (min_revenue + max_revenue) / 2
    }
    ranked_documents = []
    for idx, (doc, relevance_score) in enumerate(zip(documents, scores)):
        numerical_score = compute_numerical_score(doc, query_params)
        final_score = 0.7 * relevance_score + 0.3 * numerical_score  # Weighted scoring
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
    """
    es_health = es.cluster.health()
    llm_status = {"status": "available"}

    return {
        "elasticsearch": {
            "status": es_health.get("status"),
            "cluster_name": es_health.get("cluster_name"),
            "number_of_nodes": es_health.get("number_of_nodes"),
        },
        "llm": llm_status,
    }