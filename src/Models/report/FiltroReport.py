from pydantic import BaseModel, Field, model_validator
from typing import Optional, Literal
from datetime import date
from fastapi import HTTPException

class FiltroReport(BaseModel):
    format: Optional[str] = None
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
                raise HTTPException(status_code=400, detail="fecha_inicio no puede ser mayor que fecha_fin")

        campos_validos = {"created_at", "format", "cfdi_id"}
        if self.ordenar_por not in campos_validos:
            raise HTTPException(
                status_code=400,
                detail=f"ordenar_por debe ser uno de: {', '.join(campos_validos)}"
            )

        formatos_validos = {"pdf", "xml", "csv", "json","PDF", "XML", "CSV", "JSON","XLS","xls"}
        if self.format  not in formatos_validos:
            raise HTTPException(
                status_code=400,
                detail=f"Formato inválido. Opciones válidas: {', '.join(formatos_validos)}"
            )

        return self
