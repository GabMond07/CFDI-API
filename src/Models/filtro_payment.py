from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import date

class FiltroPayment(BaseModel):
    fecha_inicio: Optional[date]
    fecha_fin: Optional[date]
    forma_pago: Optional[str]
    moneda: Optional[str]
    monto_min: Optional[float]
    monto_max: Optional[float]
    ordenar_por: Optional[str] = Field("Payment_Date")
    ordenar_dir: Optional[Literal["asc", "desc"]] = "asc"
    pagina: int = Field(1, ge=1)
    por_pagina: int = Field(10, ge=1, le=100)

    class Config:
        extra = "ignore"