INDEX_NAME = "documents"

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
        }
    }
}
