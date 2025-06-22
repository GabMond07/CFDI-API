from pydantic import BaseModel, Field
from typing import Optional, Literal

class FiltroTax(BaseModel):
    type: Optional[str] = None
    tax: Optional[str] = None
    rate_min: Optional[float] = None
    rate_max: Optional[float] = None
    amount_min: Optional[float] = None
    amount_max: Optional[float] = None
    concept_id: Optional[int] = None
    ordenar_por: Optional[str] = Field("Tax_ID")
    ordenar_dir: Optional[Literal["asc", "desc"]] = "asc"
    pagina: int = Field(1, ge=1)
    por_pagina: int = Field(10, ge=1, le=100)
