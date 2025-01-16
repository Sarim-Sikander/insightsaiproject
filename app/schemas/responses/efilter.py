from typing import List

from pydantic import BaseModel

from app.schemas.responses.document import DocumentSchema


class FilterResponseSchema(BaseModel):
    results: List[DocumentSchema]
