from typing import Optional

from pydantic import BaseModel, Field, ValidationError, root_validator


class SemanticSearchRequestSchema(BaseModel):
    query: Optional[str] = Field(None, description="Query for semantic search.")
    min_revenue: Optional[float] = Field(None, description="Minimum revenue filter.")
    max_revenue: Optional[float] = Field(None, description="Maximum revenue filter.")
    min_net_profit: Optional[float] = Field(
        None, description="Minimum net profit filter."
    )
    max_net_profit: Optional[float] = Field(
        None, description="Maximum net profit filter."
    )
    min_revenue_growth_rate: Optional[float] = Field(
        None, description="Minimum revenue growth rate filter."
    )
    max_revenue_growth_rate: Optional[float] = Field(
        None, description="Maximum revenue growth rate filter."
    )
    min_operational_cost_reduction: Optional[float] = Field(
        None, description="Minimum operational cost reduction filter."
    )
    max_operational_cost_reduction: Optional[float] = Field(
        None, description="Maximum operational cost reduction filter."
    )
    limit: int = Field(10, description="Maximum number of documents to return.")

    @root_validator(pre=True)
    def validate_at_least_one_field(cls, values):
        if not any(
            value is not None
            for value in [
                values.get("query"),
                values.get("min_revenue"),
                values.get("max_revenue"),
                values.get("min_net_profit"),
                values.get("max_net_profit"),
                values.get("min_revenue_growth_rate"),
                values.get("max_revenue_growth_rate"),
                values.get("min_operational_cost_reduction"),
                values.get("max_operational_cost_reduction"),
            ]
        ):
            raise ValueError("At least one parameter or query must be provided.")
        return values
