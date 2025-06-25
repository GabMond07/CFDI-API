from pydantic import BaseModel, Field, model_validator
from typing import Optional, Literal, ClassVar, List

class FiltroConcept(BaseModel):
    description: Optional[str] = None
    fiscal_key: Optional[str] = None
    monto_min: Optional[float] = Field(None, ge=0, description="Monto mínimo no puede ser negativo")
    monto_max: Optional[float] = Field(None, ge=0, description="Monto máximo no puede ser negativo")
    cfdi_id: Optional[int] = None
    unit_value_min: Optional[float] = Field(None, ge=0, description="Valor unitario mínimo")
    unit_value_max: Optional[float] = Field(None, ge=0, description="Valor unitario máximo")
    quantity_min: Optional[float] = Field(None, ge=0, description="Cantidad mínima")
    quantity_max: Optional[float] = Field(None, ge=0, description="Cantidad máxima")
    discount_min: Optional[float] = Field(None, ge=0, description="Descuento mínimo")
    discount_max: Optional[float] = Field(None, ge=0, description="Descuento máximo")

    campos_validos_ordenar: ClassVar[List[str]] = ["id", "unit_value", "amount", "quantity", "discount"]

    ordenar_por: Optional[str] = Field("id")
    ordenar_dir: Optional[Literal["asc", "desc"]] = "asc"
    pagina: int = Field(1, ge=1)
    por_pagina: int = Field(10, ge=1, le=100)
    solo_con_impuestos: Optional[bool] = None

    @model_validator(mode="after")
    def validar_campos(self):
        # Validación de rangos para amount
        if self.monto_min is not None and self.monto_max is not None:
            if self.monto_max < self.monto_min:
                raise ValueError("monto_max no puede ser menor que monto_min")

        # unit_value
        if self.unit_value_min is not None and self.unit_value_max is not None:
            if self.unit_value_max < self.unit_value_min:
                raise ValueError("unit_value_max no puede ser menor que unit_value_min")

        # quantity
        if self.quantity_min is not None and self.quantity_max is not None:
            if self.quantity_max < self.quantity_min:
                raise ValueError("quantity_max no puede ser menor que quantity_min")

        # discount
        if self.discount_min is not None and self.discount_max is not None:
            if self.discount_max < self.discount_min:
                raise ValueError("discount_max no puede ser menor que discount_min")

        # Validación de campo ordenar_por
        if self.ordenar_por and self.ordenar_por not in self.campos_validos_ordenar:
            raise ValueError(f"ordenar_por debe ser uno de {self.campos_validos_ordenar}")

        return self