from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from enum import Enum
from .common import TableType, CFDIFilter

class OperationType(str, Enum):
    """Tipos de operación para combinación de filtros."""
    UNION = "union"
    INTERSECTION = "intersection"

class DataSource(BaseModel):
    table: TableType = Field(..., description="Tabla a consultar")
    filters: Optional[CFDIFilter] = Field(None, description="Filtros a aplicar")
    
    class Config:
        use_enum_values = True

class SetOperationRequest(BaseModel):
    operation: OperationType = Field(..., description="Tipo de operación de conjunto")
    sources: List[DataSource] = Field(..., min_items=1, max_items=10, description="Fuentes de datos")
    
    class Config:
        use_enum_values = True

class SetOperationResponse(BaseModel):
    items: List[Dict]