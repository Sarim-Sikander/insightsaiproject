from typing import List, Optional

from pydantic import BaseModel


class RankedDocumentSchema(BaseModel):
    title: Optional[str]
    content: Optional[str]
    relevance_score: float
    numerical_score: float
    revenue: Optional[float]
    net_profit: Optional[float]
    revenue_growth_rate: Optional[float]
    operational_cost_reduction: Optional[float]


class NQueryResponseSchema(BaseModel):
    query: str
    response: str
    ranked_documents: List[RankedDocumentSchema]


class DocumentMetricsSchema(BaseModel):
    title: Optional[str]
    content: Optional[str]
    revenue: Optional[float]
    net_profit: Optional[float]
    revenue_growth_rate: Optional[float]
    operational_cost_reduction: Optional[float]


class QueryResponseSchema(BaseModel):
    query: str
    response: str
    documents: List[DocumentMetricsSchema]
