from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Literal
from .common import CFDIFilter

class AggregationRequest(BaseModel):
    operation: Literal["sum", "count", "avg", "min", "max"]
    field: Literal["total", "subtotal"]
    filters: Optional[CFDIFilter] = None
    include_details: bool = False

class AggregationResponse(BaseModel):
    result: Dict[str, float | int]
    details: Optional[List[Dict]] = None