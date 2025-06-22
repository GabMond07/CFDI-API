from typing import Optional, Literal
from fastapi import HTTPException
from pydantic import BaseModel, Field, model_validator
from datetime import datetime


class FiltroConsulta(BaseModel):
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    categoria: Optional[str] = None
    monto_min: Optional[float] = Field(None, ge=0, description="Monto mínimo no puede ser negativo")
    monto_max: Optional[float] = Field(None, ge=0, description="Monto máximo no puede ser negativo")
    ordenar_por: Optional[str] = Field("Issue_Date")
    ordenar_dir: Optional[Literal["asc", "desc"]] = "asc"
    pagina: int = Field(1, ge=1)
    por_pagina: int = Field(10, ge=1, le=100)

    @model_validator(mode="after")
    def validar_campos(self):
        fi, ff = self.fecha_inicio, self.fecha_fin
        min_m, max_m = self.monto_min, self.monto_max

        # Validar fechas (fi debe ser <= ff)
        if fi and ff and fi > ff:
            raise ValueError("La fecha de inicio no puede ser mayor que la fecha final")

        # Validar montos
        if min_m is not None and max_m is not None and min_m > max_m:
            raise HTTPException(status_code=400, detail="El monto mínimo no puede ser mayor que el máximo")

        # Validar ordenar_por
        campos_validos = ["Issue_Date", "Total", "Subtotal"]
        if self.ordenar_por not in campos_validos:
            self.ordenar_por = "Issue_Date"  # valor por defecto

        # Validar ordenar_dir
        direcciones_validas = ["asc", "desc"]
        if self.ordenar_dir.lower() not in direcciones_validas:
            self.ordenar_dir = "asc"
        else:
            self.ordenar_dir = self.ordenar_dir.lower()

        return self
