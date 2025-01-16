from pydantic import BaseModel, Field


class ESearchRequestSchema(BaseModel):
    query: str = Field(..., description="Keyword-based query for Elasticsearch.")
    limit: int = Field(10, description="Maximum number of documents to return.")
