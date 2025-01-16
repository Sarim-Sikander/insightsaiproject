from fastapi import APIRouter, HTTPException, Query

from app.integrations.es import INDEX_NAME, es
from app.integrations.llm import compute_numerical_score, generate_llm_response
from app.schemas.responses.llm import NQueryResponseSchema, QueryResponseSchema

router = APIRouter()  # Initialize the API router for endpoints.


@router.post("/query", response_model=QueryResponseSchema)
async def query_documents(
    query: str = Query(..., description="The user query for RAG"),
    limit: int = Query(5, description="Number of documents to retrieve"),
):
    """
    Query Elasticsearch to retrieve documents relevant to the provided query.
    - Performs a multi-field search in Elasticsearch.
    - Passes the results to the LLM for a tailored response.
    """
    response = es.search(
        index=INDEX_NAME,
        body={
            "query": {
                "multi_match": {
                    "query": query,  # The user query string.
                    "fields": ["title", "topics", "content", "conclusion"],  # Fields to search in.
                }
            },
            "size": limit,  # Limit the number of documents retrieved.
        },
    )

    documents = [hit["_source"] for hit in response["hits"]["hits"]]
    if not documents:  # Raise an error if no documents are found.
        raise HTTPException(status_code=404, detail="No relevant documents found.")

    # Create a context string from the retrieved documents.
    context = "\n\n".join(
        f"Document {i+1}:\n{doc['content']}\nMetrics: Revenue: {doc.get('revenue')}, "
        f"Net Profit: {doc.get('net_profit')}, Growth Rate: {doc.get('revenue_growth_rate')}%, "
        f"Cost Reduction: {doc.get('operational_cost_reduction')}%"
        for i, doc in enumerate(documents)
    )

    try:
        # Generate a response using the LLM.
        llm_response = generate_llm_response(context=context, query=query)
    except RuntimeError as e:  # Handle errors from the LLM.
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "query": query,
        "response": llm_response,  # The response generated by the LLM.
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
    """
    Query Elasticsearch with a focus on numerical filtering and scoring.
    - Applies a range filter on revenue.
    - Combines relevance scores from Elasticsearch and numerical scores for ranking.
    """
    if min_revenue is None or max_revenue is None:  # Ensure revenue filters are provided.
        raise HTTPException(
            status_code=400,
            detail="Both 'min_revenue' and 'max_revenue' must be provided.",
        )

    # Perform the Elasticsearch query.
    response = es.search(
        index=INDEX_NAME,
        body={
            "query": {
                "multi_match": {
                    "query": query,  # The user query string.
                    "fields": ["title", "topics", "content", "conclusion"],  # Fields to search in.
                }
            },
            "size": limit,  # Limit the number of documents retrieved.
        },
    )
    documents = [hit["_source"] for hit in response["hits"]["hits"]]
    scores = [hit["_score"] for hit in response["hits"]["hits"]]  # Relevance scores.

    if not documents:  # Raise an error if no documents are found.
        raise HTTPException(status_code=404, detail="No relevant documents found.")

    query_params = {
        "revenue": (min_revenue + max_revenue) / 2  # Calculate the average revenue filter.
    }

    ranked_documents = []
    for idx, (doc, relevance_score) in enumerate(zip(documents, scores)):
        numerical_score = compute_numerical_score(doc, query_params)  # Compute the numerical score.
        final_score = 0.7 * relevance_score + 0.3 * numerical_score  # Weighted scoring.
        ranked_documents.append((final_score, relevance_score, numerical_score, doc))

    ranked_documents.sort(key=lambda x: x[0], reverse=True)  # Sort documents by final score.

    # Create a context string from the ranked documents.
    context = "\n\n".join(
        f"Document {idx+1}:\n{doc['content']}\n"
        for idx, (_, _, _, doc) in enumerate(ranked_documents[:limit])
    )
    llm_response = generate_llm_response(context=context, query=query)  # Generate the LLM response.

    return {
        "query": query,
        "response": llm_response,  # The response generated by the LLM.
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
            "status": es_health.get("status"),  # The status of the Elasticsearch cluster.
            "cluster_name": es_health.get("cluster_name"),  # The name of the Elasticsearch cluster.
            "number_of_nodes": es_health.get("number_of_nodes"),  # The number of nodes in the cluster.
        },
        "llm": llm_status,  # The status of the LLM.
    }
