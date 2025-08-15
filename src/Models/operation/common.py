from pydantic import BaseModel, validator, Field
from typing import Optional, Literal
from datetime import datetime
from enum import Enum

class TableType(str, Enum):
    """Tipos de tabla disponibles para consultas."""
    CFDI = "cfdi"
    ISSUER = "issuer"
    RECEIVER = "receiver"
    CONCEPT = "concept"
    TAXES = "taxes"
    REPORT = "report"
    VISUALIZATION = "visualization"
    NOTIFICATION = "notification"
    PAYMENT_COMPLEMENT = "payment_complement"
    CFDI_ATTACHMENT = "cfdi_attachment"
    CFDI_RELATION = "cfdi_relation"
    USER = "user"
    ROLES = "roles"
    TENANT = "tenant"
    BATCH_JOB = "batch_job"

class CFDIType(str, Enum):
    """Tipos de CFDI válidos."""
    INGRESO = "I"
    EGRESO = "E"
    TRASLADO = "T"
    NOMINA = "N"
    PAGO = "P"

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
    format: str = Field("json", description="Formato de salida: json, xml, csv, excel")
    save_report: bool = Field(False, description="Indica si se debe guardar el reporte en la DB")
    name: Optional[str] = Field(None, description="Nombre del reporte")
    description: Optional[str] = Field(None, description="Descripción del reporte")

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

    @validator('format')
    def validate_format(cls, v):
        if v.lower() not in ["json", "xml", "csv", "excel", "pdf"]:
            raise ValueError("Format must be json, xml, csv, excel, or pdf")
        return v.lower()

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