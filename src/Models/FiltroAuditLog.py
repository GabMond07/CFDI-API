from pydantic import BaseModel, Field, model_validator
from typing import Optional, Literal
from datetime import date
from fastapi import HTTPException

class FiltroAuditLog(BaseModel):
    action: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    ordenar_por: Optional[str] = Field("created_at")
    ordenar_dir: Optional[Literal["asc", "desc"]] = "desc"
    pagina: int = Field(1, ge=1)
    por_pagina: int = Field(10, ge=1, le=100)

    @model_validator(mode="after")
    def validar_filtros(self):
        # Validar fechas
        if self.fecha_inicio and self.fecha_fin:
            if self.fecha_inicio > self.fecha_fin:
                raise ValueError("La fecha de inicio no puede ser mayor que la fecha final")

        # Validar campo para ordenar
        campos_validos = {"created_at", "action"}
        if self.ordenar_por not in campos_validos:
            raise ValueError(
                f"Campo inválido para ordenar: '{self.ordenar_por}'. Opciones válidas: {', '.join(campos_validos)}")

        return self

