from pydantic import BaseModel, Field, model_validator
from typing import Optional, Literal
from datetime import date
from fastapi import HTTPException

class FiltroBatchJob(BaseModel):
    status: Optional[str] = None
    min_resultados: Optional[int] = Field(None, ge=0, description="Monto mínimo no puede ser negativo")
    max_resultados: Optional[int] = Field(None, ge=0, description="Monto máximo no puede ser negativo")
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
                raise HTTPException(
                    status_code=400,
                    detail="La fecha de inicio no puede ser mayor que la fecha final"
                )

        # Validar resultados
        if self.min_resultados is not None and self.max_resultados is not None:
            if self.min_resultados > self.max_resultados:
                raise HTTPException(
                    status_code=400,
                    detail="El número mínimo de resultados no puede ser mayor que el máximo"
                )

        # Validar campo para ordenar
        campos_validos = {"created_at", "status", "resultados"}
        if self.ordenar_por not in campos_validos:
            raise HTTPException(
                status_code=400,
                detail=f"Campo inválido para ordenar: '{self.ordenar_por}'. Opciones válidas: {', '.join(campos_validos)}"
            )

        # (Opcional) Validar valores permitidos para status
        estados_validos = {"pendiente", "en_proceso", "completado", "fallido"}
        if self.status and self.status not in estados_validos:
            raise HTTPException(
                status_code=400,
                detail=f"Estado inválido: '{self.status}'. Válidos: {', '.join(estados_validos)}"
            )

        return self
