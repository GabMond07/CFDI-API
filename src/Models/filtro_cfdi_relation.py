import re
from uuid import UUID
from typing import Optional, Literal
from pydantic import BaseModel, Field, model_validator

class FiltroCFDIRelation(BaseModel):
    related_uuid: Optional[str] = None
    relation_type: Optional[str] = None
    ordenar_por: Optional[str] = Field("id")
    ordenar_dir: Optional[Literal["asc", "desc"]] = "asc"
    pagina: int = Field(1, ge=1)
    por_pagina: int = Field(10, ge=1, le=100)

    @model_validator(mode="after")
    def validar_campos(self):
        # Validar UUID
        if self.related_uuid:
            try:
                UUID(self.related_uuid, version=4)
            except ValueError:
                raise ValueError("related_uuid debe ser un UUID v4 válido")

        # Validar ordenar_por
        campos_validos_ordenar = {"id", "cfdi_id", "related_uuid", "relation_type"}
        if self.ordenar_por not in campos_validos_ordenar:
            raise ValueError(f"ordenar_por inválido. Debe ser uno de {campos_validos_ordenar}")

        # ordenar_dir ya es validado por Literal, pero aseguramos formato
        if self.ordenar_dir.lower() not in {"asc", "desc"}:
            raise ValueError("ordenar_dir debe ser 'asc' o 'desc'")
        else:
            self.ordenar_dir = self.ordenar_dir.lower()

        return self
