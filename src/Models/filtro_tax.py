from pydantic import BaseModel, Field, model_validator
from typing import Optional, Literal, ClassVar, List

class FiltroTax(BaseModel):
    tax_type: Optional[str] = None
    rate_min: Optional[float] = Field(None, ge=0, description="La tasa mínima no puede ser negativa")
    rate_max: Optional[float] = Field(None, ge=0, description="La tasa máxima no puede ser negativa")
    amount_min: Optional[float] = Field(None, ge=0, description="El monto mínimo no puede ser negativo")
    amount_max: Optional[float] = Field(None, ge=0, description="El monto máximo no puede ser negativo")
    concept_id: Optional[int] = None
    ordenar_por: Optional[str] = Field("id")
    ordenar_dir: Optional[Literal["asc", "desc"]] = "asc"
    pagina: int = Field(1, ge=1)
    por_pagina: int = Field(10, ge=1, le=100)

    campos_validos_ordenar: ClassVar[List[str]] = [
        "id", "tax_type", "rate", "amount", "concept_id"
    ]

    @model_validator(mode="after")
    def validar_rangos(self):
        if self.rate_min is not None and self.rate_max is not None:
            if self.rate_min > self.rate_max:
                raise ValueError("La tasa mínima no puede ser mayor que la tasa máxima")

        if self.amount_min is not None and self.amount_max is not None:
            if self.amount_min > self.amount_max:
                raise ValueError("El monto mínimo no puede ser mayor que el monto máximo")

        if self.ordenar_por and self.ordenar_por not in self.campos_validos_ordenar:
            raise ValueError(f"'ordenar_por' debe ser uno de: {self.campos_validos_ordenar}")

        return self
