from pydantic import BaseModel, validator, Field
from typing import Dict, List, Optional
from .common import CFDIFilter, TableType

class JoinRequest(BaseModel):
    left_table: str = Field(..., description="Tabla izquierda para el join")
    right_table: str = Field(..., description="Tabla derecha para el join")
    join_type: str = Field(..., description="Tipo de join: inner, left, right, full")
    on: Dict[str, str] = Field(..., description="Condiciones del join")
    filters: Optional[CFDIFilter] = Field(None, description="Filtros para aplicar al join")
    sources: List[TableType] = Field(..., description="Tablas involucradas en el join")
    format: str = Field("json", description="Formato de salida: json, xml, csv, excel")
    save_report: bool = Field(False, description="Indica si se debe guardar el reporte en la DB")
    name: Optional[str] = Field(None, description="Nombre del reporte")
    description: Optional[str] = Field(None, description="Descripción del reporte")

    @validator('format')
    def validate_format(cls, v):
        if v.lower() not in ["json", "xml", "csv", "excel", "pdf"]:
            raise ValueError("Format must be json, xml, csv, excel, or pdf")
        return v.lower()

class JoinResponse(BaseModel):
    items: List[Dict]