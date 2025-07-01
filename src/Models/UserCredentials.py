from pydantic import BaseModel, Field
from typing import Optional, Literal
from pydantic import FileUrl, EmailStr
from datetime import datetime

class UserCredentials(BaseModel):
    rfc: str = Field(..., description="RFC del usuario para autenticación")
    password: str = Field(..., min_length=8, description="Contraseña del usuario")