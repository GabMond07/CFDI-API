from pydantic import BaseModel, Field
from typing import Optional, Literal
from pydantic import FileUrl
from datetime import datetime

class UserCredentials(BaseModel):
    rfc: str = Field(..., description="RFC del usuario para autenticación")
    password: str = Field(..., min_length=8, description="Contraseña del usuario")

class UserRegister(BaseModel):
    rfc: str = Field(
        ...,
        pattern="^[A-Z&Ñ]{3,4}[0-9]{2}(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])[A-Z0-9]{3}$",
        description="RFC del usuario con formato válido (ej. XAXX010101XXX)"
    )
    password: str = Field(..., min_length=8, description="Contraseña mínima de 8 caracteres")

class Token(BaseModel):
    access_token: str = Field(..., description="Token JWT para autenticación")
    token_type: str = Field(..., description="Tipo de token, debe ser 'bearer'")

class CFDIFilter(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[Literal["emitido", "cancelado"]] = None
    type: Optional[Literal["I", "E", "T", "N", "P", "R"]] = None

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
    cfdi_use: Optional[str]

class PaginatedCFDIResponse(BaseModel):
    items: list[CFDIResponse]
    total: int
    page: int
    page_size: int