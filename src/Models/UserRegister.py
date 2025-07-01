from pydantic import BaseModel, Field
from typing import Optional, Literal
from pydantic import FileUrl, EmailStr
from datetime import datetime

class UserRegister(BaseModel):
    rfc: str = Field(
        ...,
        pattern="^[A-Z&Ñ]{3,4}[0-9]{2}(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])[A-Z0-9]{3}$",
        description="RFC del usuario con formato válido (ej. XAXX010101XXX)"
    )
    password: str = Field(..., min_length=8, description="Contraseña mínima de 8 caracteres")
    username: Optional[str] = Field(None, description="Nombre de usuario del contribuyente")
    email: Optional[EmailStr] = Field(None, description="Email del usuario")