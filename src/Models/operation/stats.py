from pydantic import BaseModel, Field
from typing import Literal, Optional
from .common import CFDIFilter

class StatsRequest(BaseModel):
    field: Literal["total", "subtotal"]
    filters: Optional[CFDIFilter] = None

class CentralTendencyResponse(BaseModel):
    average: float
    median: float
    mode: float

class BasicStatsResponse(BaseModel):
    range: float
    variance: float
    standard_deviation: float
    coefficient_of_variation: float