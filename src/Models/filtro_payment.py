from pydantic import BaseModel, Field, model_validator
from typing import Optional, Literal
from datetime import date
from fastapi import HTTPException

class FiltroPayment(BaseModel):
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date]= None
    forma_pago: Optional[str]= None
    moneda: Optional[str]= None
    monto_min: Optional[float] = Field(None, ge=0, description="Monto mínimo no puede ser negativo")
    monto_max: Optional[float] = Field(None, ge=0, description="Monto máximo no puede ser negativo")
    ordenar_por: Optional[str] = Field("payment_date")
    ordenar_dir: Optional[Literal["asc", "desc"]] = "asc"
    pagina: int = Field(1, ge=1)
    por_pagina: int = Field(10, ge=1, le=100)

    @model_validator(mode="after")
    def validar_filtro(self):
        if self.fecha_inicio and self.fecha_fin:
            if self.fecha_inicio > self.fecha_fin:
                raise HTTPException(status_code=400, detail="fecha_inicio no puede ser mayor que fecha_fin")

        if self.monto_min is not None and self.monto_min < 0:
            raise HTTPException(status_code=400, detail="monto_min no puede ser negativo")
        if self.monto_max is not None and self.monto_max < 0:
            raise HTTPException(status_code=400, detail="monto_max no puede ser negativo")
        if self.monto_min is not None and self.monto_max is not None:
            if self.monto_min > self.monto_max:
                raise HTTPException(status_code=400, detail="monto_min no puede ser mayor que monto_max")

        campos_validos = {"payment_date", "amount", "currency", "forma_Pago"}
        if self.ordenar_por not in campos_validos:
            raise HTTPException(status_code=400, detail=f"ordenar_por debe ser uno de {campos_validos}")

        if self.ordenar_dir.lower() not in {"asc", "desc"}:
            raise HTTPException(status_code=400, detail="ordenar_dir debe ser 'asc' o 'desc'")

        self.ordenar_dir = self.ordenar_dir.lower()

        return self
