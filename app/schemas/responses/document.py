from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class DocumentSchema(BaseModel):
    document_id: str
    title: Optional[str]
    company: Optional[str]
    date: Optional[str]
    topics: Optional[str]
    content: Optional[str]
    conclusion: Optional[str]
    revenue: Optional[float]
    net_profit: Optional[float]
    revenue_growth_rate: Optional[float]
    operational_cost_reduction: Optional[float]

    @validator("date", pre=True, always=True)
    def format_date(cls, value):
        if isinstance(value, date):
            return value.strftime("%Y-%m-%d")
        return value

    class Config:
        orm_mode = True
