from pydantic import BaseModel, Field, model_validator
from typing import Optional, Literal, ClassVar, List

class FiltroConcept(BaseModel):
    description: Optional[str] = None
    monto_min: Optional[float] = Field(None, ge=0, description="Monto mínimo no puede ser negativo")
    monto_max: Optional[float] = Field(None, ge=0, description="Monto máximo no puede ser negativo")
    cfdi_id: Optional[int] = None

    campos_validos_ordenar: ClassVar[List[str]] = ["Concept_ID", "Unit_Value", "Amount"]

    ordenar_por: Optional[str] = Field("Concept_ID")
    ordenar_dir: Optional[Literal["asc", "desc"]] = "asc"
    pagina: int = Field(1, ge=1)
    por_pagina: int = Field(10, ge=1, le=100)
    solo_con_impuestos: Optional[bool] = None

    @model_validator(mode="after")
    def validar_montos(self):
        if self.monto_min is not None and self.monto_max is not None:
            if self.monto_max < self.monto_min:
                raise ValueError("monto_max no puede ser menor que monto_min")
        return self

    @model_validator(mode="after")
    def validar_ordenar_por(self):
        if self.ordenar_por and self.ordenar_por not in self.campos_validos_ordenar:
            raise ValueError(f"ordenar_por debe ser uno de {self.campos_validos_ordenar}")
        return self