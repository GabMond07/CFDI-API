from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime

class CFDIFilter(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[Literal["emitido", "cancelado"]] = None
    type: Optional[Literal["I", "E", "T", "N", "P", "R"]] = None
    serie: Optional[str] = None
    folio: Optional[str] = None
    issuer_id: Optional[str] = None

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
    items: list[CFDIResponse]
    total: int
    page: int
    page_size: int