from pydantic import BaseModel, validator, Field
from typing import Dict, List, Optional, Literal, Union
from datetime import datetime
from enum import Enum

class OperationType(str, Enum):
    UNION = "union"
    INTERSECTION = "intersection"

class TableType(str, Enum):
    CFDI = "cfdi"
    ISSUER = "issuer"
    RECEIVER = "receiver"
    CONCEPT = "concept"

class CFDIFilter(BaseModel):
    start_date: Optional[datetime] = Field(None, description="Fecha inicial de filtrado")
    end_date: Optional[datetime] = Field(None, description="Fecha final de filtrado")
    type: Optional[str] = Field(None, max_length=20, description="Tipo de CFDI")
    serie: Optional[str] = Field(None, max_length=25, description="Serie del CFDI")
    folio: Optional[str] = Field(None, max_length=25, description="Folio del CFDI")
    issuer_id: Optional[str] = Field(None, max_length=13, description="RFC del emisor")
    receiver_id: Optional[int] = Field(None, description="ID del receptor")
    currency: Optional[str] = Field(None, max_length=10, description="Moneda")
    payment_method: Optional[str] = Field(None, max_length=50, description="Método de pago")
    payment_form: Optional[str] = Field(None, max_length=50, description="Forma de pago")
    cfdi_use: Optional[str] = Field(None, max_length=50, description="Uso del CFDI")
    export_status: Optional[str] = Field(None, max_length=20, description="Estado de exportación")
    min_total: Optional[float] = Field(None, ge=0, description="Monto mínimo")
    max_total: Optional[float] = Field(None, ge=0, description="Monto máximo")
    status: Optional[str] = Field(None, max_length=20, description="Estado del CFDI")

    @validator('end_date')
    def validate_date_range(cls, v, values):
        if v and values.get('start_date') and v < values['start_date']:
            raise ValueError('end_date must be greater than or equal to start_date')
        return v
    
    @validator('max_total')
    def validate_total_range(cls, v, values):
        if v and values.get('min_total') and v < values['min_total']:
            raise ValueError('max_total must be greater than or equal to min_total')
        return v

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
    
    @validator('sources')
    def validate_sources(cls, v):
        if len(v) < 2 and any(source.table == TableType.CFDI for source in v):
            # Para operaciones de conjunto necesitamos al menos 2 fuentes
            pass  # Permitir 1 fuente para casos especiales
        return v
    
class CFDISort(BaseModel):
    field: Literal["issue_date", "total"] = "issue_date"
    direction: Literal["asc", "desc"] = "desc"

class CFDIResponse(BaseModel):
    id: int
    uuid: str
    version: str
    serie: Optional[str]
    folio: Optional[str]
    issue_date: datetime
    seal: Optional[str]
    certificate_number: Optional[str]
    certificate: Optional[str]
    place_of_issue: Optional[str]
    type: str
    total: float
    subtotal: float
    payment_method: Optional[str]
    payment_form: Optional[str]
    currency: Optional[str]
    user_id: str
    issuer_id: str
    issuer_name: Optional[str]
    cfdi_use: Optional[str]

class PaginatedCFDIResponse(BaseModel):
    items: List[CFDIResponse]
    total: int
    page: int
    page_size: int

class AggregationRequest(BaseModel):
    operation: Literal["sum", "count", "avg", "min", "max"]
    field: Literal["total", "subtotal"]
    filters: Optional[CFDIFilter] = None
    include_details: bool = False

class JoinRequest(BaseModel):
    sources: List[Literal["cfdi", "receiver", "issuer"]]
    join_type: Literal["inner", "left"] = "inner"
    on: Dict[str, str]
    filters: Optional[CFDIFilter] = None

class StatsRequest(BaseModel):
    field: Literal["total", "subtotal"]
    filters: Optional[CFDIFilter] = None

class ScriptRequest(BaseModel):
    language: Literal["python", "r", "sql"]
    script: str
    filters: Optional[CFDIFilter] = None

class AggregationResponse(BaseModel):
    result: Dict[str, float | int]
    details: Optional[List[Dict]] = None

class JoinResponse(BaseModel):
    items: List[Dict]

class CentralTendencyResponse(BaseModel):
    average: float
    median: float
    mode: float

class BasicStatsResponse(BaseModel):
    range: float
    variance: float
    standard_deviation: float
    coefficient_of_variation: float

class SetOperationResponse(BaseModel):
    items: List[Dict]

class ScriptResponse(BaseModel):
    message: str