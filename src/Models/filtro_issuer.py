from pydantic import BaseModel, Field, model_validator
from typing import Optional, Literal, ClassVar, List

class FiltroIssuer(BaseModel):
    rfc: Optional[str] = None
    nombre: Optional[str] = None
    regimen: Optional[str] = None
    ordenar_por: Optional[str] = Field("rfc_issuer")
    ordenar_dir: Optional[Literal["asc", "desc"]] = "asc"
    pagina: int = Field(1, ge=1)
    por_pagina: int = Field(10, ge=1, le=100)

    campos_validos_ordenar: ClassVar[List[str]] = ["rfc_issuer", "name_issuer", "tax_regime"]

    @model_validator(mode="after")
    def validar_ordenar_por(self):
        if self.ordenar_por and self.ordenar_por not in self.campos_validos_ordenar:
            raise ValueError(f"'ordenar_por' debe ser uno de: {self.campos_validos_ordenar}")
        return self
