from pydantic import BaseModel, Field
from typing import List, Literal
from .common import CFDIResponse

class CFDISort(BaseModel):
    field: Literal["issue_date", "total"] = "issue_date"
    direction: Literal["asc", "desc"] = "desc"

class PaginatedCFDIResponse(BaseModel):
    items: List[CFDIResponse]
    total: int
    page: int
    page_size: int