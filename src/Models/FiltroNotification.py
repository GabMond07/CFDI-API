from pydantic import BaseModel, Field, model_validator
from typing import Optional, Literal
from datetime import date
from fastapi import HTTPException

class FiltroNotification(BaseModel):
    type: Optional[str] = None
    status: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    cfdi_id: Optional[int] = None
    ordenar_por: Optional[str] = Field("created_at")
    ordenar_dir: Optional[Literal["asc", "desc"]] = "desc"
    pagina: int = Field(1, ge=1)
    por_pagina: int = Field(10, ge=1, le=100)

    @model_validator(mode="after")
    def validar_filtros(self):
        if self.fecha_inicio and self.fecha_fin:
            if self.fecha_inicio > self.fecha_fin:
                raise HTTPException(status_code=400, detail="La fecha de inicio no puede ser mayor que la fecha final")

        campos_validos = {"created_at", "type", "status", "cfdi_id"}
        if self.ordenar_por not in campos_validos:
            raise HTTPException(
                status_code=400,
                detail=f"Campo inválido para ordenar: '{self.ordenar_por}'. Opciones válidas: {', '.join(campos_validos)}"
            )

        estados_validos = {"pendiente", "enviado", "fallido"}
        if self.status and self.status.lower() not in estados_validos:
            raise HTTPException(
                status_code=400,
                detail=f"Estado inválido. Válidos: {', '.join(estados_validos)}"
            )

        return self
