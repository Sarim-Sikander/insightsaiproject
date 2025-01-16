from typing import Optional

from pydantic import BaseModel, Field, root_validator


class FilterRequestSchema(BaseModel):
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

    @staticmethod
    def at_least_one_field_provided(data):
        if not any(
            value is not None
            for value in [
                data.min_revenue,
                data.max_revenue,
                data.min_net_profit,
                data.max_net_profit,
                data.min_revenue_growth_rate,
                data.max_revenue_growth_rate,
                data.min_operational_cost_reduction,
                data.max_operational_cost_reduction,
            ]
        ):
            raise ValueError("At least one filter parameter must be provided.")
        return data

    @root_validator(pre=True)
    def validate_at_least_one_field(cls, values):
        return cls.at_least_one_field_provided(values)
